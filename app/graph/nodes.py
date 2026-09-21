from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.graph.state import AgentState
from app.tools.lead_tools import upsert_lead, upsert_seller_property
from app.tools.property_search import search_properties

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

class IntentResult(BaseModel):
    intent: Literal["buy", "sell", "both", "unknown"] = "unknown"

class BuyerRequirements(BaseModel):
    city: str | None = None
    locality: str | None = None
    property_type: str | None = None
    bedrooms: int | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    timeline: str | None = None
    purpose: str | None = None
    financing_status: str | None = None

class SellerRequirements(BaseModel):
    property_type: str | None = None
    city: str | None = None
    locality: str | None = None
    area: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    property_age_years: float | None = None
    condition: str | None = None
    expected_price: int | None = None
    timeline: str | None = None
    reason: str | None = None

intent_llm = llm.with_structured_output(IntentResult)
buyer_llm = llm.with_structured_output(BuyerRequirements)
seller_llm = llm.with_structured_output(SellerRequirements)

def _conversation_text(state: AgentState) -> str:
    return "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in state.get("messages", []))

def extract_intent(state: AgentState) -> dict:
    result = intent_llm.invoke(f"""
Determine the customer's real-estate intent.
Allowed values: buy, sell, both, unknown.
Do not infer unsupported intent.
Conversation:
{_conversation_text(state)}
""")
    return {"intent": result.intent}

def route_intent(state: AgentState) -> str:
    return {"buy": "buyer", "sell": "seller", "both": "both"}.get(state.get("intent"), "unknown")

def extract_buyer_requirements(state: AgentState) -> dict:
    result = buyer_llm.invoke(f"""
Extract only BUYING requirements. Do not invent values. Use null when missing.
Budget values must be numeric INR amounts.
Conversation:
{_conversation_text(state)}
""")
    return {"buyer_city": result.city, "buyer_locality": result.locality,
            "buyer_property_type": result.property_type, "buyer_bedrooms": result.bedrooms,
            "buyer_budget_min": result.budget_min, "buyer_budget_max": result.budget_max,
            "buyer_timeline": result.timeline, "buyer_purpose": result.purpose,
            "buyer_financing_status": result.financing_status}

def extract_seller_requirements(state: AgentState) -> dict:
    result = seller_llm.invoke(f"""
Extract only SELLING requirements. Do not invent values. Use null when missing.
expected_price must be numeric INR. area should be numeric when stated.
Conversation:
{_conversation_text(state)}
""")
    return {"seller_property_type": result.property_type, "seller_city": result.city,
            "seller_locality": result.locality, "seller_area": result.area,
            "seller_bedrooms": result.bedrooms, "seller_bathrooms": result.bathrooms,
            "seller_property_age_years": result.property_age_years, "seller_condition": result.condition,
            "seller_expected_price": result.expected_price, "seller_timeline": result.timeline,
            "seller_reason": result.reason}

def match_properties(state: AgentState) -> dict:
    return {"matched_properties": search_properties(
        city=state.get("buyer_city"), locality=state.get("buyer_locality"),
        property_type=state.get("buyer_property_type"), bedrooms=state.get("buyer_bedrooms"),
        budget_min=state.get("buyer_budget_min"), budget_max=state.get("buyer_budget_max"))}

def upsert_buyer_lead(state: AgentState) -> dict:
    return {"lead_id": upsert_lead(
        prospect_id=state.get("prospect_id"), intent=state.get("intent", "buy"),
        city=state.get("buyer_city"), locality=state.get("buyer_locality"),
        property_type=state.get("buyer_property_type"), bedrooms=state.get("buyer_bedrooms"),
        budget_min=state.get("buyer_budget_min"), budget_max=state.get("buyer_budget_max"),
        timeline=state.get("buyer_timeline"), purpose=state.get("buyer_purpose"),
        financing_status=state.get("buyer_financing_status"), existing_lead_id=state.get("lead_id"))}

def upsert_seller_lead(state: AgentState) -> dict:
    return {"lead_id": upsert_lead(
        prospect_id=state.get("prospect_id"), intent=state.get("intent", "sell"),
        city=state.get("seller_city"), locality=state.get("seller_locality"),
        property_type=state.get("seller_property_type"), existing_lead_id=state.get("lead_id"))}

def upsert_seller_property_node(state: AgentState) -> dict:
    if not state.get("lead_id"): return {}
    return {"seller_property_id": upsert_seller_property(
        lead_id=state["lead_id"], prospect_id=state.get("prospect_id"),
        property_type=state.get("seller_property_type"), city=state.get("seller_city"),
        locality=state.get("seller_locality"), area=state.get("seller_area"),
        bedrooms=state.get("seller_bedrooms"), bathrooms=state.get("seller_bathrooms"),
        property_age_years=state.get("seller_property_age_years"), condition=state.get("seller_condition"),
        expected_price=state.get("seller_expected_price"), selling_timeline=state.get("seller_timeline"),
        reason_for_selling=state.get("seller_reason"), existing_property_id=state.get("seller_property_id"))}

def generate_response(state: AgentState) -> dict:
    property_text = "\n".join(f"- {p.get('title')} | {p.get('location')} | {p.get('property_type')} | ₹{p.get('price')}" for p in state.get("matched_properties", []))
    result = llm.invoke(f"""
You are a professional real-estate sales assistant.
Intent: {state.get('intent')}
BUYER: city={state.get('buyer_city')}, locality={state.get('buyer_locality')}, type={state.get('buyer_property_type')}, bedrooms={state.get('buyer_bedrooms')}, budget={state.get('buyer_budget_min')} to {state.get('buyer_budget_max')}
SELLER: type={state.get('seller_property_type')}, city={state.get('seller_city')}, locality={state.get('seller_locality')}, area={state.get('seller_area')}, bedrooms={state.get('seller_bedrooms')}, expected_price={state.get('seller_expected_price')}, timeline={state.get('seller_timeline')}
MATCHED PROPERTIES:
{property_text or 'No confirmed matches.'}
Be concise and conversational. Mention only properties present above. Do not invent prices, availability, amenities, RERA details, or commitments. If buying with no matches, ask one useful qualification question. If selling, acknowledge known details and ask for the most useful missing detail. If both, address both needs briefly.
""")
    return {"response": result.content}

def generate_unknown_response(state: AgentState) -> dict:
    return {"response": "Are you looking to buy a property, sell a property, or both?"}
