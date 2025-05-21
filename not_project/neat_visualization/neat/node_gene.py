# neat/node_gene.py
class NodeGene:
    """Represents a node in the neural network."""
    
    # Node types
    INPUT = 0
    HIDDEN = 1
    OUTPUT = 2
    
    # Global innovation counter for nodes
    innovation_counter = 0
    
    @classmethod
    def get_new_innovation(cls):
        """Get a new innovation number."""
        cls.innovation_counter += 1
        return cls.innovation_counter
    
    def __init__(self, node_id, node_type):
        """Initialize a node gene.
        
        Args:
            node_id: Unique identifier for this node
            node_type: Type of node (INPUT, HIDDEN, OUTPUT)
        """
        self.node_id = node_id
        self.node_type = node_type
        self.innovation = self.get_new_innovation()
        
        # Position for visualization (to be set based on layer)
        self.x = 0
        self.y = 0
        
    def copy(self):
        """Create a copy of this node gene."""
        clone = NodeGene(self.node_id, self.node_type)
        clone.innovation = self.innovation
        clone.x = self.x
        clone.y = self.y
        return clone
        
    def __str__(self):
        """String representation of the node gene."""
        type_str = "INPUT" if self.node_type == NodeGene.INPUT else "HIDDEN" if self.node_type == NodeGene.HIDDEN else "OUTPUT"
        return f"Node {self.node_id} ({type_str})"