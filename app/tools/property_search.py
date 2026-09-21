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

    query = (
        supabase
        .table("properties")
        .select("*")
        .eq("status", "published")
    )

    # City
    if city:
        query = query.ilike("city", f"%{city}%")

    # Property type
    if property_type:
        query = query.ilike("property_type", f"%{property_type}%")

    # Bedrooms
    if bedrooms is not None:
        query = query.eq("bedrooms", bedrooms)

    # Budget
    # price=0 means unknown, so exclude it when budget is specified.
    if budget_min is not None:
        query = query.gt("price", 0).gte("price", budget_min)

    if budget_max is not None:
        query = query.gt("price", 0).lte("price", budget_max)

    # Fetch city/type/budget/bedroom candidates first.
    response = query.limit(100).execute()

    properties = response.data or []

    # Locality is handled after retrieval because the current schema
    # does not consistently store sector/locality in the `location` column.
    if locality:
        locality_normalized = locality.lower().strip()

        def locality_matches(property: dict[str, Any]) -> bool:
            searchable_text = " ".join(
                str(property.get(field) or "")
                for field in [
                    "title",
                    "location",
                    "location_slug",
                    "description",
                ]
            ).lower()

            return locality_normalized in searchable_text

        properties = [
            property
            for property in properties
            if locality_matches(property)
        ]

    return properties[:10]