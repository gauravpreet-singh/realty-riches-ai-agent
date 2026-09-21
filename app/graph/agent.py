from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    extract_buyer_requirements,
    extract_intent,
    extract_seller_requirements,
    generate_response,
    generate_unknown_response,
    match_properties,
    route_intent,
    upsert_buyer_lead,
    upsert_seller_lead,
    upsert_seller_property_node,
)
from app.graph.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)
    for name, fn in [
        ("extract_intent", extract_intent),
        ("extract_buyer_requirements", extract_buyer_requirements),
        ("upsert_buyer_lead", upsert_buyer_lead),
        ("match_properties", match_properties),
        ("extract_seller_requirements", extract_seller_requirements),
        ("upsert_seller_lead", upsert_seller_lead),
        ("upsert_seller_property", upsert_seller_property_node),
        ("generate_response", generate_response),
        ("generate_unknown_response", generate_unknown_response),
    ]:
        graph.add_node(name, fn)
    graph.add_edge(START, "extract_intent")
    graph.add_conditional_edges(
        "extract_intent",
        route_intent,
        {
            "buyer": "extract_buyer_requirements",
            "seller": "extract_seller_requirements",
            "both": "extract_buyer_requirements",
            "unknown": "generate_unknown_response",
        },
    )
    graph.add_edge("extract_buyer_requirements", "upsert_buyer_lead")
    graph.add_conditional_edges(
        "upsert_buyer_lead",
        lambda s: "both" if s.get("intent") == "both" else "buyer",
        {"buyer": "match_properties", "both": "extract_seller_requirements"},
    )
    graph.add_edge("extract_seller_requirements", "upsert_seller_lead")
    graph.add_edge("upsert_seller_lead", "upsert_seller_property")
    graph.add_conditional_edges(
        "upsert_seller_property",
        lambda s: "both" if s.get("intent") == "both" else "seller",
        {"seller": "generate_response", "both": "match_properties"},
    )
    graph.add_edge("match_properties", "generate_response")
    graph.add_edge("generate_response", END)
    graph.add_edge("generate_unknown_response", END)
    return graph.compile()


agent = build_graph()
