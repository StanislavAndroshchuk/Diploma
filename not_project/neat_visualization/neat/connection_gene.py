# neat/connection_gene.py
class ConnectionGene:
    """Represents a connection between two nodes in the neural network."""
    
    # Global innovation counter for connections
    innovation_counter = 0
    
    @classmethod
    def get_new_innovation(cls):
        """Get a new innovation number."""
        cls.innovation_counter += 1
        return cls.innovation_counter
    
    def __init__(self, in_node, out_node, weight=1.0, enabled=True):
        """Initialize a connection gene.
        
        Args:
            in_node: ID of the input node
            out_node: ID of the output node
            weight: Weight of the connection
            enabled: Whether the connection is enabled
        """
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.enabled = enabled
        self.innovation = self.get_new_innovation()
        
    def copy(self):
        """Create a copy of this connection gene."""
        clone = ConnectionGene(self.in_node, self.out_node, self.weight, self.enabled)
        clone.innovation = self.innovation
        return clone
        
    def __str__(self):
        """String representation of the connection gene."""
        status = "ENABLED" if self.enabled else "DISABLED"
        return f"Connection {self.in_node} -> {self.out_node} (Weight: {self.weight:.2f}, {status}, Innov: {self.innovation})"