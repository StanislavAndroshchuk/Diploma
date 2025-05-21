import random
import math # Import math for potentially sigmoid-like activation, not strictly needed for genome structure, but good practice

from node import Node
from connection import Connection

class Genome:
    """Represents a genome encoding a neural network."""
    def __init__(self):
        self.nodes = {}  # Dictionary of Node objects, key is node_id
        self.connections = {}  # Dictionary of Connection objects, key is (in_node_id, out_node_id)
        self.next_node_id = 0
        # In a full NEAT implementation, innovation numbers are global across the species/population
        # For this visualization, we'll use a simple incrementing counter within the genome
        self.next_innovation_num = 0

    def add_node(self, node_type):
        """Adds a new node to the genome."""
        node = Node(self.next_node_id, node_type)
        self.nodes[self.next_node_id] = node
        self.next_node_id += 1
        return node

    def add_connection(self, in_node_id, out_node_id, weight, enabled=True):
        """Adds a new connection gene to the genome."""
        # Check if node IDs are valid
        if in_node_id not in self.nodes or out_node_id not in self.nodes:
             print(f"Error adding connection: Node IDs {in_node_id} or {out_node_id} not found.")
             return None

        # Check if connection already exists
        if (in_node_id, out_node_id) in self.connections:
            # print(f"Warning: Connection from {in_node_id} to {out_node_id} already exists.")
            return None # Or handle as an error/warning

        connection = Connection(in_node_id, out_node_id, weight, enabled, self.next_innovation_num)
        self.connections[(in_node_id, out_node_id)] = connection
        # In a real NEAT, innovation numbers are handled more carefully across the population
        self.next_innovation_num += 1
        return connection

    def create_initial_network(self, num_inputs, num_outputs):
        """Creates a basic initial network with input and output nodes."""
        self.nodes = {}
        self.connections = {}
        self.next_node_id = 0
        self.next_innovation_num = 0

        # Add input nodes
        for _ in range(num_inputs):
            self.add_node("input")

        # Add output nodes
        for _ in range(num_outputs):
            self.add_node("output")

        # You might want to add initial connections here, e.g., fully connected input to output,
        # or start with no connections and let mutations build the network.
        # For simplicity in visualization of mutations, starting with just nodes is fine.

    def mutate_add_connection(self):
        """Attempts to add a new random connection."""
        if len(self.nodes) < 2:
            # print("Not enough nodes to add a connection.")
            return False, "Недостатньо вузлів для додавання зв'язку."

        # Get lists of node ids by type
        input_node_ids = [node_id for node_id, node in self.nodes.items() if node.node_type == "input"]
        output_node_ids = [node_id for node_id, node in self.nodes.items() if node.node_type == "output"]
        hidden_node_ids = [node_id for node_id, node in self.nodes.items() if node.node_type == "hidden"]

        possible_in_node_ids = input_node_ids + hidden_node_ids
        possible_out_node_ids = output_node_ids + hidden_node_ids + hidden_node_ids # Can connect to hidden nodes twice as likely? Or just include all

        if not possible_in_node_ids or not possible_out_node_ids:
            return False, "Немає можливих вузлів для з'єднання."

        # Try adding a connection a few times to avoid infinite loops on full graphs or cycles
        attempts = 100
        for _ in range(attempts):
            in_node_id = random.choice(possible_in_node_ids)
            out_node_id = random.choice(possible_out_node_ids)

            # Avoid self-connections
            if in_node_id == out_node_id:
                continue

            # Avoid connecting to input nodes
            if self.nodes[out_node_id].node_type == "input":
                 continue

            # Simple check to prevent obvious cycles in a feedforward network (connecting back to an input or from output)
            if self.nodes[in_node_id].node_type == "output":
                 continue
            # A more robust cycle detection for hidden-to-hidden connections would require graph traversal.
            # For this visualization, we keep it simple.

            # Check if connection already exists
            if (in_node_id, out_node_id) in self.connections:
                continue

            # Add the connection
            weight = random.uniform(-1, 1)
            new_connection = self.add_connection(in_node_id, out_node_id, weight)
            if new_connection:
                return True, f"Додано зв'язок: {new_connection}"

        return False, f"Не вдалося додати зв'язок після {attempts} спроб (можливі причини: повний граф, уникнення циклів, недостатньо вузлів)."

    def mutate_add_node(self):
        """Attempts to add a new node on an existing enabled connection."""
        enabled_connections = [conn for conn in self.connections.values() if conn.enabled]

        if not enabled_connections:
            return False, "Немає активних зв'язків для додавання вузла."

        # Choose a random enabled connection
        chosen_connection = random.choice(enabled_connections)

        # Disable the chosen connection
        chosen_connection.enabled = False

        # Create a new hidden node
        new_node = self.add_node("hidden")

        # Create two new connections:
        # 1. From the original input node to the new hidden node with weight 1.0
        # 2. From the new hidden node to the original output node with the weight of the disabled connection
        in_node_id = chosen_connection.in_node_id
        out_node_id = chosen_connection.out_node_id
        original_weight = chosen_connection.weight

        conn1 = self.add_connection(in_node_id, new_node.node_id, 1.0)
        conn2 = self.add_connection(new_node.node_id, out_node_id, original_weight)

        if conn1 and conn2:
             return True, f"Додано вузол {new_node.node_id} на зв'язку {chosen_connection.in_node_id} -> {chosen_connection.out_node_id}. Створено нові зв'язки: {conn1}, {conn2}. Оригінальний зв'язок деактивовано."
        else:
             # This case should ideally not happen if add_connection is robust,
             # but good for debugging. You might need to revert changes if adding fails.
             return False, "Помилка при додаванні нових зв'язків після додавання вузла."


    def mutate_mutate_weights(self, probability=0.8, perturb_probability=0.9, step=0.1):
        """Mutates the weights of connections."""
        mutated_count = 0
        for connection in self.connections.values():
            if random.random() < probability:
                if random.random() < perturb_probability:
                    # Perturb weight
                    connection.weight += random.uniform(-step, step)
                else:
                    # Assign new random weight
                    connection.weight = random.uniform(-1, 1)
                mutated_count += 1
        return mutated_count > 0, f"Змінено ваги {mutated_count} зв'язків."


    def get_genotype_string(self):
        """Returns a structured string representation of the genome."""
        s = "=== Genotype ===\n\n"
        s += "--- Nodes ---\n"
        # Sort nodes by ID for consistent display
        for node_id in sorted(self.nodes.keys()):
            node = self.nodes[node_id]
            s += f"Node ID: {node.node_id}, Type: {node.node_type}\n"

        s += "\n--- Connections ---\n"
        # Sort connections by innovation number or (in_node, out_node) for consistent display
        sorted_connections = sorted(self.connections.values(), key=lambda c: c.innovation_num if c.innovation_num is not None else float('inf'))
        for connection in sorted_connections:
             s += (f"In: {connection.in_node_id}, Out: {connection.out_node_id}, "
                   f"Weight: {connection.weight:.4f}, Enabled: {connection.enabled}, "
                   f"Innovation: {connection.innovation_num}\n")

        s += "\n================"
        return s