import math
import tkinter as tk
from tkinter import ttk, scrolledtext
import random
# We won't use networkx for drawing directly on canvas, but the structure logic is based on it.
# We will use PIL for potential anti-aliasing, though direct canvas drawing will be the main approach first.
from PIL import Image, ImageDraw, ImageTk # Import PIL modules

# Reuse NEAT core classes (Node, Connection, Genome)
# Global innovation number counter (for demonstration purposes)
global_innovation_number = 0
global_node_id = 0

def next_innovation_number():
    """Increments and returns the global innovation number."""
    global global_innovation_number
    global_innovation_number += 1
    return global_innovation_number

def next_node_id():
    """Increments and returns the global node ID."""
    global global_node_id
    global_node_id += 1
    return global_node_id

class Node:
    """Represents a single neuron node in the network."""
    def __init__(self, node_id, node_type):
        self.id = node_id
        self.type = node_type  # 'input', 'hidden', 'output', 'bias'
        # Position for visualization (will be set by the visualization logic)
        self.pos = None # (x, y) tuple

    def __repr__(self):
        return f"Node(id={self.id}, type='{self.type}')"

    def __str__(self):
         return f"Node {self.id} ({self.type})"


class Connection:
    """Represents a connection between two nodes."""
    def __init__(self, in_node_id, out_node_id, weight, enabled, innovation_number):
        self.in_node_id = in_node_id
        self.out_node_id = out_node_id
        self.weight = weight
        self.enabled = enabled
        self.innovation_number = innovation_number

    def __repr__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"Connection(in={self.in_node_id}, out={self.out_node_id}, weight={self.weight:.2f}, {status}, innov={self.innovation_number})"

    def __str__(self):
         status = "enabled" if self.enabled else "disabled"
         return f"Conn {self.in_node_id} -> {self.out_node_id} (w={self.weight:.2f}, innov={self.innovation_number}, {status})"


class Genome:
    """Represents the genotype of a neural network."""
    def __init__(self, input_size, output_size, include_bias=True):
        self.nodes = {}  # Dictionary of Node objects: {node_id: Node}
        self.connections = {} # Dictionary of Connection objects: {innovation_number: Connection}
        self.fitness = 0 # For potential future use

        # Initialize with minimal structure: inputs -> outputs
        self._initialize_minimal(input_size, output_size, include_bias)

    def _initialize_minimal(self, input_size, output_size, include_bias):
        """Creates a minimal starting structure."""
        global global_node_id, global_innovation_number
        global_node_id = 0
        global_innovation_number = 0

        # Add input nodes
        for _ in range(input_size):
            self.add_node('input')

        # Add bias node
        if include_bias:
             self.add_node('bias')


        # Add output nodes
        for _ in range(output_size):
            self.add_node('output')

        # Connect all inputs (including bias) to all outputs initially
        input_node_ids = [n.id for n in self.nodes.values() if n.type in ['input', 'bias']]
        output_node_ids = [n.id for n in self.nodes.values() if n.type == 'output']

        for in_id in input_node_ids:
            for out_id in output_node_ids:
                self.add_connection(in_id, out_id, weight=random.uniform(-1, 1))


    def add_node(self, node_type):
        """Adds a new node to the genome."""
        new_node_id = next_node_id()
        self.nodes[new_node_id] = Node(new_node_id, node_type)
        return new_node_id

    def add_connection(self, in_node_id, out_node_id, weight=None, enabled=True):
        """Adds a new connection to the genome."""
        # In a real NEAT implementation, you'd check for existing connections
        # and reuse innovation numbers if the exact same connection has been seen before
        # across the entire population's history.
        # For this simple example, we'll just generate a new innovation number every time.

        if weight is None:
            weight = random.uniform(-1, 1) # Assign random weight

        innov_num = next_innovation_number()
        # Check if the exact connection gene already exists (same in, out, innov_num)
        # This is a simplified check, a real system needs global innovation tracking.
        for conn in self.connections.values():
             if conn.in_node_id == in_node_id and conn.out_node_id == out_node_id:
                 # If a connection between these two nodes exists, reuse its innovation number
                 # This is a critical part of NEAT's historical marking
                 # However, for this simple demo, we'll just assign a new one always
                 pass # Simplification for demo

        self.connections[innov_num] = Connection(in_node_id, out_node_id, weight, enabled, innov_num)
        return innov_num

    def mutate_add_connection(self):
        """Applies the add connection mutation."""
        # Select two random nodes to connect
        # Ensure they are not the same node
        # Avoid connecting 'output' to 'input' or 'hidden' to 'input' or 'output' to 'output' etc.
        # This needs careful consideration of allowed connections in a feedforward network.

        # Get lists of node IDs by type
        input_ids = [n.id for n in self.nodes.values() if n.type == 'input']
        output_ids = [n.id for n in self.nodes.values() if n.type == 'output']
        hidden_ids = [n.id for n in self.nodes.values() if n.type == 'hidden']
        bias_ids = [n.id for n in self.nodes.values() if n.type == 'bias']

        # Possible source nodes: inputs, bias, hidden
        possible_sources = input_ids + bias_ids + hidden_ids
        # Possible destination nodes: hidden, outputs
        possible_destinations = hidden_ids + output_ids

        if not possible_sources or not possible_destinations:
             print("Cannot add connection: Not enough eligible nodes.")
             return False

        in_node_id = random.choice(possible_sources)
        out_node_id = random.choice(possible_destinations)

        # Prevent self-loops
        while in_node_id == out_node_id:
            in_node_id = random.choice(possible_sources)
            out_node_id = random.choice(possible_destinations)

        # Prevent connecting backwards in a simple layered sense (approximate check)
        # This is a simplification; a real NEAT checks for cycles more robustly.
        in_node_type = self.nodes[in_node_id].type
        out_node_type = self.nodes[out_node_id].type

        # Simple layer check: input < bias < hidden < output
        layer_order = {'input': 0, 'bias': 1, 'hidden': 2, 'output': 3}

        # Keep selecting until a valid pair is found or attempts run out
        attempts = 0
        max_attempts = 100
        while (in_node_id == out_node_id or layer_order[in_node_type] > layer_order[out_node_type] or
               (in_node_type == out_node_type and in_node_type in ['input', 'output']) or # No input-input or output-output
               any(conn.in_node_id == in_node_id and conn.out_node_id == out_node_id and conn.enabled for conn in self.connections.values())): # Check if enabled connection already exists

            in_node_id = random.choice(possible_sources)
            out_node_id = random.choice(possible_destinations)
            in_node_type = self.nodes[in_node_id].type
            out_node_type = self.nodes[out_node_id].type
            attempts += 1
            if attempts > max_attempts:
                print("Could not find a suitable connection point after multiple attempts.")
                return False # Failed to find a valid connection

        innov_num = self.add_connection(in_node_id, out_node_id)
        print(f"Mutated: Added connection from {in_node_id} to {out_node_id} (Innov: {innov_num})")
        return True

    def mutate_add_node(self):
        """Applies the add node mutation."""
        # Select a random enabled connection to split
        enabled_connections = [conn for conn in self.connections.values() if conn.enabled]

        if not enabled_connections:
            print("Cannot add node: No enabled connections to split.")
            return False

        # Select a connection to split (weighted by innovation number to prefer older ones is an option,
        # but random is simpler for this demo)
        conn_to_split = random.choice(enabled_connections)

        # Disable the old connection
        conn_to_split.enabled = False

        # Check if a node was already added on this specific historical connection
        # In a real NEAT, this prevents multiple nodes being added to the same original connection.
        # We'd need a mapping from (in_node, out_node) before split -> new_node_id
        # For this demo, we'll simplify and just add a new node every time this mutation is triggered on *any* enabled connection.

        # Create a new node (it's always a hidden node)
        new_node_id = self.add_node('hidden')
        print(f"Mutated: Added new node {new_node_id} by splitting connection (Innov: {conn_to_split.innovation_number})")

        # Add two new connections: from old_in to new_node, and from new_node to old_out
        # These get new innovation numbers
        self.add_connection(conn_to_split.in_node_id, new_node_id, weight=1.0) # Weight 1.0
        self.add_connection(new_node_id, conn_to_split.out_node_id, weight=conn_to_split.weight) # Inherit weight

        return True


    def get_genotype_info(self):
        """Returns a string summary of the genotype."""
        info = "--- Genotype Info ---\n"
        info += f"Nodes ({len(self.nodes)}):\n"
        # Sort nodes by ID for readability
        for node_id in sorted(self.nodes.keys()):
             node = self.nodes[node_id]
             info += f"  - {node}\n"

        info += f"\nConnections ({len(self.connections)}):\n"
        # Sort connections by innovation number
        sorted_connections = sorted(self.connections.values(), key=lambda c: c.innovation_number)
        for conn in sorted_connections:
             info += f"  - {conn}\n"
        info += "---------------------"
        return info


class NeatVisualizationApp:
    def __init__(self, root, input_size, output_size):
        self.root = root
        root.title("NEAT Mutation Visualization")

        self.input_size = input_size
        self.output_size = output_size
        self.genome = None # Will hold the current genome

        self._create_widgets()
        self._setup_layout()

        # Create initial genome on startup
        self.create_initial_genome()

    def _create_widgets(self):
        """Creates all the GUI widgets."""
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_width = 800
        self.canvas_height = 500
        # Use PIL for potential anti-aliasing, though direct canvas drawing will be used for simplicity first
        self.image = Image.new('RGB', (self.canvas_width, self.canvas_height), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.photo_image = ImageTk.PhotoImage(self.image)

        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Keep a reference to the image to prevent garbage collection
        self._canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)


        self.controls_frame = ttk.Frame(self.root)

        self.btn_initial = ttk.Button(self.controls_frame, text="Create Initial Genome", command=self.create_initial_genome)
        self.btn_add_conn = ttk.Button(self.controls_frame, text="Mutate: Add Connection", command=self.mutate_add_connection)
        self.btn_add_node = ttk.Button(self.controls_frame, text="Mutate: Add Node", command=self.mutate_add_node)

        self.genotype_label = ttk.Label(self.controls_frame, text="Genotype Info:")
        self.genotype_text = scrolledtext.ScrolledText(self.controls_frame, wrap=tk.WORD, width=60, height=10)
        self.genotype_text.insert(tk.END, "Genotype information will appear here.")
        self.genotype_text.config(state=tk.DISABLED) # Make it read-only

        # "Testing Tools" placeholders - showing probabilities or just the mutation buttons
        # For this example, the mutation buttons and the genotype info ARE the main "tools".
        # We could add entries for mutation rates if we were doing continuous evolution.
        # Let's add a simple label indicating this section.
        self.tools_label = ttk.Label(self.controls_frame, text="Mutation Controls:", font=('Arial', 10, 'bold'))


    def _setup_layout(self):
        """Sets up the layout of the widgets."""
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Layout controls within the controls_frame
        self.tools_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        self.btn_initial.grid(row=1, column=0, padx=5, pady=5)
        self.btn_add_conn.grid(row=1, column=1, padx=5, pady=5)
        self.btn_add_node.grid(row=1, column=2, padx=5, pady=5)

        self.genotype_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(10, 2))
        self.genotype_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)


    def create_initial_genome(self):
        """Creates a new initial genome and updates the display."""
        self.genome = Genome(self.input_size, self.output_size, include_bias=True)
        self.update_display("Initial Genome Created")

    def mutate_add_connection(self):
        """Applies add connection mutation and updates display."""
        if self.genome:
            self.genome.mutate_add_connection()
            self.update_display("Add Connection Mutation Applied")
        else:
            print("Create a genome first.")

    def mutate_add_node(self):
        """Applies add node mutation and updates display."""
        if self.genome:
            self.genome.mutate_add_node()
            self.update_display("Add Node Mutation Applied")
        else:
            print("Create a genome first.")

    def update_display(self, status_message=""):
        """Updates the canvas visualization and genotype text."""
        print(status_message)
        if self.genome:
            self.draw_phenotype_on_canvas()
            self.update_genotype_text()

    def update_genotype_text(self):
        """Updates the text area with current genotype info."""
        self.genotype_text.config(state=tk.NORMAL)
        self.genotype_text.delete(1.0, tk.END)
        if self.genome:
            self.genotype_text.insert(tk.END, self.genome.get_genotype_info())
        self.genotype_text.config(state=tk.DISABLED)


    def draw_phenotype_on_canvas(self):
        """Draws the current genome's phenotype on the tkinter canvas."""
        if not self.genome:
            return

        # Clear previous drawing
        self.canvas.delete("all")

        # Redraw the background image
        self.image = Image.new('RGB', (self.canvas_width, self.canvas_height), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.photo_image = ImageTk.PhotoImage(self.image)
        self._canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image) # Update reference


        # --- Position Calculation ---
        # This is similar to the matplotlib version, but tailored for canvas coordinates
        # Canvas coordinates: (0,0) top-left, x increases right, y increases DOWN

        node_radius = 15
        layer_spacing_x = self.canvas_width / 3.5 # Horizontal space between layers
        node_spacing_y = 50 # Vertical space between nodes in a layer
        padding_x = 50
        padding_y = 30
        jitter_strength = 20 # Pixels of random jitter

        input_nodes = [n for n in self.genome.nodes.values() if n.type == 'input']
        output_nodes = [n for n in self.genome.nodes.values() if n.type == 'output']
        hidden_nodes = [n for n in self.genome.nodes.values() if n.type == 'hidden']
        bias_nodes = [n for n in self.genome.nodes.values() if n.type == 'bias']

        # Sort nodes for consistent vertical positioning
        input_nodes.sort(key=lambda n: n.id)
        output_nodes.sort(key=lambda n: n.id)
        hidden_nodes.sort(key=lambda n: n.id)
        bias_nodes.sort(key=lambda n: n.id)

        # Calculate total height needed for each layer
        input_layer_height = max(len(input_nodes), 1) * node_spacing_y
        output_layer_height = max(len(output_nodes), 1) * node_spacing_y
        hidden_layer_height = max(len(hidden_nodes), 1) * node_spacing_y

        # Center the layers vertically
        input_start_y = (self.canvas_height - input_layer_height) / 2 + padding_y
        output_start_y = (self.canvas_height - output_layer_height) / 2 + padding_y
        hidden_start_y = (self.canvas_height - hidden_layer_height) / 2 + padding_y # Simple centering for hidden

        # Assign positions
        # Input nodes (left)
        for i, node in enumerate(input_nodes):
            x = padding_x + random.uniform(-jitter_strength, jitter_strength)
            y = input_start_y + i * node_spacing_y + random.uniform(-jitter_strength, jitter_strength)
            node.pos = (x, y)

        # Bias nodes (slightly right of input, or just above/below)
        for i, node in enumerate(bias_nodes):
            # Position bias node near inputs, maybe slightly offset
            x = padding_x + layer_spacing_x * 0.2 + random.uniform(-jitter_strength, jitter_strength)
            y = input_start_y - node_spacing_y + i * node_spacing_y * 0.5 + random.uniform(-jitter_strength, jitter_strength) # Place slightly above inputs
            node.pos = (x, y)

        # Output nodes (right)
        for i, node in enumerate(output_nodes):
            x = self.canvas_width - padding_x + random.uniform(-jitter_strength, jitter_strength)
            y = output_start_y + i * node_spacing_y + random.uniform(-jitter_strength, jitter_strength)
            node.pos = (x, y)

        # Hidden nodes (between input and output, try to order based on "depth" or just list order)
        # For simplicity, just place them in a column in the middle with jitter.
        for i, node in enumerate(hidden_nodes):
            x = padding_x + layer_spacing_x + random.uniform(-jitter_strength, jitter_strength)
            y = hidden_start_y + i * node_spacing_y + random.uniform(-jitter_strength, jitter_strength)
            node.pos = (x, y)


        # --- Draw Connections (on PIL image first for potential AA) ---
        # Use PIL Draw object
        for conn in self.genome.connections.values():
            if conn.enabled:
                start_node = self.genome.nodes[conn.in_node_id]
                end_node = self.genome.nodes[conn.out_node_id]

                if start_node.pos and end_node.pos:
                    x1, y1 = start_node.pos
                    x2, y2 = end_node.pos

                    # Determine line color based on weight
                    line_color = (0, 255, 0) if conn.weight >= 0 else (255, 0, 0) # Green for positive, Red for negative
                    # Determine line thickness based on absolute weight
                    line_width = max(1, int(abs(conn.weight) * 3 + 1)) # Min thickness 1

                    # Draw the line
                    # PIL Draw line doesn't directly support arrowheads or anti-aliasing easily for complex shapes
                    # We'll draw directly on canvas with basic AA if available, or manually simulate.
                    # Let's try drawing directly on canvas for simplicity first.

                    # Calculate vector for arrowhead
                    dx = x2 - x1
                    dy = y2 - y1
                    length = math.sqrt(dx**2 + dy**2)
                    # Normalize vector
                    if length > 0:
                        udx = dx / length
                        udy = dy / length
                    else: # Nodes are at the same position, shouldn't happen with positioning logic
                         udx, udy = 0, 0

                    # Point just before the end node circle
                    end_x = x2 - udx * node_radius
                    end_y = y2 - udy * node_radius

                    # Draw the line segment up to the point before the end node
                    self.canvas.create_line(x1, y1, end_x, end_y,
                                             fill=f'#{line_color[0]:02x}{line_color[1]:02x}{line_color[2]:02x}',
                                             width=line_width,
                                             arrow=tk.LAST, arrowshape=(10, 12, 5)) # arrowhead shape (size_across, size_back, size_tip)

                    # Draw weight label near the middle of the line
                    mid_x, mid_y = (x1 + end_x) / 2, (y1 + end_y) / 2
                    self.canvas.create_text(mid_x, mid_y, text=f"{conn.weight:.2f}", font=('Arial', 8), fill='blue')


        # --- Draw Nodes (on Canvas) ---
        for node in self.genome.nodes.values():
            if node.pos:
                x, y = node.pos
                fill_color = 'skyblue' if node.type == 'input' else 'lightcoral' if node.type == 'output' else 'lightgreen' if node.type == 'hidden' else 'yellow' # bias
                outline_color = 'black'

                # Draw the circle
                self.canvas.create_oval(x - node_radius, y - node_radius,
                                        x + node_radius, y + node_radius,
                                        fill=fill_color, outline=outline_color)

                # Draw node ID/label
                self.canvas.create_text(x, y, text=str(node.id), fill='black', font=('Arial', 10, 'bold'))


        # Update the canvas to show drawn elements (this is automatic after create_ calls)
        # If using PIL image, you would update the canvas image here:
        # self.photo_image = ImageTk.PhotoImage(self.image)
        # self.canvas.itemconfig(self._canvas_image_id, image=self.photo_image)


# --- Main Application Setup ---
if __name__ == "__main__":
    root = tk.Tk()
    # Set input/output sizes for the example
    input_size = 3
    output_size = 2
    app = NeatVisualizationApp(root, input_size, output_size)
    root.mainloop()