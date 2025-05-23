# neat/genome.py

import random
import math
import copy # Імпортуємо модуль copy для глибокого копіювання
from typing import Optional, Dict, List, Tuple # Додаємо типізацію

# Імпортуємо InnovationManager (переконайтесь, що він доступний)
try:
    from .innovation import InnovationManager
except ImportError:
    # Якщо запускаємо файл окремо, може виникнути помилка імпорту
    print("Warning: Could not import InnovationManager. Assuming it's defined elsewhere for standalone run.")
    class InnovationManager: # Заглушка для автономного запуску
        def get_connection_innovation(self, *args): return 0
        def register_node_addition(self, *args): return (0, 0, 0)

# --- Константи та Допоміжні Функції ---

NODE_TYPES = ["INPUT", "OUTPUT", "HIDDEN", "BIAS"]

# --- Функції активації ---
def sigmoid(x: float) -> float:
    """Стійка до переповнення версія сигмоїди (коеф. 4.9 з NEAT)."""
    try:
        return 1.0 / (1.0 + math.exp(-4.9 * x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0

def relu(x: float) -> float:
    """Rectified Linear Unit."""
    return max(0.0, x)

def linear(x: float) -> float:
    """Лінійна функція активації (ідентичність)."""
    return x

# Словник доступних функцій активації
ACTIVATION_FUNCTIONS = {
    "sigmoid": sigmoid,
    "relu": relu,
    "linear": linear,
}
# Функція активації за замовчуванням для нових вузлів
DEFAULT_ACTIVATION = "sigmoid"

# --- Класи Генів ---

class NodeGene:
    """Представляє ген вузла (нейрона) в геномі."""
    def __init__(self, node_id: int, node_type: str, bias: Optional[float] = None, activation_func: str = DEFAULT_ACTIVATION):
        self.id = int(node_id)
        node_type_upper = node_type.upper()
        if node_type_upper not in NODE_TYPES:
            raise ValueError(f"Invalid node type: {node_type}")
        self.type = node_type_upper

        # Ініціалізуємо біас випадково в діапазоні [-1, 1], якщо не задано
        self.bias = float(bias) if bias is not None else random.uniform(-1.0, 1.0)

        # Встановлюємо функцію активації
        if self.type in ("INPUT", "BIAS"):
            self.activation_function_name = "linear"
            self.activation_function = linear
        else:
            func_name = activation_func if activation_func in ACTIVATION_FUNCTIONS else DEFAULT_ACTIVATION
            if activation_func not in ACTIVATION_FUNCTIONS:
                 print(f"Warning: Unsupported activation '{activation_func}'. Using default '{DEFAULT_ACTIVATION}'.")
            self.activation_function_name = func_name
            self.activation_function = ACTIVATION_FUNCTIONS[func_name]

        # Тимчасові сховища для активації мережі (для nn.py)
        self.output_value: float = 0.0
        self._input_sum: float = 0.0

    def __repr__(self) -> str:
        """Рядкове представлення гена вузла."""
        return (f"NodeGene(id={self.id}, type={self.type}, "
                f"bias={self.bias:.3f}, act='{self.activation_function_name}')")

    def copy(self) -> 'NodeGene':
        """Створює копію гена вузла."""
        return NodeGene(self.id, self.type, self.bias, self.activation_function_name)

class ConnectionGene:
    """Представляє ген з'єднання (вагу) в геномі."""
    def __init__(self, in_node_id: int, out_node_id: int, weight: float, enabled: bool, innovation_num: int):
        self.in_node_id = int(in_node_id)
        self.out_node_id = int(out_node_id)
        self.weight = float(weight)
        self.enabled = bool(enabled)
        self.innovation = int(innovation_num) # Історичний маркер

    def __repr__(self) -> str:
        """Рядкове представлення гена з'єднання."""
        status = "Enabled" if self.enabled else "Disabled"
        return (f"ConnGene(innov={self.innovation}: {self.in_node_id} -> {self.out_node_id}, "
                f"w={self.weight:.3f}, status={status})")

    def copy(self) -> 'ConnectionGene':
        """Створює копію гена з'єднання."""
        return ConnectionGene(self.in_node_id, self.out_node_id, self.weight, self.enabled, self.innovation)

# --- Клас Геному ---

class Genome:
    """
    Представляє повний геном (нейронну мережу).
    Містить вузли та з'єднання, а також методи для мутації та кросоверу.
    """
    def __init__(self, genome_id: int, num_inputs: int, num_outputs: int, config: dict, innovation_manager: InnovationManager): # Додано innovation_manager
        """
        Ініціалізує геном з мінімальною структурою.
        """
        self.id = genome_id
        self.config = config # Зберігаємо посилання на конфігурацію
        self.nodes: Dict[int, NodeGene] = {}          # Словник: node_id -> NodeGene
        self.connections: Dict[int, ConnectionGene] = {}    # Словник: innovation_num -> ConnectionGene
        self._input_node_ids: List[int] = []
        self._output_node_ids: List[int] = []
        self._bias_node_id: Optional[int] = None
        self.fitness: float = 0.0       # Нескоригована пристосованість
        self.adjusted_fitness: float = 0.0 # Пристосованість після fitness sharing
        self.species_id: Optional[int] = None   # ID виду

        node_counter = 0 # Лічильник для початкових ID

        # Створюємо вхідні вузли
        for _ in range(num_inputs):
            node_id = node_counter
            # Вхідні вузли не мають біасу і використовують лінійну активацію
            self.nodes[node_id] = NodeGene(node_id, "INPUT", bias=0.0, activation_func='linear')
            self._input_node_ids.append(node_id)
            node_counter += 1

        # Створюємо біас-вузол
        self._bias_node_id = node_counter
        self.nodes[self._bias_node_id] = NodeGene(self._bias_node_id, "BIAS", bias=0.0, activation_func='linear')
        self.nodes[self._bias_node_id].output_value = 1.0 # Вихід біасу завжди 1.0
        node_counter += 1

        # Створюємо вихідні вузли
        for _ in range(num_outputs):
            node_id = node_counter
            self.nodes[node_id] = NodeGene(node_id, "OUTPUT", activation_func=DEFAULT_ACTIVATION)
            self._output_node_ids.append(node_id)
            node_counter += 1

        # Ініціалізація з'єднань: всі входи + біас до всіх виходів
        num_initial_connections = self.config.get('INITIAL_CONNECTIONS', 10)
        all_inputs_ids = self._input_node_ids + [self._bias_node_id] # Включаємо біас
        #innov_num_counter = 0 # Початкові інновації (0, 1, 2, ...)
        weight_init_range = self.config.get('WEIGHT_INIT_RANGE', 1.0)

        possible_initial_pairs: List[Tuple[int, int]] = []
        for in_id in all_inputs_ids:
             for out_id in self._output_node_ids:
                 possible_initial_pairs.append((in_id, out_id))
        num_to_create = min(num_initial_connections, len(possible_initial_pairs))
        chosen_pairs = random.sample(possible_initial_pairs, num_to_create)
        for in_id, out_id in chosen_pairs:
             weight = random.uniform(-weight_init_range, weight_init_range)
             enabled = True
             # Використовуємо InnovationManager для отримання номера інновації
             # Це гарантує унікальність і правильну послідовність на старті
             innov = innovation_manager.get_connection_innovation(in_id, out_id) # ПРАВИЛЬНО
             self.connections[innov] = ConnectionGene(in_id, out_id, weight, enabled, innov)

    # --- Метод копіювання геному ---
    def copy(self) -> 'Genome':
        """Створює глибоку копію цього геному."""
        # !!! ВАЖЛИВО: При копіюванні innovation_manager НЕ копіюється, використовується той самий конфіг !!!
        # Створюємо новий екземпляр, використовуючи ID та конфіг оригіналу
        # num_inputs/outputs тут не важливі, бо ми перезапишемо списки ID
        new_genome = Genome(self.id, 0, 0, self.config, InnovationManager())
        new_genome.id = self.id # Відновлюємо ID (або генеруємо новий в neat_algorithm)
        # Копіюємо основні атрибути
        new_genome.fitness = self.fitness
        new_genome.adjusted_fitness = self.adjusted_fitness
        new_genome.species_id = self.species_id
        # Копіюємо списки ID (вони містять лише числа)
        new_genome._input_node_ids = list(self._input_node_ids)
        new_genome._output_node_ids = list(self._output_node_ids)
        new_genome._bias_node_id = self._bias_node_id
        # Глибоке копіювання словників вузлів та з'єднань
        # Викликаємо copy() для кожного гена
        new_genome.nodes = {nid: node.copy() for nid, node in self.nodes.items()}
        new_genome.connections = {innov: conn.copy() for innov, conn in self.connections.items()}

        return new_genome

    # --- Методи додавання генів ---
    def add_node(self, node_gene: NodeGene):
        """Додає NodeGene до геному (з можливою заміною)."""
        if node_gene.id in self.nodes:
            # print(f"Warning: Node {node_gene.id} already exists in genome {self.id}. Overwriting.")
            pass
        self.nodes[node_gene.id] = node_gene

    def add_connection(self, conn_gene: ConnectionGene):
        """Додає ConnectionGene до геному (з можливою заміною)."""
        if conn_gene.innovation in self.connections:
            # print(f"Warning: Connection {conn_gene.innovation} already exists in genome {self.id}. Overwriting.")
            pass
        self.connections[conn_gene.innovation] = conn_gene

    # --- Методи доступу ---
    def get_node_ids(self) -> List[int]:
        """Повертає відсортований список ID всіх вузлів."""
        return sorted(self.nodes.keys())

    def get_connection_innovs(self) -> List[int]:
        """Повертає відсортований список інноваційних номерів з'єднань."""
        return sorted(self.connections.keys())

    def get_input_output_bias_ids(self) -> Tuple[List[int], List[int], Optional[int]]:
        """Повертає ID вхідних, вихідних та біас вузлів."""
        return self._input_node_ids, self._output_node_ids, self._bias_node_id

    # --- Методи мутацій ---
    def mutate_weights(self):
        """Мутує ваги та біаси згідно параметрів конфігурації."""
        prob_mutate = self.config.get('WEIGHT_MUTATE_RATE', 0.8)
        prob_replace = self.config.get('WEIGHT_REPLACE_RATE', 0.1)
        mutate_power = self.config.get('WEIGHT_MUTATE_POWER', 0.5)
        cap = self.config.get('WEIGHT_CAP', 8.0)

        # Мутація ваг з'єднань
        for conn in self.connections.values():
            if random.random() < prob_mutate:
                if random.random() < prob_replace:
                    conn.weight = random.uniform(-cap, cap)
                else:
                    # Збурення за Гауссом
                    perturbation = random.gauss(0, mutate_power)
                    conn.weight += perturbation
                    conn.weight = max(-cap, min(cap, conn.weight)) # Обмеження

        # Мутація біасів прихованих та вихідних вузлів
        for node in self.nodes.values():
            if node.type in ("HIDDEN", "OUTPUT"):
                if random.random() < prob_mutate:
                     if random.random() < prob_replace:
                          node.bias = random.uniform(-cap, cap)
                     else:
                          perturbation = random.gauss(0, mutate_power)
                          node.bias += perturbation
                          node.bias = max(-cap, min(cap, node.bias))

    def mutate_add_connection(self, innovation_manager: InnovationManager, max_attempts: int = 20) -> bool:
        """Намагається додати нове з'єднання між існуючими вузлами."""
        possible_starts = [nid for nid, n in self.nodes.items() if n.type != "OUTPUT"]
        possible_ends = [nid for nid, n in self.nodes.items() if n.type not in ("INPUT", "BIAS")]

        if not possible_starts or not possible_ends:
            return False # Немає можливих кінців/початків

        for _ in range(max_attempts):
            start_node_id = random.choice(possible_starts)
            end_node_id = random.choice(possible_ends)

            # Перевірка на недопустимі з'єднання
            if start_node_id == end_node_id: continue # Петля на себе
            # TODO: Додати перевірку на цикли, якщо мережа має бути строго FF

            connection_exists = False
            reverse_connection_exists = False # Для FF
            for conn in self.connections.values():
                if conn.in_node_id == start_node_id and conn.out_node_id == end_node_id:
                    connection_exists = True
                    break
                # Для строго FF, забороняємо і зворотне з'єднання
                if conn.in_node_id == end_node_id and conn.out_node_id == start_node_id:
                    reverse_connection_exists = True
                    # break # Можна зупинитись, якщо знайдено зворотне

            # Не додаємо, якщо пряме існує, або якщо зворотне існує (для FF)
            if connection_exists or reverse_connection_exists:
                 continue

            # Додаємо нове з'єднання
            weight_init_range = self.config.get('WEIGHT_INIT_RANGE', 1.0)
            weight = random.uniform(-weight_init_range, weight_init_range)
            innov = innovation_manager.get_connection_innovation(start_node_id, end_node_id)
            new_conn = ConnectionGene(start_node_id, end_node_id, weight, True, innov)
            self.add_connection(new_conn)
            return True # Успішно додали

        return False # Не вдалося знайти місце для нового з'єднання

    def mutate_add_node(self, innovation_manager: InnovationManager) -> bool:
        """Намагається додати новий вузол, розділивши існуюче увімкнене з'єднання."""
        enabled_connections = [conn for conn in self.connections.values() if conn.enabled]
        if not enabled_connections:
            return False # Немає активних з'єднань для розділення

        conn_to_split = random.choice(enabled_connections)

        # Вимикаємо старе з'єднання
        conn_to_split.enabled = False

        # Реєструємо інновацію додавання вузла
        innovation_data = innovation_manager.register_node_addition(
            conn_to_split.innovation,
            conn_to_split.in_node_id,
            conn_to_split.out_node_id
        )
        new_node_id, innov1, innov2 = innovation_data

        # Створюємо новий прихований вузол (якщо ще не існує)
        if new_node_id not in self.nodes:
             # Новий біас може бути 0 або успадкований/випадковий
             new_bias = random.uniform(-0.1, 0.1)
             new_node = NodeGene(new_node_id, "HIDDEN", bias=new_bias, activation_func=DEFAULT_ACTIVATION)
             self.add_node(new_node)

        # Створюємо два нових з'єднання
        # Вага 1.0 для першого, вага старого для другого (згідно NEAT)
        conn1 = ConnectionGene(conn_to_split.in_node_id, new_node_id, 1.0, True, innov1)
        conn2 = ConnectionGene(new_node_id, conn_to_split.out_node_id, conn_to_split.weight, True, innov2)
        self.add_connection(conn1)
        self.add_connection(conn2)
        return True # Успішно додали вузол

    # --- Метод кросоверу ---
    @staticmethod
    def crossover(genome1: 'Genome', genome2: 'Genome', g1_is_fitter: bool) -> 'Genome':
        """Виконує кросовер між двома геномами."""
        config = genome1.config # Беремо конфіг від першого батька
        # Створюємо "порожнього" нащадка
        child = Genome(f"c_{genome1.id}_{genome2.id}", 0, 0, config, InnovationManager())
        child.nodes = {}
        child.connections = {}
        child._input_node_ids = list(genome1._input_node_ids)
        child._output_node_ids = list(genome1._output_node_ids)
        child._bias_node_id = genome1._bias_node_id

        # Копіюємо вузли від більш пристосованого батька
        fitter_parent_nodes = genome1.nodes if g1_is_fitter else genome2.nodes
        for node_id, node_gene in fitter_parent_nodes.items():
            child.add_node(node_gene.copy())
        # Опціонально: додати вузли, які є у менш пристосованого, але відсутні у кращого
        # less_fit_parent_nodes = genome2.nodes if g1_is_fitter else genome1.nodes
        # for node_id, node_gene in less_fit_parent_nodes.items():
        #     if node_id not in child.nodes:
        #         child.add_node(node_gene.copy())

        # Комбінуємо з'єднання
        innovs1 = set(genome1.connections.keys())
        innovs2 = set(genome2.connections.keys())
        matching_innovs = innovs1.intersection(innovs2) # Спільні інновації

        # Успадковуємо відповідні (matching) гени
        for innov in sorted(list(matching_innovs)):
            conn1 = genome1.connections[innov]
            conn2 = genome2.connections[innov]
            # Вибираємо випадково від одного з батьків
            chosen_conn = random.choice([conn1, conn2]).copy()
            # Перевіряємо успадкування вимкненого стану
            disable_prob = config.get('INHERIT_DISABLED_GENE_RATE', 0.75)
            if not conn1.enabled or not conn2.enabled:
                 # Якщо хоча б у одного вимкнено, є шанс успадкувати вимкнений стан
                 chosen_conn.enabled = (random.random() >= disable_prob)
            else:
                 chosen_conn.enabled = True # Якщо в обох увімкнено, залишаємо увімкненим
            child.add_connection(chosen_conn)

        # Успадковуємо роз'єднані (disjoint) та надлишкові (excess) гени
        # Тільки від БІЛЬШ пристосованого батька
        disjoint_excess_innovs = (innovs1 - innovs2) if g1_is_fitter else (innovs2 - innovs1)
        fitter_parent_conns = genome1.connections if g1_is_fitter else genome2.connections

        for innov in sorted(list(disjoint_excess_innovs)):
             # Перевіряємо, чи ця інновація дійсно належить кращому батькові
            if innov in fitter_parent_conns:
                child.add_connection(fitter_parent_conns[innov].copy())

        # Присвоюємо нащадку атрибути (можливо, ID краще генерувати в NeatAlgorithm)
        child.id = f"c_{genome1.id}_{genome2.id}" # Тимчасовий ID
        child.species_id = None # Нащадок ще не належить до виду

        return child

    # --- Метод розрахунку відстані ---
    def distance(self, other_genome: 'Genome', c1: float, c2: float, c3: float) -> float:
        """Обчислює генетичну відстань між цим геномом та іншим."""
        innovs1 = set(self.connections.keys())
        innovs2 = set(other_genome.connections.keys())

        # --- СПРОЩЕННЯ/ПЕРЕВІРКА для однакових структур ---
        if innovs1 == innovs2:
            # Якщо набори інновацій однакові, excess і disjoint = 0
            matching_count = 0
            weight_diff_sum = 0.0
            if not innovs1: return 0.0 # Якщо обидва порожні

            for innov in innovs1:
                # Перевіряємо наявність в обох (має бути, якщо множини рівні)
                if innov in self.connections and innov in other_genome.connections:
                    conn1 = self.connections[innov]
                    conn2 = other_genome.connections[innov]
                    weight_diff_sum += abs(conn1.weight - conn2.weight)
                    matching_count += 1
                else: # Цього не повинно статися, якщо innovs1 == innovs2
                    print(f"Warning: Inconsistency in matching genes despite equal innovation sets (innov={innov})")

            avg_weight_diff = (weight_diff_sum / matching_count) if matching_count > 0 else 0.0
            # Відстань = тільки компонент ваги
            distance = c3 * avg_weight_diff
            print(f"DEBUG (Identical Structure): dist = {c3} * {avg_weight_diff:.4f} = {distance:.4f}") # Debug
            return distance
        # --- КІНЕЦЬ СПРОЩЕННЯ ---

        # --- Стандартний розрахунок для різних структур ---
        max_innov1 = max(innovs1) if innovs1 else 0
        max_innov2 = max(innovs2) if innovs2 else 0

        matching_count = 0
        weight_diff_sum = 0.0
        disjoint_count = 0
        excess_count = 0

        conns1_sorted = sorted(self.connections.values(), key=lambda c: c.innovation)
        conns2_sorted = sorted(other_genome.connections.values(), key=lambda c: c.innovation)
        idx1, idx2 = 0, 0

        while idx1 < len(conns1_sorted) or idx2 < len(conns2_sorted):
            conn1 = conns1_sorted[idx1] if idx1 < len(conns1_sorted) else None
            conn2 = conns2_sorted[idx2] if idx2 < len(conns2_sorted) else None
            innov1 = conn1.innovation if conn1 else float('inf')
            innov2 = conn2.innovation if conn2 else float('inf')

            if innov1 == innov2:
                matching_count += 1
                weight_diff_sum += abs(conn1.weight - conn2.weight)
                idx1 += 1
                idx2 += 1
            elif innov1 < innov2:
                if innov1 <= max_innov2: disjoint_count += 1
                else: excess_count += 1
                idx1 += 1
            elif innov2 < innov1:
                if innov2 <= max_innov1: disjoint_count += 1
                else: excess_count += 1
                idx2 += 1

        num_genes_larger_genome = max(len(conns1_sorted), len(conns2_sorted))
        N = max(1.0, float(num_genes_larger_genome))
        avg_weight_diff = (weight_diff_sum / matching_count) if matching_count > 0 else 0.0

        distance = (c1 * excess_count / N) + (c2 * disjoint_count / N) + (c3 * avg_weight_diff)
        return distance

    # --- Магічні методи ---
    def __lt__(self, other: 'Genome') -> bool:
        """Дозволяє сортувати геноми за фітнесом (менше = гірше)."""
        return self.fitness < other.fitness

    def __repr__(self) -> str:
        """Рядкове представлення геному для налагодження."""
        return (f"Genome(id={self.id}, fit={self.fitness:.4f}, adj_fit={self.adjusted_fitness:.4f}, "
                f"sp={self.species_id}, nodes={len(self.nodes)}, conns={len(self.connections)})")