from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    prospect_id: str | None
    conversation_id: str | None

    # Conversation
    messages: list[dict[str, str]]

    # Buyer/seller intent
    intent: str

    # Buyer requirements
    city: str | None
    locality: str | None
    property_type: str | None
    bedrooms: int | None
    budget_min: int | None
    budget_max: int | None
    timeline: str | None
    purpose: str | None

    # Search results
    matched_properties: list[dict[str, Any]]

    # Lead
    lead_id: str | None
    lead_created: bool

    # Agent control
    next_action: str
    summary: str