import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from ..tools.lead_tools import create_buyer_lead
from ..tools.property_search import search_properties
from .state import AgentState

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)


class PropertyRequirements(BaseModel):
    intent: str = "unknown"
    city: str | None = None
    locality: str | None = None
    property_type: str | None = None
    bedrooms: int | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    timeline: str | None = None
    purpose: str | None = None


structured_llm = llm.with_structured_output(PropertyRequirements)


EXTRACTION_PROMPT = """
You extract structured real-estate requirements from the entire conversation.

The customer may be interested in buying, selling, both, or neither.

Return:

- intent: buy, sell, both, or unknown
- city
- locality
- property_type
- bedrooms
- budget_min
- budget_max
- timeline
- purpose

Rules:

1. Use information provided by the CUSTOMER.
2. Never invent information.
3. If information is unknown, return null.
4. Preserve information from previous customer messages.
5. Indian currency must be represented as integer INR.
6. 1 crore = 10000000.
7. 1 lakh = 100000.
8. "Around 1 crore" means budget_max = 10000000.
"""


def extract_requirements(state: AgentState) -> AgentState:

    history = state.get("messages", [])

    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in history
    )

    result = structured_llm.invoke([
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=conversation),
    ])

    extracted = result.model_dump()

    # Keep previous values when Gemini doesn't return a new value.
    merged = {
        **state,
    }

    for key, value in extracted.items():

        if value is not None:

            # Don't overwrite an existing intent with "unknown".
            if key == "intent" and value == "unknown":
                continue

            merged[key] = value

    return merged


def match_properties(state: AgentState) -> AgentState:

    intent = state.get("intent")

    # Property matching is only relevant to buyers.
    if intent not in ("buy", "both"):
        return {
            **state,
            "matched_properties": [],
        }

    properties = search_properties(
        city=state.get("city"),
        locality=state.get("locality"),
        property_type=state.get("property_type"),
        min_price=state.get("budget_min"),
        max_price=state.get("budget_max"),
        bedrooms=state.get("bedrooms"),
    )

    return {
        **state,
        "matched_properties": properties,
    }


def should_create_lead(state: AgentState) -> bool:

    if state.get("lead_created"):
        return False

    if state.get("intent") not in ("buy", "both"):
        return False

    # We consider a buyer sufficiently qualified
    # when we know at least location OR budget.
    has_location = bool(
        state.get("city") or state.get("locality")
    )

    has_budget = (
        state.get("budget_min") is not None
        or state.get("budget_max") is not None
    )

    return has_location or has_budget


def create_lead(state: AgentState) -> AgentState:

    if not should_create_lead(state):
        return state

    locations = []

    if state.get("city"):
        locations.append(state["city"])

    if state.get("locality"):
        locations.append(state["locality"])

    summary = (
        f"Buyer interested in "
        f"{state.get('property_type') or 'property'}"
    )

    lead = create_buyer_lead(
        prospect_id=state.get("prospect_id"),
        intent=state["intent"],
        budget_min=state.get("budget_min"),
        budget_max=state.get("budget_max"),
        preferred_locations=locations,
        property_type=state.get("property_type"),
        bedrooms=state.get("bedrooms"),
        timeline=state.get("timeline"),
        purpose=state.get("purpose"),
        summary=summary,
    )

    return {
        **state,
        "lead_id": lead["id"],
        "lead_created": True,
    }


RESPONSE_PROMPT = """
You are a helpful real-estate AI sales assistant.

Your job is to qualify the customer and help them find suitable properties.

Rules:

- Be conversational.
- Keep responses relatively short.
- Ask only the next useful question.
- Never invent property details.
- Never invent prices.
- A property with price 0 has an unknown price.
- Only recommend properties supplied by the property-search tool.
- If properties match, mention the most relevant ones.
- If important information is missing, ask for it.
- Do not say a lead was created unless lead_created is true.
"""


def generate_response(state: AgentState) -> AgentState:

    context = {
        "requirements": {
            "intent": state.get("intent"),
            "city": state.get("city"),
            "locality": state.get("locality"),
            "property_type": state.get("property_type"),
            "bedrooms": state.get("bedrooms"),
            "budget_min": state.get("budget_min"),
            "budget_max": state.get("budget_max"),
            "timeline": state.get("timeline"),
            "purpose": state.get("purpose"),
        },

        "matched_properties": state.get(
            "matched_properties",
            []
        ),

        "lead_created": state.get(
            "lead_created",
            False
        ),
    }

    result = llm.invoke([
        SystemMessage(content=RESPONSE_PROMPT),
        HumanMessage(
            content=json.dumps(
                context,
                default=str
            )
        ),
    ])

    messages = list(
        state.get("messages", [])
    )

    messages.append({
        "role": "assistant",
        "content": result.content,
    })

    return {
        **state,
        "messages": messages,
        "next_action": "continue",
    }