from datetime import datetime, timezone
from typing import Any

from app.db import supabase
from app.main import run_agent
from app.tools.conversation_tools import create_conversation


class TelephonyService:
    """Maps a Twilio call to a prospect/conversation and runs the core agent."""

    def __init__(self, db=supabase):
        self.db = db

    def resolve_prospect(self, phone: str) -> dict[str, Any]:
        result = (
            self.db.table("prospects")
            .select("*")
            .eq("phone", phone)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

        # Inbound callers can be created as prospects. Outbound eligibility
        # is enforced separately before initiating calls.
        result = (
            self.db.table("prospects")
            .insert({"phone": phone, "source": "twilio"})
            .select("*")
            .execute()
        )
        if not result.data:
            raise RuntimeError("Unable to create prospect for inbound caller")
        return result.data[0]

    def get_or_create_conversation(self, call_sid: str, prospect_id: str, channel="voice") -> str:
        result = (
            self.db.table("call_attempts")
            .select("id, conversation_id")
            .eq("provider_call_id", call_sid)
            .limit(1)
            .execute()
        )
        if result.data and result.data[0].get("conversation_id"):
            return result.data[0]["conversation_id"]

        conversation_id = create_conversation(prospect_id=prospect_id, channel=channel)
        now = datetime.now(timezone.utc).isoformat()
        self.db.table("call_attempts").insert(
            {
                "prospect_id": prospect_id,
                "conversation_id": conversation_id,
                "provider": "twilio",
                "provider_call_id": call_sid,
                "started_at": now,
                "status": "in_progress",
            }
        ).execute()
        return conversation_id

    def process_transcript(self, call_sid: str, phone: str, transcript: str) -> dict[str, Any]:
        prospect = self.resolve_prospect(phone)
        conversation_id = self.get_or_create_conversation(call_sid, prospect["id"])
        result = run_agent(
            transcript,
            prospect_id=prospect["id"],
            conversation_id=conversation_id,
        )
        self.db.table("call_attempts").update(
            {"transcript": transcript, "summary": result.get("response")}
        ).eq("provider_call_id", call_sid).execute()
        return result

    def end_call(self, call_sid: str, status: str = "completed") -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.table("call_attempts").update(
            {"ended_at": now, "status": status}
        ).eq("provider_call_id", call_sid).execute()
