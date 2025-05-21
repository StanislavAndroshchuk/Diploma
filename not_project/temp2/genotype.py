class Genome:
    def __init__(self):
        self.node_genes = {}
        self.connection_genes = {}

class NodeGene:
    def __init__(self):
        self.id = None
        self.type = enumerate(['input', 'output', 'hidden'])
        self.activation_function = None

class ConnectionGene:
    def __init__(self):
        self.in_node_id = None
        self.out_node_id = None
        self.weight = None
        self.enabled = True
        self.innovation_number = None