# phenotype.py
import math

# Проста сигмоїдна функція активації
def sigmoid(x):
   # Використовуємо модифіковану сигмоїду з NEAT для кращої оптимізації [source: 1019]
   try:
       return 1 / (1 + math.exp(-4.9 * x))
   except OverflowError:
       # Обробка дуже великих/малих значень x
       return 0.0 if x < 0 else 1.0


class NeuralNetwork:
    """Фенотип - функціональна нейронна мережа, створена з генотипу."""
    def __init__(self, genome):
        self.input_nodes = []
        self.output_nodes = []
        self.hidden_nodes = []
        self.node_map = {} # {node_id: {'type': ..., 'connections': [(from_id, weight)], 'output': 0.0}}
        self.bias_id = -1

        # --- Будуємо мережу з геному ---
        # 1. Створюємо вузли
        for node_gene in genome.node_genes.values():
            self.node_map[node_gene.id] = {'type': node_gene.type, 'connections': [], 'output': 0.0, 'summed_input': 0.0}
            if node_gene.type == 'input':
                self.input_nodes.append(node_gene.id)
            elif node_gene.type == 'output':
                self.output_nodes.append(node_gene.id)
            elif node_gene.type == 'hidden':
                self.hidden_nodes.append(node_gene.id)
            elif node_gene.type == 'bias':
                self.bias_id = node_gene.id
                self.node_map[node_gene.id]['output'] = 1.0 # Bias завжди 1

        # 2. Додаємо активні зв'язки
        for conn_gene in genome.connection_genes.values():
            if conn_gene.enabled: # Враховуємо тільки активні гени [source: 920]
                if conn_gene.out_node_id in self.node_map: # Переконуємось, що вузол існує
                    # Додаємо вхідний зв'язок до вихідного вузла
                    self.node_map[conn_gene.out_node_id]['connections'].append(
                        (conn_gene.in_node_id, conn_gene.weight)
                    )

        # 3. Сортування вузлів для feed-forward активації (дуже базове)
        #    Для рекурентних мереж потрібен складніший підхід (напр., активація за кроками)
        #    Це сортування передбачає, що мережа є DAG (Directed Acyclic Graph)
        self.activation_order = self._get_activation_order()


    def _get_activation_order(self):
        """
        Виконує топологічне сортування для визначення порядку активації вузлів
        у feed-forward мережі. Повертає список ID вузлів.
        Проста реалізація, яка працює для DAG.
        """
        order = []
        visited = set()
        nodes_to_process = list(self.input_nodes)
        if self.bias_id != -1:
             nodes_to_process.append(self.bias_id)

        # Простий підхід: спочатку входи, потім приховані (якщо є), потім виходи
        order.extend(nodes_to_process)
        visited.update(nodes_to_process)

        # Додаємо приховані вузли (для простоти, не гарантує правильний порядок між ними)
        # Повноцінне топологічне сортування складніше
        order.extend(self.hidden_nodes)
        visited.update(self.hidden_nodes)

        order.extend(self.output_nodes)

        # Повертаємо тільки ті ID, що є в node_map (на випадок відключених шляхів)
        return [node_id for node_id in order if node_id in self.node_map]


    def activate(self, input_values):
        """
        Активує мережу для заданих вхідних значень.
        Args:
            input_values (list): Список значень для вхідних вузлів.
        Returns:
            list: Список значень на вихідних вузлах.
        """
        if len(input_values) != len(self.input_nodes):
            raise ValueError("Incorrect number of input values provided.")

        # 1. Встановлюємо значення вхідних вузлів
        for i, node_id in enumerate(self.input_nodes):
            self.node_map[node_id]['output'] = input_values[i]
            self.node_map[node_id]['summed_input'] = input_values[i] # Для візуалізації

        # Встановлюємо вихід bias вузла (якщо він є)
        if self.bias_id != -1 and self.bias_id in self.node_map:
             self.node_map[self.bias_id]['output'] = 1.0
             self.node_map[self.bias_id]['summed_input'] = 1.0


        # 2. Активуємо вузли в топологічному порядку (спрощено)
        for node_id in self.activation_order:
            node_info = self.node_map[node_id]
            node_type = node_info['type']

            # Вхідні та bias вузли вже мають значення
            if node_type == 'input' or node_type == 'bias':
                continue

            # Обчислюємо сумарний вхід для прихованих та вихідних вузлів
            summed_input = 0.0
            for connected_node_id, weight in node_info['connections']:
                 # Переконуємось, що вузол, з якого йде зв'язок, існує
                 if connected_node_id in self.node_map:
                      summed_input += self.node_map[connected_node_id]['output'] * weight
                 else:
                      # Можлива ситуація, якщо вузол був видалений або зв'язок не мав сенсу
                      # print(f"Warning: Source node {connected_node_id} for connection to {node_id} not found.")
                      pass


            node_info['summed_input'] = summed_input

            # Застосовуємо функцію активації (сигмоїду)
            node_info['output'] = sigmoid(summed_input)

        # 3. Збираємо вихідні значення
        output_values = [self.node_map[out_id]['output'] for out_id in self.output_nodes]
        return output_values

    def __repr__(self):
        return f"NeuralNetwork (Inputs: {len(self.input_nodes)}, Hidden: {len(self.hidden_nodes)}, Outputs: {len(self.output_nodes)})"