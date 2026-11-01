# LangGraph StateGraph Overview

LangGraph is a framework for building stateful, multi-step applications using graphs. A graph consists of nodes, edges, and a shared state schema.

## StateGraph

Create a graph with `StateGraph(State)`, where State is commonly a TypedDict. Nodes are Python functions that receive the current state and return a dictionary containing state updates. State keys can be added or updated as the graph executes.

## Nodes and edges

Add nodes with `add_node(name, function)`. Set the starting node with `set_entry_point(name)`. Add a normal edge with `add_edge(source, destination)`. The `END` marker represents completion.

## Conditional edges

Use `add_conditional_edges(source, routing_function, path_map)` to choose the next node based on the current state. The routing function returns a key that maps to a destination. This supports retries, branching, and approval workflows.

## Compile and invoke

Call `compile()` to create an executable graph. Use `invoke(initial_state)` to run it synchronously. The returned value contains the final state after graph execution.

## Retry design

A workflow can store a retry counter in its state. After a validation or grading node, a conditional edge can route back to an earlier node while the counter is below a configured limit. Once the limit is reached, route to a fallback node or end the graph to prevent infinite loops.
