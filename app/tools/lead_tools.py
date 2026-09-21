from typing import Any

from app.db import supabase


def upsert_lead(*, prospect_id: str | None, intent: str, city: str | None = None,
                locality: str | None = None, property_type: str | None = None,
                bedrooms: int | None = None, budget_min: int | None = None,
                budget_max: int | None = None, timeline: str | None = None,
                purpose: str | None = None, financing_status: str | None = None,
                existing_lead_id: str | None = None) -> str:
    data: dict[str, Any] = {"intent": intent, "status": "new"}
    if prospect_id: data["prospect_id"] = prospect_id
    if property_type is not None: data["property_type"] = property_type
    if bedrooms is not None: data["bedrooms"] = bedrooms
    if budget_min is not None: data["budget_min"] = budget_min
    if budget_max is not None: data["budget_max"] = budget_max
    if timeline is not None: data["timeline"] = timeline
    if purpose is not None: data["purpose"] = purpose
    if financing_status is not None: data["financing_status"] = financing_status
    if city or locality: data["summary"] = f"Property interest in {locality or city}."
    if existing_lead_id:
        result = supabase.table("leads").update(data).eq("id", existing_lead_id).execute()
    else:
        result = supabase.table("leads").insert(data).execute()
    if not result.data: raise RuntimeError("Lead write returned no row.")
    return result.data[0]["id"]

def upsert_seller_property(*, lead_id: str, prospect_id: str | None,
                           property_type: str | None = None, city: str | None = None,
                           locality: str | None = None, area: float | None = None,
                           bedrooms: int | None = None, bathrooms: int | None = None,
                           property_age_years: float | None = None, condition: str | None = None,
                           expected_price: int | None = None, selling_timeline: str | None = None,
                           reason_for_selling: str | None = None,
                           existing_property_id: str | None = None) -> str:
    data: dict[str, Any] = {"lead_id": lead_id}
    values = {"prospect_id": prospect_id, "property_type": property_type, "city": city,
              "locality": locality, "area": area, "bedrooms": bedrooms, "bathrooms": bathrooms,
              "property_age_years": property_age_years, "condition": condition,
              "expected_price": expected_price, "selling_timeline": selling_timeline,
              "reason_for_selling": reason_for_selling}
    data.update({k: v for k, v in values.items() if v is not None})
    if existing_property_id:
        result = supabase.table("seller_properties").update(data).eq("id", existing_property_id).execute()
    else:
        result = supabase.table("seller_properties").insert(data).execute()
    if not result.data: raise RuntimeError("Seller property write returned no row.")
    return result.data[0]["id"]
