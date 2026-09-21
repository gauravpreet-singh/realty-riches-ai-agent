from app.graph.agent import agent


def run_agent(message: str, *, prospect_id: str | None = None,
              conversation_id: str | None = None, previous_state: dict | None = None):
    state = dict(previous_state or {})
    state["prospect_id"] = prospect_id or state.get("prospect_id")
    state["conversation_id"] = conversation_id or state.get("conversation_id")
    messages = list(state.get("messages", []))
    messages.append({"role": "user", "content": message})
    state["messages"] = messages
    result = agent.invoke(state)
    result["messages"] = list(result.get("messages", [])) + [{"role": "assistant", "content": result["response"]}]
    return result

if __name__ == "__main__":
    result = run_agent("I want to sell my house in Sector 66B Mohali.")
    print("Intent:", result.get("intent"))
    print("Response:", result.get("response"))
    print("Lead ID:", result.get("lead_id"))
    print("Matches:", len(result.get("matched_properties", [])))
