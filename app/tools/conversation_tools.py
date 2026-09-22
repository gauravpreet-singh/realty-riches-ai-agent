from datetime import datetime, timezone
from typing import Any

from app.db import supabase


def create_conversation(prospect_id: str | None = None, channel: str = "text") -> str:
    data: dict[str, Any] = {"channel": channel}
    if prospect_id:
        data["prospect_id"] = prospect_id

    result = (
        supabase.table("conversations")
        .insert(data)
        .select("id")
        .execute()
    )

    if not result.data:
        raise RuntimeError("Conversation creation returned no row.")

    return result.data[0]["id"]


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def load_messages(conversation_id: str) -> list[dict[str, str]]:
    result = (
        supabase.table("conversation_messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    result = (
        supabase.table("conversation_messages")
        .insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        })
        .select("id")
        .execute()
    )

    if not result.data:
        raise RuntimeError("Conversation message insert returned no row.")

    return result.data[0]["id"]


def update_conversation(
    conversation_id: str,
    *,
    lead_id: str | None = None,
    summary: str | None = None,
    outcome: str | None = None,
    ended: bool = False,
) -> None:
    data: dict[str, Any] = {}

    if lead_id is not None:
        data["lead_id"] = lead_id
    if summary is not None:
        data["summary"] = summary
    if outcome is not None:
        data["outcome"] = outcome
    if ended:
        data["ended_at"] = datetime.now(timezone.utc).isoformat()

    if data:
        supabase.table("conversations").update(data).eq("id", conversation_id).execute()
