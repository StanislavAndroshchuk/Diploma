
import random
from innovation import get_innovation_number 

class NodeGene:
    def __init__(self, node_id, node_type):
        """
        Args:
            node_id (int): Унікальний ідентифікатор вузла.
            node_type (str): Тип вузла ('input', 'output', 'hidden', 'bias').
        """
        self.id = node_id
        self.type = node_type # 'input', 'output', 'hidden', 'bias'
        # Можна додати інші властивості, напр., функцію активації для CPPN/HyperNEAT

    def __repr__(self):
        return f"NodeGene(id={self.id}, type='{self.type}')"

class ConnectionGene:
    """Представляє ген зв'язку між двома вузлами."""
    def __init__(self, in_node_id, out_node_id, weight, enabled, innovation_number):
        """
        Args:
            in_node_id (int): ID вхідного вузла.
            out_node_id (int): ID вихідного вузла.
            weight (float): Вага зв'язку.
            enabled (bool): Чи активний зв'язок.
            innovation_number (int): Історичний маркер зв'язку.
        """
        self.in_node_id = in_node_id
        self.out_node_id = out_node_id
        self.weight = weight
        self.ention_nabled = enabled
        self.innovaumber = innovation_number

    def __repr__(self):
        status = "enabled" if self.enabled else "disabled"
        return (f"ConnectionGene(in={self.in_node_id}, out={self.out_node_id}, "
                f"weight={self.weight:.3f}, status={status}, innov={self.innovation_number})")

# --- Клас Геному ---
class Genome:
    """Представляє повний геном (креслення) для нейронної мережі."""
    def __init__(self, num_inputs, num_outputs):
        self.node_genes = {}  # Словник: {node_id: NodeGene}
        self.connection_genes = {} # Словник: {innovation_number: ConnectionGene}
        self.next_node_id = 0 # Лічильник для ID нових вузлів

        # --- Ініціалізація мінімальної структури ---
        # Створюємо вхідні вузли (включаючи вузол зміщення - bias)
        input_ids = []
        for _ in range(num_inputs):
            node_id = self._get_new_node_id()
            self.node_genes[node_id] = NodeGene(node_id, 'input')
            input_ids.append(node_id)

        # Додаємо вузол зміщення (bias)
        bias_id = self._get_new_node_id()
        self.node_genes[bias_id] = NodeGene(bias_id, 'bias')
        input_ids.append(bias_id) # Bias теж вважається вхідним для зв'язків

        # Створюємо вихідні вузли
        output_ids = []
        for _ in range(num_outputs):
            node_id = self._get_new_node_id()
            self.node_genes[node_id] = NodeGene(node_id, 'output')
            output_ids.append(node_id)

        # --- Початкове з'єднання (мінімальна топологія) ---
        # З'єднуємо кожен вхідний вузол (включаючи bias) з кожним вихідним
        for in_id in input_ids:
            for out_id in output_ids:
                # Призначаємо випадкову вагу
                weight = random.uniform(-1.0, 1.0)
                # Отримуємо унікальний інноваційний номер
                innov_num = get_innovation_number()
                # Створюємо та додаємо ген зв'язку
                conn_gene = ConnectionGene(in_id, out_id, weight, enabled=True, innovation_number=innov_num)
                self.connection_genes[innov_num] = conn_gene

    def _get_new_node_id(self):
        """Генерує та повертає новий унікальний ID для вузла."""
        new_id = self.next_node_id
        self.next_node_id += 1
        return new_id

    def mutate_add_connection(self):
        """
        Мутація: Додає новий зв'язок між двома раніше не з'єднаними вузлами.
        """
        possible_starts = [nid for nid, node in self.node_genes.items() if node.type != 'output']
        possible_ends = [nid for nid, node in self.node_genes.items() if node.type != 'input' and node.type != 'bias']

        attempts = 0
        max_attempts = 20 # Щоб уникнути нескінченного циклу у щільних мережах

        while attempts < max_attempts:
            attempts += 1
            start_node_id = random.choice(possible_starts)
            end_node_id = random.choice(possible_ends)

            # Перевіряємо, чи вузли однакові або чи це спроба створити зв'язок з input/bias
            if start_node_id == end_node_id or self.node_genes[end_node_id].type in ['input', 'bias']:
                 continue

            # Перевірка на рекурентність (проста, для чисто feed-forward можна посилити)
            # Тут можна додати перевірку на цикли, якщо потрібно

            # Перевіряємо, чи такий зв'язок вже існує
            connection_exists = False
            for gene in self.connection_genes.values():
                if gene.in_node_id == start_node_id and gene.out_node_id == end_node_id:
                    connection_exists = True
                    break

            if not connection_exists:
                # Зв'язок не існує, додаємо новий
                new_weight = random.uniform(-1.0, 1.0)
                new_innov_num = get_innovation_number()
                new_conn = ConnectionGene(start_node_id, end_node_id, new_weight, enabled=True, innovation_number=new_innov_num)
                self.connection_genes[new_innov_num] = new_conn
                print(f"--- Mutate Add Connection: Added {new_conn}")
                return # Мутація успішна

        print("--- Mutate Add Connection: Failed to find a new connection after several attempts.")


    def mutate_add_node(self):
        """
        Мутація: Додає новий прихований вузол, розщеплюючи існуючий зв'язок.
        """
        if not self.connection_genes:
            print("--- Mutate Add Node: No connections to split.")
            return

        # Вибираємо випадковий існуючий зв'язок для розщеплення
        connection_to_split = random.choice(list(self.connection_genes.values()))

        # Вимикаємо старий зв'язок [source: 927]
        connection_to_split.enabled = False

        # Створюємо новий прихований вузол [source: 926]
        new_node_id = self._get_new_node_id()
        self.node_genes[new_node_id] = NodeGene(new_node_id, 'hidden')

        # Створюємо два нові зв'язки [source: 927]
        # 1. Зв'язок від початкового вузла старого зв'язку до нового вузла
        innov1 = get_innovation_number()
        weight1 = 1.0 # Згідно з папером NEAT [source: 928]
        conn1 = ConnectionGene(connection_to_split.in_node_id, new_node_id, weight1, enabled=True, innovation_number=innov1)
        self.connection_genes[innov1] = conn1

        # 2. Зв'язок від нового вузла до кінцевого вузла старого зв'язку
        innov2 = get_innovation_number()
        weight2 = connection_to_split.weight # Зберігаємо оригінальну вагу [source: