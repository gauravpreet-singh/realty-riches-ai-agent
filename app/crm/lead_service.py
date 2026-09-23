VALID_STATUSES={"new","contacted","qualified","follow_up","visit_scheduled","converted","lost"}

class LeadService:
    def __init__(self, supabase): self.db=supabase

    def get(self, lead_id):
        return self.db.table("leads").select("*").eq("id",lead_id).maybe_single().execute().data

    def update_status(self, lead_id, status):
        if status not in VALID_STATUSES: raise ValueError(status)
        r=self.db.table("leads").update({"status":status}).eq("id",lead_id).execute()
        if not r.data: raise ValueError(f"Lead not updated: {lead_id}")
        return r.data[0]

    def upsert_buyer(self, lead_id=None, prospect_id=None, intent="buy", **req):
        locations=[x for x in (req.get("locality"),req.get("city")) if x]
        payload={"intent":intent,"budget_min":req.get("budget_min"),
                 "budget_max":req.get("budget_max"),
                 "preferred_locations":locations,
                 "property_type":req.get("property_type"),
                 "bedrooms":req.get("bedrooms")}
        if lead_id:
            old=self.get(lead_id) or {}
            for k in ("budget_min","budget_max","preferred_locations","property_type","bedrooms"):
                if payload[k] in (None,[]) and old.get(k) not in (None,[]):
                    payload[k]=old[k]
            r=self.db.table("leads").update(payload).eq("id",lead_id).execute()
            return r.data[0]
        r=self.db.table("leads").insert({**payload,"prospect_id":prospect_id,"status":"new"}).execute()
        return r.data[0]

    def create_follow_up(self, lead_id, reason, due_at=None, notes=None):
        r=self.db.table("lead_follow_ups").insert({
            "lead_id":lead_id,"reason":reason,"status":"open",
            "due_at":due_at,"notes":notes}).execute()
        return r.data[0]
