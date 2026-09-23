from app.main import run_agent

messages = [
    "I'm looking to buy a property in Mohali.",
    "I need 3 bedrooms.",
    "My budget is around 50 lakh.",
    "Sector 66B would be ideal.",
]

conversation_id = None
state = None

for message in messages:
    result = run_agent(
        message,
        previous_state=state,
        conversation_id=conversation_id,
    )

    conversation_id = result.get("conversation_id")
    state = result

    print("\n" + "=" * 70)
    print("USER:", message)
    print("CONVERSATION:", conversation_id)
    print("INTENT:", result.get("intent"))
    print("CITY:", result.get("buyer_city"))
    print("LOCALITY:", result.get("buyer_locality"))
    print("BEDROOMS:", result.get("buyer_bedrooms"))
    print("BUDGET:", result.get("buyer_budget_min"), "-", result.get("buyer_budget_max"))
    print("MATCH FOUND:", result.get("match_found"))
    print("LEAD STATUS:", result.get("lead_status"))
    print("FOLLOW UP:", result.get("follow_up_id"))
    print("RESPONSE:", result.get("response"))
