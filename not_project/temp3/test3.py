import tkinter as tk
from tkinter import ttk, Canvas, Frame, Label, Button, StringVar
import random
import math
from PIL import Image, ImageTk, ImageDraw

class Node:
    def __init__(self, node_id, node_type, layer=0, x=0, y=0):
        self.id = node_id
        self.type = node_type  # "input", "hidden", or "output"
        self.layer = layer
        self.x = x
        self.y = y
        self.innovation_number = node_id

class Connection:
    def __init__(self, input_node, output_node, weight, enabled=True, innovation_num=None):
        self.input_node = input_node
        self.output_node = output_node
        self.weight = weight
        self.enabled = enabled
        self.innovation_number = innovation_num if innovation_num else random.randint(1, 1000)

class Genome:
    def __init__(self, nodes=None, connections=None, fitness=0.0):
        self.nodes = nodes or []
        self.connections = connections or []
        self.fitness = fitness
        
    def clone(self):
        """Create a deep copy of this genome"""
        nodes = [Node(n.id, n.type, n.layer, n.x, n.y) for n in self.nodes]
        connections = []
        for c in self.connections:
            in_node_idx = next(i for i, n in enumerate(self.nodes) if n.id == c.input_node)
            out_node_idx = next(i for i, n in enumerate(self.nodes) if n.id == c.output_node)
            connections.append(Connection(
                nodes[in_node_idx].id, 
                nodes[out_node_idx].id, 
                c.weight, 
                c.enabled, 
                c.innovation_number
            ))
        return Genome(nodes, connections, self.fitness)

    def add_connection_mutation(self):
        """Add a new connection between two nodes that aren't already connected"""
        # Get list of possible connections (input→hidden, input→output, hidden→hidden, hidden→output)
        possible_connections = []
        for in_node in self.nodes:
            if in_node.type == "output":
                continue  # Output nodes can't be inputs to connections
                
            for out_node in self.nodes:
                if out_node.type == "input":
                    continue  # Input nodes can't be outputs of connections
                    
                # Check if the connection already exists
                if not any(c.input_node == in_node.id and c.output_node == out_node.id for c in self.connections):
                    # Avoid recurrent connections for simplicity
                    if in_node.layer < out_node.layer:
                        possible_connections.append((in_node, out_node))
        
        if not possible_connections:
            return False  # No possible new connections
        
        # Choose a random connection to add
        in_node, out_node = random.choice(possible_connections)
        weight = random.uniform(-1, 1)
        
        # Find the next innovation number
        max_innov = max([c.innovation_number for c in self.connections]) if self.connections else 0
        
        # Add the new connection
        self.connections.append(Connection(in_node.id, out_node.id, weight, True, max_innov + 1))
        return True

    def add_node_mutation(self):
        """Split an existing connection and add a node in the middle"""
        if not self.connections:
            return False  # No connections to split
            
        # Choose a random enabled connection to split
        eligible_connections = [c for c in self.connections if c.enabled]
        if not eligible_connections:
            return False
            
        conn = random.choice(eligible_connections)
        conn.enabled = False  # Disable the original connection
        
        # Get the nodes on each end of the connection
        in_node = next(n for n in self.nodes if n.id == conn.input_node)
        out_node = next(n for n in self.nodes if n.id == conn.output_node)
        
        # Create a new node
        next_node_id = max([n.id for n in self.nodes]) + 1
        new_layer = (in_node.layer + out_node.layer) / 2
        x_pos = (in_node.x + out_node.x) / 2
        y_pos = (in_node.y + out_node.y) / 2
        new_node = Node(next_node_id, "hidden", new_layer, x_pos, y_pos)
        self.nodes.append(new_node)
        
        # Find the next innovation numbers
        max_innov = max([c.innovation_number for c in self.connections])
        
        # Create two new connections
        self.connections.append(Connection(
            in_node.id, new_node.id, 1.0, True, max_innov + 1
        ))
        self.connections.append(Connection(
            new_node.id, out_node.id, conn.weight, True, max_innov + 2
        ))
        
        return True

def crossover(genome1, genome2):
    """Perform crossover between two genomes"""
    # For simplicity, just take the fitter parent's structure
    if genome1.fitness > genome2.fitness:
        parent1, parent2 = genome1, genome2
    else:
        parent1, parent2 = genome2, genome1
    
    child = parent1.clone()
    
    # For each matching connection gene, randomly choose which parent's weight to inherit
    for i, conn1 in enumerate(child.connections):
        # Find matching connection in parent2 by innovation number
        matching_conn = next((c for c in parent2.connections 
                              if c.innovation_number == conn1.innovation_number), None)
        
        if matching_conn and random.random() < 0.5:
            # Inherit weight from parent2
            child.connections[i].weight = matching_conn.weight
            
            # Also inherit enabled/disabled status with some probability
            if not matching_conn.enabled and conn1.enabled and random.random() < 0.75:
                child.connections[i].enabled = False
    
    return child

def create_simple_genome():
    """Create a simple initial genome with input and output nodes only"""
    nodes = [
        Node(1, "input", 0, 100, 100),
        Node(2, "input", 0, 100, 200),
        Node(3, "input", 0, 100, 300),
        Node(4, "output", 1, 300, 200),
    ]
    
    connections = [
        Connection(1, 4, random.uniform(-1, 1), True, 1),
        Connection(2, 4, random.uniform(-1, 1), True, 2),
        Connection(3, 4, random.uniform(-1, 1), True, 3),
    ]
    
    return Genome(nodes, connections, random.uniform(0, 10))

class NEATVisualizationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NEAT Visualization Tool")
        self.root.geometry("1200x800")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 12))
        
        # Initialize genomes
        self.genome1 = create_simple_genome()
        self.genome2 = create_simple_genome()
        self.current_genome = self.genome1
        
        # Create main frames
        self.control_frame = Frame(root, width=300, bg="#f0f0f0")
        self.control_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        self.visualization_frame = Frame(root)
        self.visualization_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Setup control panel
        self.setup_control_panel()
        
        # Setup visualization area
        self.setup_visualization_area()
        
        # Initial visualization
        self.update_visualizations()
    
    def setup_control_panel(self):
        # Title
        title_label = Label(self.control_frame, text="NEAT Controls", font=("Arial", 14, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Current genome info
        self.genome_info_var = StringVar()
        genome_info_label = Label(self.control_frame, textvariable=self.genome_info_var, 
                                 font=("Arial", 10), bg="#f0f0f0", justify="left")
        genome_info_label.pack(pady=10, anchor="w")
        
        # Mutations section
        mutations_frame = ttk.LabelFrame(self.control_frame, text="Mutations")
        mutations_frame.pack(fill="x", padx=5, pady=10)
        
        add_conn_btn = ttk.Button(mutations_frame, text="Add Connection", 
                                 command=self.add_connection_mutation)
        add_conn_btn.pack(fill="x", padx=5, pady=5)
        
        add_node_btn = ttk.Button(mutations_frame, text="Add Node", 
                                 command=self.add_node_mutation)
        add_node_btn.pack(fill="x", padx=5, pady=5)
        
        # Genome selection and crossover
        crossover_frame = ttk.LabelFrame(self.control_frame, text="Genomes & Crossover")
        crossover_frame.pack(fill="x", padx=5, pady=10)
        
        view_genome1_btn = ttk.Button(crossover_frame, text="View Genome 1", 
                                    command=lambda: self.switch_genome(1))
        view_genome1_btn.pack(fill="x", padx=5, pady=5)
        
        view_genome2_btn = ttk.Button(crossover_frame, text="View Genome 2", 
                                    command=lambda: self.switch_genome(2))
        view_genome2_btn.pack(fill="x", padx=5, pady=5)
        
        crossover_btn = ttk.Button(crossover_frame, text="Perform Crossover", 
                                 command=self.perform_crossover)
        crossover_btn.pack(fill="x", padx=5, pady=5)
        
        # Randomize fitness
        randomize_frame = ttk.LabelFrame(self.control_frame, text="Randomize")
        randomize_frame.pack(fill="x", padx=5, pady=10)
        
        randomize_fitness_btn = ttk.Button(randomize_frame, text="Randomize Fitness", 
                                         command=self.randomize_fitness)
        randomize_fitness_btn.pack(fill="x", padx=5, pady=5)
        
        reset_btn = ttk.Button(self.control_frame, text="Reset Genomes", 
                              command=self.reset_genomes)
        reset_btn.pack(fill="x", padx=5, pady=10)
    
    def setup_visualization_area(self):
        # Create tabs for phenotype and genotype
        self.tab_control = ttk.Notebook(self.visualization_frame)
        
        self.phenotype_tab = ttk.Frame(self.tab_control)
        self.genotype_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.phenotype_tab, text="Phenotype")
        self.tab_control.add(self.genotype_tab, text="Genotype")
        self.tab_control.pack(expand=1, fill="both")
        
        # Setup phenotype canvas
        self.phenotype_canvas = Canvas(self.phenotype_tab, bg="white")
        self.phenotype_canvas.pack(fill="both", expand=True)
        
        # Setup genotype canvas
        self.genotype_canvas = Canvas(self.genotype_tab, bg="white")
        self.genotype_canvas.pack(fill="both", expand=True)
    
    def update_visualizations(self):
        """Update both phenotype and genotype visualizations"""
        self.update_phenotype_visualization()
        self.update_genotype_visualization()
        self.update_genome_info()
    
    def update_phenotype_visualization(self):
        """Draw the neural network (phenotype)"""
        self.phenotype_canvas.delete("all")
        
        # Calculate node positions based on layers
        self.calculate_node_positions()
        
        # Draw connections first (so they're behind nodes)
        for conn in self.current_genome.connections:
            if not conn.enabled:
                continue
                
            # Find the source and target nodes
            source_node = next((n for n in self.current_genome.nodes if n.id == conn.input_node), None)
            target_node = next((n for n in self.current_genome.nodes if n.id == conn.output_node), None)
            
            if source_node and target_node:
                # Determine connection color and width based on weight
                color = "blue" if conn.weight >= 0 else "red"
                width = abs(conn.weight) * 2
                
                self.phenotype_canvas.create_line(
                    source_node.x, source_node.y, 
                    target_node.x, target_node.y,
                    width=width, fill=color, arrow=tk.LAST)
        
        # Draw nodes
        for node in self.current_genome.nodes:
            if node.type == "input":
                color = "#66BB6A"  # Green
            elif node.type == "output":
                color = "#EF5350"  # Red
            else:
                color = "#42A5F5"  # Blue
            
            self.phenotype_canvas.create_oval(
                node.x - 15, node.y - 15, 
                node.x + 15, node.y + 15,
                fill=color, outline="black", width=2
            )
            
            self.phenotype_canvas.create_text(
                node.x, node.y, text=str(node.id),
                fill="white", font=("Arial", 10, "bold")
            )
    
    def update_genotype_visualization(self):
        """Draw the genome representation (genotype)"""
        self.genotype_canvas.delete("all")
        
        # Create image with PIL for more advanced drawing
        width, height = self.genotype_canvas.winfo_width(), self.genotype_canvas.winfo_height()
        if width <= 1:  # Not yet properly initialized
            width, height = 800, 600
        
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)
        
        # Draw dividing line
        mid_x = width // 2
        draw.line([(mid_x, 0), (mid_x, height)], fill="black", width=2)
        
        # Draw "Genotype" and "Phenotype" headers
        draw.text((mid_x // 2, 20), "Node Genes", fill="black")
        draw.text((mid_x + mid_x // 2, 20), "Connection Genes", fill="black")
        
        # Draw node genes
        start_y = 70
        box_height = 40
        box_width = 150
        spacing = 10
        
        for i, node in enumerate(self.current_genome.nodes):
            x = 50
            y = start_y + i * (box_height + spacing)
            
            # Draw box
            draw.rectangle([(x, y), (x + box_width, y + box_height)], outline="black", width=2)
            
            # Draw text
            node_info = f"Node {node.id}\n{node.type.capitalize()} Layer"
            draw.text((x + 5, y + 5), node_info, fill="black")
        
        # Draw connection genes
        start_y = 70
        box_height = 60
        box_width = 180
        
        for i, conn in enumerate(self.current_genome.connections):
            x = mid_x + 50
            y = start_y + i * (box_height + spacing)
            
            # Draw box
            fill_color = "white" if conn.enabled else "#f0f0f0"
            draw.rectangle([(x, y), (x + box_width, y + box_height)], fill=fill_color, outline="black", width=2)
            
            # Draw text
            conn_info = f"In {conn.input_node}\nOut {conn.output_node}\nWeight: {conn.weight:.2f}\n"
            conn_info += f"{'Enabled' if conn.enabled else 'Disabled'}\nInnov {conn.innovation_number}"
            draw.text((x + 5, y + 5), conn_info, fill="black")
        
        # Convert to PhotoImage and display
        self.genotype_image = ImageTk.PhotoImage(img)
        self.genotype_canvas.create_image(0, 0, image=self.genotype_image, anchor="nw")
    
    def calculate_node_positions(self):
        """Calculate positions for drawing nodes in the neural network"""
        # Get canvas dimensions
        width = self.phenotype_canvas.winfo_width()
        height = self.phenotype_canvas.winfo_height()
        
        if width <= 1:  # Canvas not yet properly initialized
            width, height = 800, 600
        
        # Group nodes by layer
        layers = {}
        for node in self.current_genome.nodes:
            if node.layer not in layers:
                layers[node.layer] = []
            layers[node.layer].append(node)
        
        # Sort layers
        sorted_layers = sorted(layers.keys())
        
        # Calculate horizontal spacing
        h_spacing = width / (len(sorted_layers) + 1)
        
        # Position nodes in each layer
        for i, layer in enumerate(sorted_layers):
            nodes = layers[layer]
            v_spacing = height / (len(nodes) + 1)
            
            for j, node in enumerate(nodes):
                node.x = (i + 1) * h_spacing
                node.y = (j + 1) * v_spacing
    
    def update_genome_info(self):
        """Update the displayed genome information"""
        info_text = f"Current: {'Genome 1' if self.current_genome == self.genome1 else 'Genome 2'}\n"
        info_text += f"Fitness: {self.current_genome.fitness:.2f}\n"
        info_text += f"Nodes: {len(self.current_genome.nodes)}\n"
        info_text += f"Connections: {len(self.current_genome.connections)}\n"
        info_text += f"Enabled connections: {sum(1 for c in self.current_genome.connections if c.enabled)}"
        
        self.genome_info_var.set(info_text)
    
    def add_connection_mutation(self):
        """Add a connection to the current genome"""
        success = self.current_genome.add_connection_mutation()
        if success:
            self.update_visualizations()
        else:
            # Show a message if mutation wasn't possible
            tk.messagebox.showinfo("Mutation Failed", 
                                  "Could not add a connection - all possible connections may already exist.")
    
    def add_node_mutation(self):
        """Add a node to the current genome"""
        success = self.current_genome.add_node_mutation()
        if success:
            self.update_visualizations()
        else:
            # Show a message if mutation wasn't possible
            tk.messagebox.showinfo("Mutation Failed", 
                                  "Could not add a node - no enabled connections to split.")
    
    def switch_genome(self, genome_num):
        """Switch between genome 1 and genome 2"""
        self.current_genome = self.genome1 if genome_num == 1 else self.genome2
        self.update_visualizations()
    
    def perform_crossover(self):
        """Perform crossover between genome 1 and genome 2"""
        child = crossover(self.genome1, self.genome2)
        
        # Replace the current genome with the child
        if self.current_genome == self.genome1:
            self.genome1 = child
            self.current_genome = self.genome1
        else:
            self.genome2 = child
            self.current_genome = self.genome2
        
        self.update_visualizations()
    
    def randomize_fitness(self):
        """Randomize the fitness of both genomes"""
        self.genome1.fitness = random.uniform(0, 10)
        self.genome2.fitness = random.uniform(0, 10)
        self.update_genome_info()
    
    def reset_genomes(self):
        """Reset both genomes to simple initial states"""
        self.genome1 = create_simple_genome()
        self.genome2 = create_simple_genome()
        self.current_genome = self.genome1
        self.update_visualizations()

if __name__ == "__main__":
    root = tk.Tk()
    app = NEATVisualizationApp(root)
    
    # Bind window resize event to update the visualization
    def on_resize(event):
        app.update_visualizations()
    
    root.bind("<Configure>", on_resize)
    root.mainloop()