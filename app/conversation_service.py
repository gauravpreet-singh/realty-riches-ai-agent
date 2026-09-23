class ConversationService:
    def __init__(self, supabase, agent_runner):
        self.db=supabase; self.agent_runner=agent_runner

    def process_message(self, conversation_id, prospect_id, message, channel):
        if conversation_id:
            c=self.db.table("conversations").select("*").eq("id",conversation_id).single().execute().data
        else:
            c=self.db.table("conversations").insert({
                "prospect_id":prospect_id,"channel":channel}).execute().data[0]
        history=(self.db.table("conversation_messages").select("role,content")
                 .eq("conversation_id",c["id"]).order("created_at").execute().data or [])
        history.append({"role":"user","content":message})
        state=self.agent_runner({"prospect_id":prospect_id,
                                 "conversation_id":c["id"],"messages":history})
        response=state.get("response")
        if not response:
            a=[m for m in state.get("messages",[]) if m.get("role")=="assistant"]
            response=a[-1]["content"] if a else ""
        self.db.table("conversation_messages").insert({
            "conversation_id":c["id"],"role":"user","content":message}).execute()
        if response:
            self.db.table("conversation_messages").insert({
                "conversation_id":c["id"],"role":"assistant","content":response}).execute()
        return {"conversation_id":c["id"],"response":response,"state":state}
