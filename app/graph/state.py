from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    prospect_id: str | None
    conversation_id: str | None
    messages: list[dict[str, str]]
    intent: str

    buyer_city: str | None
    buyer_locality: str | None
    buyer_property_type: str | None
    buyer_bedrooms: int | None
    buyer_budget_min: int | None
    buyer_budget_max: int | None
    buyer_timeline: str | None
    buyer_purpose: str | None
    buyer_financing_status: str | None

    seller_property_type: str | None
    seller_city: str | None
    seller_locality: str | None
    seller_area: float | None
    seller_bedrooms: int | None
    seller_bathrooms: int | None
    seller_property_age_years: float | None
    seller_condition: str | None
    seller_expected_price: int | None
    seller_timeline: str | None
    seller_reason: str | None

    matched_properties: list[dict[str, Any]]
    lead_id: str | None
    seller_property_id: str | None
    response: str
