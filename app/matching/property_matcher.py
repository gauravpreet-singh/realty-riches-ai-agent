from typing import Any

from .scoring import score_property_for_lead

ACTIVE = ["new", "contacted", "qualified", "follow_up", "visit_scheduled"]


class PropertyMatcher:
    """Deterministic inventory <-> buyer matching service."""

    def __init__(self, supabase):
        self.db = supabase

    def _property(self, property_id: str) -> dict[str, Any]:
        result = (
            self.db.table("properties")
            .select("*")
            .eq("id", property_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise ValueError(f"Property not found: {property_id}")
        return result.data[0]

    def _lead(self, lead_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("leads")
            .select("*")
            .eq("id", lead_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def _leads(self) -> list[dict[str, Any]]:
        result = (
            self.db.table("leads")
            .select("*")
            .in_("intent", ["buy", "both"])
            .in_("status", ACTIVE)
            .execute()
        )
        return result.data or []

    def _properties(self) -> list[dict[str, Any]]:
        result = (
            self.db.table("properties")
            .select("*")
            .eq("status", "published")
            .execute()
        )
        return result.data or []

    def _save(self, lead_id: str, property_id: str, score: int) -> None:
        self.db.table("lead_property_matches").upsert(
            {
                "lead_id": lead_id,
                "property_id": property_id,
                "match_score": score,
                "status": "new",
            },
            on_conflict="lead_id,property_id",
        ).execute()

    def match_property_to_leads(
        self, property_id: str, threshold: int = 70
    ) -> list[dict[str, Any]]:
        prop = self._property(property_id)
        if prop.get("status") != "published":
            return []

        matches: list[dict[str, Any]] = []
        for lead in self._leads():
            result = score_property_for_lead(lead, prop)
            if result.score >= threshold:
                self._save(lead["id"], property_id, result.score)
                matches.append(
                    {
                        "lead_id": lead["id"],
                        "property_id": property_id,
                        "score": result.score,
                        "breakdown": {
                            "location": result.location,
                            "budget": result.budget,
                            "property_type": result.property_type,
                            "bedrooms": result.bedrooms,
                        },
                    }
                )

        return sorted(matches, key=lambda item: item["score"], reverse=True)

    def match_lead_to_properties(
        self, lead_id: str, threshold: int = 70, limit: int = 10
    ) -> list[dict[str, Any]]:
        lead = self._lead(lead_id)
        if not lead or lead.get("intent") not in ("buy", "both"):
            return []

        matches: list[dict[str, Any]] = []
        for prop in self._properties():
            result = score_property_for_lead(lead, prop)
            if result.score >= threshold:
                self._save(lead_id, prop["id"], result.score)
                matches.append(
                    {
                        **prop,
                        "match_score": result.score,
                        "match_breakdown": {
                            "location": result.location,
                            "budget": result.budget,
                            "property_type": result.property_type,
                            "bedrooms": result.bedrooms,
                        },
                    }
                )

        return sorted(matches, key=lambda item: item["match_score"], reverse=True)[:limit]
