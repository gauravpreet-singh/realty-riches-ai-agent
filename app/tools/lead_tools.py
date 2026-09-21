from typing import Any

from ..db import supabase


def create_buyer_lead(
    *,
    prospect_id: str | None,
    intent: str,
    budget_min: int | None,
    budget_max: int | None,
    preferred_locations: list[str],
    property_type: str | None,
    bedrooms: int | None,
    timeline: str | None,
    purpose: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:

    payload = {
        "prospect_id": prospect_id,
        "intent": intent,
        "status": "new",
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferred_locations": preferred_locations,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "timeline": timeline,
        "purpose": purpose,
        "summary": summary,
    }

    response = (
        supabase
        .table("leads")
        .insert(payload)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Failed to create buyer lead")

    return response.data[0]