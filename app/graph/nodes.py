from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.db import supabase
from app.graph.state import AgentState
from app.matching.property_matcher import PropertyMatcher
from app.tools.lead_tools import (
    create_follow_up,
    update_lead_status,
    upsert_lead,
    upsert_seller_property,
)

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
    return "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}"
        for m in state.get("messages", [])
    )


def _only_present(values: dict) -> dict:
    return {key: value for key, value in values.items() if value is not None}


def extract_intent(state: AgentState) -> dict:
    result = intent_llm.invoke(f"""
Determine the customer's real-estate intent from the entire conversation.

Allowed values:
buy = wants to buy
sell = wants to sell
both = wants to buy and sell
unknown = unclear

Do not infer unsupported intent.

Conversation:
{_conversation_text(state)}
""")
    return {"intent": result.intent}


def route_intent(state: AgentState) -> str:
    return {"buy": "buyer", "sell": "seller", "both": "both"}.get(
        state.get("intent"), "unknown"
    )


def extract_buyer_requirements(state: AgentState) -> dict:
    result = buyer_llm.invoke(f"""
Extract the customer's current BUYING requirements from the entire conversation.

Rules:
- Do not invent values.
- Return null for information that is not known.
- Preserve earlier requirements unless the customer explicitly changes them.
- Understand natural Indian real-estate language such as lakh, crore, BHK, sector and locality.
- If the customer says "actually", "instead", "make that", etc., use the latest requirement.

Conversation:
{_conversation_text(state)}
""")

    extracted = {
        "buyer_city": result.city,
        "buyer_locality": result.locality,
        "buyer_property_type": result.property_type,
        "buyer_bedrooms": result.bedrooms,
        "buyer_budget_min": result.budget_min,
        "buyer_budget_max": result.budget_max,
        "buyer_timeline": result.timeline,
        "buyer_purpose": result.purpose,
        "buyer_financing_status": result.financing_status,
    }

    # Critical multi-turn behavior: never overwrite a known value with None.
    return _only_present(extracted)


def extract_seller_requirements(state: AgentState) -> dict:
    result = seller_llm.invoke(f"""
Extract the customer's current SELLING requirements from the entire conversation.

Rules:
- Do not invent values.
- Return null for information that is not known.
- Preserve earlier requirements unless the customer explicitly changes them.
- expected_price must be numeric INR.
- area should be numeric when explicitly stated.

Conversation:
{_conversation_text(state)}
""")

    extracted = {
        "seller_property_type": result.property_type,
        "seller_city": result.city,
        "seller_locality": result.locality,
        "seller_area": result.area,
        "seller_bedrooms": result.bedrooms,
        "seller_bathrooms": result.bathrooms,
        "seller_property_age_years": result.property_age_years,
        "seller_condition": result.condition,
        "seller_expected_price": result.expected_price,
        "seller_timeline": result.timeline,
        "seller_reason": result.reason,
    }
    return _only_present(extracted)


def match_properties(state: AgentState) -> dict:
    """Match the persisted buyer lead against published inventory.

    Phase 6 matching is deterministic and runs after Phase 5 has extracted
    the requirements and Phase 7 has upserted the lead. The matcher also
    persists qualifying pairs in lead_property_matches.
    """
    lead_id = state.get("lead_id")
    if not lead_id or state.get("intent") not in ("buy", "both"):
        return {"matched_properties": [], "match_found": False}

    matcher = PropertyMatcher(supabase)
    properties = matcher.match_lead_to_properties(lead_id, threshold=70, limit=10)

    return {
        "matched_properties": properties,
        "match_found": bool(properties),
    }


def upsert_buyer_lead(state: AgentState) -> dict:
    return {"lead_id": upsert_lead(
        prospect_id=state.get("prospect_id"),
        intent=state.get("intent", "buy"),
        city=state.get("buyer_city"),
        locality=state.get("buyer_locality"),
        property_type=state.get("buyer_property_type"),
        bedrooms=state.get("buyer_bedrooms"),
        budget_min=state.get("buyer_budget_min"),
        budget_max=state.get("buyer_budget_max"),
        timeline=state.get("buyer_timeline"),
        purpose=state.get("buyer_purpose"),
        financing_status=state.get("buyer_financing_status"),
        existing_lead_id=state.get("lead_id"),
    )}


def upsert_seller_lead(state: AgentState) -> dict:
    return {"lead_id": upsert_lead(
        prospect_id=state.get("prospect_id"),
        intent=state.get("intent", "sell"),
        city=state.get("seller_city"),
        locality=state.get("seller_locality"),
        property_type=state.get("seller_property_type"),
        existing_lead_id=state.get("lead_id"),
    )}


def upsert_seller_property_node(state: AgentState) -> dict:
    if not state.get("lead_id"):
        return {}
    return {"seller_property_id": upsert_seller_property(
        lead_id=state["lead_id"],
        prospect_id=state.get("prospect_id"),
        property_type=state.get("seller_property_type"),
        city=state.get("seller_city"),
        locality=state.get("seller_locality"),
        area=state.get("seller_area"),
        bedrooms=state.get("seller_bedrooms"),
        bathrooms=state.get("seller_bathrooms"),
        property_age_years=state.get("seller_property_age_years"),
        condition=state.get("seller_condition"),
        expected_price=state.get("seller_expected_price"),
        selling_timeline=state.get("seller_timeline"),
        reason_for_selling=state.get("seller_reason"),
        existing_property_id=state.get("seller_property_id"),
    )}


def persist_buyer_search_result(state: AgentState) -> dict:
    lead_id = state.get("lead_id")
    if not lead_id:
        return {}

    if state.get("matched_properties"):
        update_lead_status(lead_id, "qualified")
        return {"lead_status": "qualified"}

    reason = "No current inventory match for the buyer's requirements."
    notes = (
        f"Requirement: {state.get('buyer_property_type') or 'property'}, "
        f"{state.get('buyer_bedrooms') or 'any'} BHK, "
        f"{state.get('buyer_locality') or state.get('buyer_city') or 'preferred area'}, "
        f"budget {state.get('buyer_budget_min')}–{state.get('buyer_budget_max')} INR."
    )

    update_lead_status(lead_id, "follow_up")
    follow_up_id = create_follow_up(
        lead_id=lead_id,
        reason=reason,
        notes=notes,
    )

    return {
        "lead_status": "follow_up",
        "follow_up_id": follow_up_id,
    }


def generate_response(state: AgentState) -> dict:
    property_text = "\n".join(
        f"- {p.get('title')} | {p.get('location')} | {p.get('property_type')} | ₹{p.get('price')}"
        for p in state.get("matched_properties", [])
    )

    result = llm.invoke(f"""
You are a professional real-estate sales consultant having a natural human conversation.

Be warm, concise and conversational. Do not sound like a questionnaire or CRM form.
Ask at most one useful follow-up question at a time.
Never ask for information the customer already provided.
Use previous conversation naturally.
Do not invent property details, availability, prices, amenities, RERA details or commitments.
A property with price 0 means its price is unknown; never quote it as ₹0.

If BUYING and there are matches:
- Mention only the properties listed below.
- Mention one or two relevant options, not the entire inventory.
- Explain briefly why they may fit.

If BUYING and there are NO matches:
- Be honest that there is no suitable current inventory match.
- Reassure the customer that their requirement has been noted/persisted.
- Say that the team can get back to them if a suitable property becomes available.
- Do not promise a specific time or guaranteed property.
- If a small clarification would materially improve the search, ask only one question.

If SELLING:
- Acknowledge what has been collected.
- Ask only for the next useful missing detail.

If BOTH:
- Address both needs naturally without turning the conversation into two separate interviews.

INTENT:
{state.get('intent')}

BUYER REQUIREMENTS:
city={state.get('buyer_city')}
locality={state.get('buyer_locality')}
property_type={state.get('buyer_property_type')}
bedrooms={state.get('buyer_bedrooms')}
budget_min={state.get('buyer_budget_min')}
budget_max={state.get('buyer_budget_max')}
timeline={state.get('buyer_timeline')}

SELLER REQUIREMENTS:
property_type={state.get('seller_property_type')}
city={state.get('seller_city')}
locality={state.get('seller_locality')}
area={state.get('seller_area')}
expected_price={state.get('seller_expected_price')}
timeline={state.get('seller_timeline')}

MATCHED PROPERTIES:
{property_text or 'No confirmed matches.'}

RECENT CONVERSATION:
{_conversation_text(state)}

Generate only the next response to the customer.
""")
    return {"response": result.content}


def generate_unknown_response(state: AgentState) -> dict:
    return {"response": "Are you looking to buy a property, sell a property, or both?"}
