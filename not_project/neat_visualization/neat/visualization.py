# neat/visualization.py
import tkinter as tk

def calculate_layout(genome):
    """Calculate the layout of the genome for visualization.
    
    Args:
        genome: Genome to visualize
        
    Returns:
        Layout information including node positions
    """
    # Group nodes by type
    input_nodes = []
    hidden_nodes = []
    output_nodes = []
    
    for node in genome.nodes.values():
        if node.node_type == 0:  # INPUT
            input_nodes.append(node)
        elif node.node_type == 1:  # HIDDEN
            hidden_nodes.append(node)
        else:  # OUTPUT
            output_nodes.append(node)
    
    # Sort nodes by ID for consistent layout
    input_nodes.sort(key=lambda n: n.node_id)
    hidden_nodes.sort(key=lambda n: n.node_id)
    output_nodes.sort(key=lambda n: n.node_id)
    
    # Set positions
    all_nodes = {}
    
    # Position input nodes in a row at the left
    for i, node in enumerate(input_nodes):
        node.x = 50  # Fixed x coordinate for input layer
        node.y = 50 + i * 40  # Spread vertically
        all_nodes[node.node_id] = (node.x, node.y)
    
    # Position output nodes in a row at the right
    for i, node in enumerate(output_nodes):
        node.x = 350  # Fixed x coordinate for output layer
        node.y = 50 + i * 40  # Spread vertically
        all_nodes[node.node_id] = (node.x, node.y)
    
    # Position hidden nodes in the middle
    for i, node in enumerate(hidden_nodes):
        node.x = 200  # Fixed x coordinate for hidden layer
        node.y = 50 + i * 40  # Spread vertically
        all_nodes[node.node_id] = (node.x, node.y)
    
    return {
        'nodes': all_nodes,
        'input_nodes': input_nodes,
        'hidden_nodes': hidden_nodes,
        'output_nodes': output_nodes
    }

def draw_genome(canvas, genome, width=400, height=300):
    """Draw the genome on the given canvas.
    
    Args:
        canvas: Tkinter canvas to draw on
        genome: Genome to visualize
        width: Width of the canvas
        height: Height of the canvas
    """
    # Clear canvas
    canvas.delete("all")
    
    # Calculate layout
    layout = calculate_layout(genome)
    
    # Draw connections first (so they're behind nodes)
    for conn in genome.connections.values():
        if conn.in_node in layout['nodes'] and conn.out_node in layout['nodes']:
            x1, y1 = layout['nodes'][conn.in_node]
            x2, y2 = layout['nodes'][conn.out_node]
            
            # Color based on weight (red for negative, green for positive)
            color = "red" if conn.weight < 0 else "green"
            
            # Line width based on weight magnitude
            width = abs(conn.weight) * 1.5
            
            # Dashed line if disabled
            dash = (5, 5) if not conn.enabled else None
            
            canvas.create_line(x1, y1, x2, y2, fill=color, width=width, dash=dash, tags="connection")
            
            # Draw small label for weight
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            canvas.create_text(mid_x, mid_y, text=f"{conn.weight:.1f}", fill="white", font=("Arial", 8), tags="weight")
    
    # Draw nodes
    for node_type, nodes in [
        ("input", layout['input_nodes']), 
        ("hidden", layout['hidden_nodes']), 
        ("output", layout['output_nodes'])
    ]:
        for node in nodes:
            x, y = node.x, node.y
            
            # Different colors for different node types
            if node.node_type == 0:  # INPUT
                color = "blue"
            elif node.node_type == 1:  # HIDDEN
                color = "purple"
            else:  # OUTPUT
                color = "orange"
            
            # Draw node as a circle
            canvas.create_oval(x-15, y-15, x+15, y+15, fill=color, outline="white", width=2, tags=f"node_{node_type}")
            
            # Draw node ID
            canvas.create_text(x, y, text=str(node.node_id), fill="white", font=("Arial", 10, "bold"), tags="node_id")