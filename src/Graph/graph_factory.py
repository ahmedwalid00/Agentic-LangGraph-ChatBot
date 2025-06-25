# src/Graph/graph_factory.py

from langgraph.graph import StateGraph, END

# Import only the nodes we are now using
from src.Agents.AgentsController.agents_nodes import (
    supervisor_node,
    # enhancer_node is removed
    researcher_node,
    coder_node,
    validator_node,
)
from src.Schemes.graph_state import BasicChatState

def supervisor_router(state: BasicChatState):
    """
    Router for the supervisor node. This now includes a failsafe
    to handle invalid routing decisions from the LLM.
    """
    decision = state["next"]
    print(f"Supervisor's raw decision: '{decision}'")
    
    # THE FAILSAFE:
    # If the LLM hallucinates a node that doesn't exist (like 'enhancer'),
    # we override its decision and default to the 'researcher'.
    if decision not in ["researcher", "coder", "FINISH"]:
        print(f"WARNING: Invalid route '{decision}' chosen. Overriding to 'researcher'.")
        return "researcher"
    
    # Otherwise, the decision is valid, so we return it.
    return decision

def validator_router(state: BasicChatState):
    """Router for the validator node."""
    if state["next"] == END:
        return END
    return "supervisor"

def get_graph_builder():
    """
    Returns an uncompiled StateGraph builder with the simplified workflow.
    """
    graph_builder = StateGraph(BasicChatState)

    # Add the remaining nodes
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("researcher", researcher_node)
    graph_builder.add_node("coder", coder_node)
    graph_builder.add_node("validator", validator_node)

    # Define the graph structure (edges)
    graph_builder.set_entry_point("supervisor")
    graph_builder.add_edge("researcher", "validator")
    graph_builder.add_edge("coder", "validator")

    # Define conditional routing
    graph_builder.add_conditional_edges(
        "supervisor",
        supervisor_router,
        # The mapping now only contains valid nodes. The router handles errors.
        {"researcher": "researcher", "coder": "coder", "FINISH": END},
    )
    graph_builder.add_conditional_edges(
        "validator",
        validator_router,
        {"supervisor": "supervisor", END: END},
    )
    
    return graph_builder

# Create a single, shared instance of the builder.
graph_builder_instance = get_graph_builder()