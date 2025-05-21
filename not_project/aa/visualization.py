import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import collections # For defaultdict and deque

from node import Node
from connection import Connection


def get_topological_sort(genome):
    """
    Performs a topological sort to determine node depths.
    Returns a dictionary {node_id: depth}.
    Assumes a directed graph; handles basic feedforward structure.
    Assigns depth 0 to inputs. Depth of other nodes is 1 + max depth of inputs.
    Isolated nodes get a default depth.
    """
    in_degree = {node_id: 0 for node_id in genome.nodes}
    # Map output nodes for each node
    outgoing_connections = collections.defaultdict(list)
    # Map input nodes for each node
    incoming_connections = collections.defaultdict(list)


    for conn in genome.connections.values():
        if conn.enabled:
            in_degree[conn.out_node_id] += 1
            outgoing_connections[conn.in_node_id].append(conn.out_node_id)
            incoming_connections[conn.out_node_id].append(conn.in_node_id)


    # Nodes with in-degree 0 are initial nodes (inputs)
    queue = collections.deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    # Initialize depths. Input nodes have depth 0.
    node_depths = {node_id: 0 for node_id in genome.nodes} # Initialize all to 0
    for node_id in queue: # Ensure initial inputs are 0
        node_depths[node_id] = 0

    # Process nodes layer by layer
    processed_queue = collections.deque(queue)
    visited = set(processed_queue)

    while processed_queue:
        current_node_id = processed_queue.popleft()

        # Calculate depth for outgoing nodes
        current_depth = node_depths[current_node_id]

        for neighbor_id in outgoing_connections[current_node_id]:
             # The depth of a node is the maximum depth of its inputs + 1
             # Need to check if all inputs to neighbor_id have been processed to get correct depth
             all_inputs_processed = all(input_node_id in visited for input_node_id in incoming_connections[neighbor_id])

             if all_inputs_processed:
                 max_input_depth = max(node_depths[input_node_id] for input_node_id in incoming_connections[neighbor_id]) if incoming_connections[neighbor_id] else current_depth # If no incoming, base on current?

                 node_depths[neighbor_id] = max(node_depths.get(neighbor_id, 0), max_input_depth + 1)

                 in_degree[neighbor_id] -= 1
                 if in_degree[neighbor_id] == 0 and neighbor_id not in visited:
                      processed_queue.append(neighbor_id)
                      visited.add(neighbor_id)

    # Handle isolated nodes or nodes in cycles not reached by the feedforward pass
    # Assign them a depth based on their type, possibly after the main layers
    max_calculated_depth = max(node_depths.values()) if node_depths else 0
    for node_id in genome.nodes:
         if node_id not in visited: # If not visited by the main topological sort
              if genome.nodes[node_id].node_type == "input":
                   node_depths[node_id] = 0 # Should have been visited, but safety check
              elif genome.nodes[node_id].node_type == "output":
                   node_depths[node_id] = max_calculated_depth + 2 # Place after main layers
              else: # Hidden or other types not fully processed
                   node_depths[node_id] = max_calculated_depth + 1 # Place after main layers


    # Normalize depths to start from 0 for positioning purposes,
    # and ensure inputs are at 0, outputs are at the highest possible layer
    min_depth = min(node_depths.values()) if node_depths else 0
    node_depths = {node_id: depth - min_depth for node_id, depth in node_depths.items()}

    # Ensure inputs are at depth 0, find max depth for outputs
    input_depths = [node_depths[node_id] for node_id, node in genome.nodes.items() if node.node_type == "input"]
    output_depths = [node_depths[node_id] for node_id, node in genome.nodes.items() if node.node_type == "output"]

    min_input_depth = min(input_depths) if input_depths else 0
    max_output_depth = max(output_depths) if output_depths else (max(node_depths.values()) if node_depths else 0) + 1


    # Adjust depths: inputs to 0, outputs to max_output_layer
    adjusted_depths = {}
    for node_id, depth in node_depths.items():
         if genome.nodes[node_id].node_type == "input":
              adjusted_depths[node_id] = 0
         elif genome.nodes[node_id].node_type == "output":
              adjusted_depths[node_id] = max_output_depth # Place outputs at the last layer
         else: # Hidden nodes
              # Keep their calculated depth, but ensure they are between 0 and max_output_depth
              adjusted_depths[node_id] = max(1, min(max_output_depth - 1, depth)) # Hidden nodes are in layers 1 to max_output_depth - 1 if possible


    return adjusted_depths


def draw_network(genome, canvas, canvas_width, canvas_height):
    """Draws the neural network represented by the genome on a Tkinter canvas with layered hidden nodes based on depth."""
    canvas.delete("all")
    if not genome or not genome.nodes:
        return

    node_radius = 15
    padding = 30

    # Calculate topological depth for each node (adjusted)
    node_depths = get_topological_sort(genome)

    # Group nodes by their adjusted depth
    nodes_by_depth = collections.defaultdict(list)
    for node_id, depth in node_depths.items():
        nodes_by_depth[depth].append(genome.nodes[node_id])

    # Sort nodes within each depth layer by ID for consistent vertical ordering
    for depth in nodes_by_depth:
        nodes_by_depth[depth].sort(key=lambda node: node.node_id)

    # Determine the number of layers (unique depths)
    depth_levels = sorted(nodes_by_depth.keys())
    num_layers = len(depth_levels)

    if num_layers == 0:
        return

    # Calculate horizontal spacing between layers
    layer_spacing = (canvas_width - 2 * padding) / max(1, num_layers - 1)

    # Position nodes based on depth and vertical index within depth layer
    for i, depth in enumerate(depth_levels):
        nodes_in_layer = nodes_by_depth[depth]
        vertical_spacing = (canvas_height - 2 * padding) / max(1, len(nodes_in_layer) - 1)

        for j, node in enumerate(nodes_in_layer):
            # Horizontal position is determined by depth layer
            node.x = padding + i * layer_spacing
            # Vertical position within the layer
            node.y = padding + j * vertical_spacing

    # Draw connections
    for connection in genome.connections.values():
        if connection.enabled:
            try:
                start_node = genome.nodes[connection.in_node_id]
                end_node = genome.nodes[connection.out_node_id]
                # Scale line width by absolute weight
                line_width = max(1, min(4, abs(connection.weight) * 3))
                canvas.create_line(start_node.x, start_node.y, end_node.x, end_node.y,
                                   arrow=tk.LAST, width=line_width,
                                   fill="blue" if connection.weight > 0 else "red")
            except KeyError:
                print(f"Warning: Connection refers to non-existent node(s): {connection}")

    # Draw nodes
    for node in genome.nodes.values():
        color = "lightblue" if node.node_type == "input" else ("yellow" if node.node_type == "hidden" else "lightgreen")
        canvas.create_oval(node.x - node_radius, node.y - node_radius,
                           node.x + node_radius, node.y + node_radius,
                           fill=color, outline="black")
        canvas.create_text(node.x, node.y, text=str(node.node_id), fill="black", font=('Arial', 8))
        # Optional: Display depth below node ID for debugging layout
        # canvas.create_text(node.x, node.y + node_radius + 5, text=f"d:{node_depths.get(node.node_id, '?')}", fill="gray", font=('Arial', 7))