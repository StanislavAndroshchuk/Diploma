class Connection:
    """Represents a connection gene in the genome."""
    def __init__(self, in_node_id, out_node_id, weight, enabled=True, innovation_num=None):
        self.in_node_id = in_node_id
        self.out_node_id = out_node_id
        self.weight = weight
        self.enabled = enabled
        self.innovation_num = innovation_num

    def __repr__(self):
        return (f"Connection(in={self.in_node_id}, out={self.out_node_id}, "
                f"weight={self.weight:.2f}, enabled={self.enabled}, innovation={self.innovation_num})")