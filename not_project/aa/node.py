class Node:
    """Represents a node in the neural network."""
    def __init__(self, node_id, node_type="hidden"):
        self.node_id = node_id
        self.node_type = node_type  # 'input', 'output', 'hidden'
        self.x = 0  # Placeholder for visualization position
        self.y = 0  # Placeholder for visualization position

    def __repr__(self):
        return f"Node(id={self.node_id}, type='{self.node_type}')"