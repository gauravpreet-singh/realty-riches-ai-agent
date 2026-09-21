from typing import Any

from ..db import supabase


def search_properties(
    *,
    city: str | None = None,
    locality: str | None = None,
    property_type: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    bedrooms: int | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Search published properties using deterministic structured filters.

    Important: price=0 is treated as unknown, so it is never considered
    budget-compatible when a price ceiling is supplied.
    """
    query = (
        supabase.table("properties")
        .select(
            "id,title,property_type,location,location_slug,city,price,"
            "area,bedrooms,bathrooms,description,possession,status"
        )
        .eq("status", "published")
    )

    if city:
        query = query.ilike("city", f"%{city}%")

    if locality:
        query = query.ilike("location", f"%{locality}%")

    if property_type:
        query = query.ilike("property_type", property_type)

    if bedrooms is not None:
        query = query.eq("bedrooms", bedrooms)

    # Apply a lower bound only to known prices.
    if min_price is not None:
        query = query.gte("price", min_price)

    # Exclude unknown prices when the caller supplied a budget ceiling.
    if max_price is not None:
        query = query.gt("price", 0).lte("price", max_price)

    response = query.limit(limit).execute()
    return response.data or []
