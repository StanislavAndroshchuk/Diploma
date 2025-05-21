# neat/genome.py
import random
from .node_gene import NodeGene
from .connection_gene import ConnectionGene

class Genome:
    """Represents a genome in NEAT (genotype of neural network)."""
    
    def __init__(self, genome_id):
        """Initialize a genome.
        
        Args:
            genome_id: Unique identifier for this genome
        """
        self.genome_id = genome_id
        self.nodes = {}  # node_id -> NodeGene
        self.connections = {}  # innovation -> ConnectionGene
        self.fitness = 0
        
    def add_node(self, node_id, node_type):
        """Add a node to the genome.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of node (INPUT, HIDDEN, OUTPUT)
        
        Returns:
            The added node gene
        """
        node = NodeGene(node_id, node_type)
        self.nodes[node_id] = node
        return node
        
    def add_connection(self, in_node, out_node, weight=None, enabled=True):
        """Add a connection to the genome.
        
        Args:
            in_node: ID of the input node
            out_node: ID of the output node
            weight: Weight of the connection (random if None)
            enabled: Whether the connection is enabled
        
        Returns:
            The added connection gene or None if the nodes don't exist
        """
        if in_node not in self.nodes or out_node not in self.nodes:
            return None
            
        # Don't allow connections from output to any node or to input
        if self.nodes[in_node].node_type == NodeGene.OUTPUT:
            return None
        if self.nodes[out_node].node_type == NodeGene.INPUT:
            return None
            
        # Check for existing connection
        for conn in self.connections.values():
            if conn.in_node == in_node and conn.out_node == out_node:
                return None
                
        # Create the connection with random weight if none provided
        if weight is None:
            weight = random.uniform(-2.0, 2.0)
            
        connection = ConnectionGene(in_node, out_node, weight, enabled)
        self.connections[connection.innovation] = connection
        return connection
        
    def mutate_add_node(self):
        """Mutate the genome by adding a node.
        
        This is done by splitting an existing connection into two connections
        with a new node in the middle.
        
        Returns:
            True if mutation was successful, False otherwise
        """
        if not self.connections:
            return False
            
        # Choose a random enabled connection to split
        enabled_connections = [c for c in self.connections.values() if c.enabled]
        if not enabled_connections:
            return False
            
        connection = random.choice(enabled_connections)
        
        # Disable the original connection
        connection.enabled = False
        
        # Add a new node
        new_node_id = max(self.nodes.keys()) + 1 if self.nodes else 0
        new_node = self.add_node(new_node_id, NodeGene.HIDDEN)
        
        # Add two new connections
        self.add_connection(connection.in_node, new_node_id, 1.0, True)
        self.add_connection(new_node_id, connection.out_node, connection.weight, True)
        
        return True
        
    def mutate_add_connection(self):
        """Mutate the genome by adding a connection between existing nodes.
        
        Returns:
            True if mutation was successful, False otherwise
        """
        # Get all possible valid connections
        possible_connections = []
        
        for in_node in self.nodes.values():
            for out_node in self.nodes.values():
                # Skip invalid connections
                if in_node.node_type == NodeGene.OUTPUT:
                    continue
                if out_node.node_type == NodeGene.INPUT:
                    continue
                    
                # Skip existing connections
                exists = False
                for conn in self.connections.values():
                    if conn.in_node == in_node.node_id and conn.out_node == out_node.node_id:
                        exists = True
                        break
                        
                if not exists:
                    possible_connections.append((in_node.node_id, out_node.node_id))
        
        if not possible_connections:
            return False
            
        # Choose a random possible connection
        in_node, out_node = random.choice(possible_connections)
        
        # Add the connection
        self.add_connection(in_node, out_node)
        
        return True
        
    def mutate_weight(self):
        """Mutate the weights of the connections.
        
        Returns:
            True if mutation was successful, False otherwise
        """
        if not self.connections:
            return False
            
        for connection in self.connections.values():
            if random.random() < 0.9:  # 90% chance to mutate a weight
                if random.random() < 0.1:  # 10% chance to completely replace weight
                    connection.weight = random.uniform(-2.0, 2.0)
                else:  # 90% chance to perturb weight
                    connection.weight += random.uniform(-0.5, 0.5)
                    
        return True
        
    def mutate_toggle_enable(self):
        """Mutate the genome by toggling the enabled status of a connection.
        
        Returns:
            True if mutation was successful, False otherwise
        """
        if not self.connections:
            return False
            
        connection = random.choice(list(self.connections.values()))
        connection.enabled = not connection.enabled
        
        return True
        
    def mutate(self):
        """Apply mutation to the genome.
        
        There are several types of mutations:
        1. Add a new node
        2. Add a new connection
        3. Mutate connection weights
        4. Toggle connection enable/disable
        
        Returns:
            True if any mutation was applied, False otherwise
        """
        mutated = False
        
        # Add node (with 5% probability)
        if random.random() < 0.05:
            mutated |= self.mutate_add_node()
            
        # Add connection (with 5% probability)
        if random.random() < 0.05:
            mutated |= self.mutate_add_connection()
            
        # Mutate weights (always try)
        mutated |= self.mutate_weight()
        
        # Toggle enable (with 1% probability)
        if random.random() < 0.01:
            mutated |= self.mutate_toggle_enable()
            
        return mutated
        
    def copy(self):
        """Create a copy of this genome."""
        clone = Genome(self.genome_id)
        
        # Copy nodes
        for node_id, node in self.nodes.items():
            clone.nodes[node_id] = node.copy()
            
        # Copy connections
        for innovation, connection in self.connections.items():
            clone.connections[innovation] = connection.copy()
            
        return clone
        
    def create_initial_minimal(self, num_inputs, num_outputs):
        """Create an initial minimal genome with the given number of inputs and outputs.
        
        Args:
            num_inputs: Number of input nodes
            num_outputs: Number of output nodes
        """
        # Create input nodes
        for i in range(num_inputs):
            self.add_node(i, NodeGene.INPUT)
            
        # Create output nodes
        for i in range(num_inputs, num_inputs + num_outputs):
            self.add_node(i, NodeGene.OUTPUT)
            
        # Connect all inputs to all outputs
        for i in range(num_inputs):
            for j in range(num_inputs, num_inputs + num_outputs):
                self.add_connection(i, j)