from typing import Any

from app.db import supabase


def search_properties(
    city: str | None = None,
    locality: str | None = None,
    property_type: str | None = None,
    bedrooms: int | None = None,
    budget_min: int | None = None,
    budget_max: int | None = None,
) -> list[dict[str, Any]]:
    query = supabase.table("properties").select("*").eq("status", "published")

    if city:
        query = query.ilike("city", f"%{city}%")
    if property_type:
        query = query.ilike("property_type", f"%{property_type}%")
    if bedrooms is not None:
        query = query.eq("bedrooms", bedrooms)

    # price=0 means unknown in the current inventory.
    if budget_min is not None:
        query = query.gt("price", 0).gte("price", budget_min)
    if budget_max is not None:
        query = query.gt("price", 0).lte("price", budget_max)

    # Locality/sector is not consistently stored in the current `location`
    # column. Retrieve candidates using structured filters, then search the
    # textual property fields for the locality/sector.
    properties = query.limit(100).execute().data or []

    if locality:
        needle = locality.lower().strip()

        def matches(property_row: dict[str, Any]) -> bool:
            text = " ".join(
                str(property_row.get(field) or "")
                for field in ("title", "location", "location_slug", "description")
            ).lower()
            return needle in text

        properties = [p for p in properties if matches(p)]

    return properties[:10]
