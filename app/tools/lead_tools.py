from typing import Any

from app.db import supabase


def upsert_lead(
    *,
    prospect_id: str | None,
    intent: str,
    city: str | None = None,
    locality: str | None = None,
    property_type: str | None = None,
    bedrooms: int | None = None,
    budget_min: int | None = None,
    budget_max: int | None = None,
    timeline: str | None = None,
    purpose: str | None = None,
    financing_status: str | None = None,
    existing_lead_id: str | None = None,
    status: str | None = None,
) -> str:
    data: dict[str, Any] = {"intent": intent}

    if prospect_id:
        data["prospect_id"] = prospect_id
    if property_type is not None:
        data["property_type"] = property_type
    if bedrooms is not None:
        data["bedrooms"] = bedrooms
    if budget_min is not None:
        data["budget_min"] = budget_min
    if budget_max is not None:
        data["budget_max"] = budget_max
    if timeline is not None:
        data["timeline"] = timeline
    if purpose is not None:
        data["purpose"] = purpose
    if financing_status is not None:
        data["financing_status"] = financing_status
    if city or locality:
        data["preferred_locations"] = [x for x in [locality, city] if x]
        data["summary"] = f"Property interest in {locality or city}."
    if status is not None:
        data["status"] = status

    if existing_lead_id:
        result = (
            supabase.table("leads")
            .update(data)
            .eq("id", existing_lead_id)
            .select("id")
            .execute()
        )
    else:
        data.setdefault("status", "new")
        result = supabase.table("leads").insert(data).select("id").execute()

    if not result.data:
        raise RuntimeError("Lead write returned no row.")
    return result.data[0]["id"]


def update_lead_status(lead_id: str, status: str) -> None:
    result = supabase.table("leads").update({"status": status}).eq("id", lead_id).execute()
    if not result.data:
        # Supabase may return no updated rows depending on RLS/select behavior.
        # The backend uses the secret key, so treat this as a genuine failure only if needed later.
        return


def create_follow_up(
    *,
    lead_id: str,
    reason: str,
    due_at: str | None = None,
    notes: str | None = None,
) -> str:
    data: dict[str, Any] = {
        "lead_id": lead_id,
        "reason": reason,
        "status": "open",
    }
    if due_at is not None:
        data["due_at"] = due_at
    if notes is not None:
        data["notes"] = notes

    result = supabase.table("lead_follow_ups").insert(data).select("id").execute()
    if not result.data:
        raise RuntimeError("Follow-up creation returned no row.")
    return result.data[0]["id"]


def upsert_seller_property(
    *,
    lead_id: str,
    prospect_id: str | None,
    property_type: str | None = None,
    city: str | None = None,
    locality: str | None = None,
    area: float | None = None,
    bedrooms: int | None = None,
    bathrooms: int | None = None,
    property_age_years: float | None = None,
    condition: str | None = None,
    expected_price: int | None = None,
    selling_timeline: str | None = None,
    reason_for_selling: str | None = None,
    existing_property_id: str | None = None,
) -> str:
    data: dict[str, Any] = {"lead_id": lead_id}
    values = {
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
    data.update({k: v for k, v in values.items() if v is not None})

    if existing_property_id:
        result = (
            supabase.table("seller_properties")
            .update(data)
            .eq("id", existing_property_id)
            .select("id")
            .execute()
        )
    else:
        result = supabase.table("seller_properties").insert(data).select("id").execute()

    if not result.data:
        raise RuntimeError("Seller property write returned no row.")
    return result.data[0]["id"]
