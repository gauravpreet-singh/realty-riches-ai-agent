from .scoring import score_property_for_lead

ACTIVE = ["new","contacted","qualified","follow_up","visit_scheduled"]

class PropertyMatcher:
    def __init__(self, supabase): self.db=supabase

    def _property(self, pid):
        r=self.db.table("properties").select("*").eq("id",pid).single().execute()
        if not r.data: raise ValueError(f"Property not found: {pid}")
        return r.data

    def _leads(self):
        r=(self.db.table("leads").select("*").in_("intent",["buy","both"])
           .in_("status",ACTIVE).execute())
        return r.data or []

    def _properties(self):
        r=self.db.table("properties").select("*").eq("status","published").execute()
        return r.data or []

    def _save(self, lead_id, property_id, score):
        r=(self.db.table("lead_property_matches")
           .upsert({"lead_id":lead_id,"property_id":property_id,
                    "match_score":score,"status":"new"},
                   on_conflict="lead_id,property_id").execute())
        return (r.data or [{}])[0]

    def match_property_to_leads(self, property_id, threshold=70):
        p=self._property(property_id)
        if p.get("status")!="published": return []
        out=[]
        for lead in self._leads():
            s=score_property_for_lead(lead,p)
            if s.score>=threshold:
                self._save(lead["id"],property_id,s.score)
                out.append({"lead_id":lead["id"],"property_id":property_id,
                            "score":s.score,
                            "breakdown":{"location":s.location,"budget":s.budget,
                                         "property_type":s.property_type,
                                         "bedrooms":s.bedrooms}})
        return sorted(out,key=lambda x:x["score"],reverse=True)

    def match_lead_to_properties(self, lead_id, threshold=70):
        r=self.db.table("leads").select("*").eq("id",lead_id).single().execute()
        lead=r.data
        if not lead or lead.get("intent") not in ("buy","both"): return []
        out=[]
        for p in self._properties():
            s=score_property_for_lead(lead,p)
            if s.score>=threshold:
                self._save(lead_id,p["id"],s.score)
                out.append({"property_id":p["id"],"score":s.score})
        return sorted(out,key=lambda x:x["score"],reverse=True)
