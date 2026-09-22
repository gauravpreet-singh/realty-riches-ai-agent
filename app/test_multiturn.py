from app.main import run_agent

state = None

requests = [
    "I'm looking to buy a property in Mohali.",
    "I need 3 bedrooms.",
    "My budget is around 90 lakh.",
    "Sector 125 or somewhere nearby would be fine.",
    "I can move in around a year.",
]

for message in requests:
    result = run_agent(
        message,
        previous_state=state,
    )

    print("\n" + "=" * 60)
    print("USER:", message)
    print("INTENT:", result.get("intent"))
    print("RESPONSE:", result.get("response"))
    print("CITY:", result.get("buyer_city"))
    print("LOCALITY:", result.get("buyer_locality"))
    print("BEDROOMS:", result.get("buyer_bedrooms"))
    print(
        "BUDGET:",
        result.get("buyer_budget_min"),
        "-",
        result.get("buyer_budget_max"),
    )
    print("MATCHES:", len(result.get("matched_properties", [])))

    state = result