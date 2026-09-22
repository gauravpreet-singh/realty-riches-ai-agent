from app.graph.agent import agent
from app.tools.conversation_tools import (
    create_conversation,
    get_conversation,
    load_messages,
    save_message,
    update_conversation,
)


def run_agent(
    message: str,
    *,
    prospect_id: str | None = None,
    conversation_id: str | None = None,
    previous_state: dict | None = None,
):
    """Run one turn using Supabase-backed conversation memory.

    `previous_state` is still accepted for local experiments, but the durable
    source of conversation history is now conversation_messages in Supabase.
    """
    if conversation_id:
        conversation = get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
    else:
        conversation_id = create_conversation(
            prospect_id=prospect_id,
            channel="web",
        )
        conversation = get_conversation(conversation_id) or {}

    stored_messages = load_messages(conversation_id)

    # Start with durable conversation history. Previous state is only a
    # compatibility fallback for local tests and non-message state.
    state = dict(previous_state or {})
    state["prospect_id"] = (
        prospect_id
        or conversation.get("prospect_id")
        or state.get("prospect_id")
    )
    state["conversation_id"] = conversation_id
    state["lead_id"] = conversation.get("lead_id") or state.get("lead_id")
    state["messages"] = stored_messages + [
        {"role": "user", "content": message}
    ]

    result = agent.invoke(state)
    response = result["response"]

    # Persist exactly the new turn. Existing history was loaded above.
    save_message(conversation_id, "user", message)
    save_message(conversation_id, "assistant", response)

    lead_id = result.get("lead_id")
    update_conversation(
        conversation_id,
        lead_id=lead_id,
        summary=_build_summary(result),
        outcome=_build_outcome(result),
    )

    result["conversation_id"] = conversation_id
    result["messages"] = state["messages"] + [
        {"role": "assistant", "content": response}
    ]

    return result


def _build_summary(state: dict) -> str:
    intent = state.get("intent", "unknown")

    if intent == "buy":
        return (
            f"Buyer: {state.get('buyer_property_type') or 'property'} in "
            f"{state.get('buyer_locality') or state.get('buyer_city') or 'unspecified location'}; "
            f"budget {state.get('buyer_budget_min') or ''}-{state.get('buyer_budget_max') or ''}."
        )

    if intent == "sell":
        return (
            f"Seller: {state.get('seller_property_type') or 'property'} in "
            f"{state.get('seller_locality') or state.get('seller_city') or 'unspecified location'}; "
            f"expected price {state.get('seller_expected_price') or 'unknown'}."
        )

    if intent == "both":
        return "Customer is both buying and selling property."

    return "Customer intent has not yet been established."


def _build_outcome(state: dict) -> str:
    if state.get("intent") == "unknown":
        return "qualification_pending"
    if state.get("matched_properties"):
        return "property_matches_found"
    if state.get("intent") in {"sell", "both"}:
        return "seller_qualification"
    return "qualification_pending"


if __name__ == "__main__":
    result = run_agent(
        "I am looking to buy a 3 BHK in Mohali around 90 lakh."
    )

    print("Conversation ID:", result.get("conversation_id"))
    print("Intent:", result.get("intent"))
    print("Response:", result.get("response"))
    print("Lead ID:", result.get("lead_id"))
    print("Matches:", len(result.get("matched_properties", [])))
