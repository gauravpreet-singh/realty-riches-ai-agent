from langgraph.graph import END, START, StateGraph

from .nodes import (
    create_lead,
    extract_requirements,
    generate_response,
    match_properties,
)
from .state import AgentState


def build_agent():

    graph = StateGraph(AgentState)

    graph.add_node(
        "extract_requirements",
        extract_requirements
    )

    graph.add_node(
        "match_properties",
        match_properties
    )

    graph.add_node(
        "create_lead",
        create_lead
    )

    graph.add_node(
        "generate_response",
        generate_response
    )

    graph.add_edge(
        START,
        "extract_requirements"
    )

    graph.add_edge(
        "extract_requirements",
        "match_properties"
    )

    graph.add_edge(
        "match_properties",
        "create_lead"
    )

    graph.add_edge(
        "create_lead",
        "generate_response"
    )

    graph.add_edge(
        "generate_response",
        END
    )

    return graph.compile()