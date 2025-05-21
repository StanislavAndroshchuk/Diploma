from genome import Genome
import random
def crossover(parent1, parent2):
    # Передбачається, що parent1 має кращий фітнес
    child = Genome()
    
    # Додаємо всі вузли від обох батьків
    for node_id, node in parent1.nodes.items():
        child.add_node(node_id, node.type)
    
    for node_id, node in parent2.nodes.items():
        if node_id not in child.nodes:
            child.add_node(node_id, node.type)
    
    # Обробляємо зв'язки
    for innovation, conn1 in parent1.connections.items():
        if innovation in parent2.connections:
            # Випадковий вибір зв'язку від батьків
            conn2 = parent2.connections[innovation]
            weight = conn1.weight if random.random() < 0.5 else conn2.weight
            enabled = conn1.enabled if random.random() < 0.5 else conn2.enabled
            
            # Якщо обидва батьки мають вимкнений зв'язок, дитина також може мати його вимкненим
            if not conn1.enabled and not conn2.enabled:
                enabled = False if random.random() < 0.75 else True
                
            child.add_connection(conn1.in_node, conn1.out_node, weight, enabled, innovation)
        else:
            # Disjoint або excess ген від parent1 (з більшим фітнесом)
            child.add_connection(conn1.in_node, conn1.out_node, conn1.weight, conn1.enabled, innovation)
    
    return child