from typing import Any

from ..db import supabase


def create_seller_property(
    *,
    lead_id: str | None,
    prospect_id: str | None,
    property_type: str | None,
    city: str | None,
    locality: str | None,
    area: float | None,
    bedrooms: int | None,
    bathrooms: int | None,
    property_age_years: float | None,
    condition: str | None,
    expected_price: int | None,
    selling_timeline: str | None,
    reason_for_selling: str | None,
) -> dict[str, Any]:

    payload = {
        "lead_id": lead_id,
        "prospect_id": prospect_id,
        "property_type": property_type,
        "city": city,
        "locality": locality,
        "area": area,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "property_age_years": property_age_years,
        "condition": condition,
        "expected_price": expected_price,
        "selling_timeline": selling_timeline,
        "reason_for_selling": reason_for_selling,
    }

    response = (
        supabase
        .table("seller_properties")
        .insert(payload)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Failed to create seller property"
        )

    return response.data[0]