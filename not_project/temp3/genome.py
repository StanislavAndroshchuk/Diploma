class NodeGene:
    def __init__(self, node_id, node_type):
        self.id = node_id  # Унікальний ідентифікатор вузла
        self.type = node_type  # Тип вузла: 'input', 'output', 'hidden'
        
class ConnectionGene:
    def __init__(self, in_node, out_node, weight, enabled, innovation_number):
        self.in_node = in_node  # ID вхідного вузла
        self.out_node = out_node  # ID вихідного вузла
        self.weight = weight  # Вага зв'язку
        self.enabled = enabled  # Чи активований зв'язок
        self.innovation = innovation_number  # Історичний маркер
        
class Genome:
    def __init__(self):
        self.nodes = {}  # Словник вузлів (id -> NodeGene)
        self.connections = {}  # Словник зв'язків (innovation -> ConnectionGene)
        self.fitness = 0.0  # Значення фітнесу для традиційного NEAT
        self.novelty = 0.0  # Значення новизни для novelty search
        
    def add_node(self, node_id, node_type):
        self.nodes[node_id] = NodeGene(node_id, node_type)
        
    def add_connection(self, in_node, out_node, weight, enabled, innovation):
        self.connections[innovation] = ConnectionGene(in_node, out_node, weight, enabled, innovation)
    
    def mutate_weight(self, innovation, new_weight):
        if innovation in self.connections:
            self.connections[innovation].weight = new_weight
    
    def disable_connection(self, innovation):
        if innovation in self.connections:
            self.connections[innovation].enabled = False
    
    def add_node_mutation(self, old_conn_innovation, new_node_id, new_in_conn_innovation, new_out_conn_innovation):
        # Отримуємо старе з'єднання
        old_conn = self.connections[old_conn_innovation]
        
        # Вимикаємо старе з'єднання
        old_conn.enabled = False
        
        # Додаємо новий вузол
        self.add_node(new_node_id, 'hidden')
        
        # Додаємо нові з'єднання
        self.add_connection(old_conn.in_node, new_node_id, 1.0, True, new_in_conn_innovation)
        self.add_connection(new_node_id, old_conn.out_node, old_conn.weight, True, new_out_conn_innovation)
    
    def add_connection_mutation(self, in_node, out_node, weight, innovation):
        self.add_connection(in_node, out_node, weight, True, innovation)
    
    def copy(self):
        # Створення копії геному
        new_genome = Genome()
        
        # Копіювання вузлів
        for node_id, node in self.nodes.items():
            new_genome.add_node(node_id, node.type)
            
        # Копіювання зв'язків
        for innovation, conn in self.connections.items():
            new_genome.add_connection(conn.in_node, conn.out_node, conn.weight, conn.enabled, conn.innovation)
            
        return new_genome