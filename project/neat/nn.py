# neat/nn.py

import math
from collections import deque
import traceback
from typing import Optional # Import traceback for detailed error logging

# Імпортуємо потрібні класи та функції з сусіднього файлу genome
from .genome import Genome, NodeGene, ConnectionGene, ACTIVATION_FUNCTIONS

def _get_network_graph(genome: Genome) -> tuple[dict[int, list[int]], dict[int, int]]:
    """
    Допоміжна функція для побудови графа мережі та підрахунку вхідних ступенів.
    Враховує лише УВІМКНЕНІ з'єднання.
    """
    # Включаємо лише ті вузли, що беруть участь у *ввімкнених* з'єднаннях або є вх/вих/біас
    inp_ids, out_ids, bias_id = genome.get_input_output_bias_ids()
    relevant_node_ids = set(inp_ids) | set(out_ids)
    if bias_id is not None:
         relevant_node_ids.add(bias_id)

    enabled_connections = [conn for conn in genome.connections.values() if conn.enabled]

    # Додаємо вузли, які з'єднані активними зв'язками
    for conn in enabled_connections:
         if conn.in_node_id in genome.nodes: # Перевірка наявності вузла
             relevant_node_ids.add(conn.in_node_id)
         if conn.out_node_id in genome.nodes: # Перевірка наявності вузла
             relevant_node_ids.add(conn.out_node_id)

    # Залишаємо тільки ті ID, які реально є в геномі
    relevant_node_ids = {nid for nid in relevant_node_ids if nid in genome.nodes}

    in_degree = {node_id: 0 for node_id in relevant_node_ids}
    out_connections = {node_id: [] for node_id in relevant_node_ids}

    for conn in enabled_connections:
        # Перевіряємо, чи обидва вузли існують і релевантні
        if conn.in_node_id in relevant_node_ids and conn.out_node_id in relevant_node_ids:
            # Перевіряємо, чи вузол призначення є в in_degree (має бути, якщо він релевантний)
            if conn.out_node_id in in_degree:
                 in_degree[conn.out_node_id] += 1
            # Перевіряємо, чи вузол джерела є в out_connections
            if conn.in_node_id in out_connections:
                 out_connections[conn.in_node_id].append(conn.out_node_id)

    return out_connections, in_degree


def determine_evaluation_order(genome: Genome) -> list[int]:
    """
    Визначає порядок обчислення активації вузлів для мережі прямого поширення.
    """
    try:
        out_connections, in_degree = _get_network_graph(genome)
        relevant_node_ids = set(in_degree.keys())
        if not relevant_node_ids: return [] # Немає релевантних вузлів

        # Вузли, що потрібно обчислити (приховані та вихідні)
        nodes_to_activate = {
            nid for nid in relevant_node_ids
            if genome.nodes[nid].type in ("HIDDEN", "OUTPUT")
        }
        if not nodes_to_activate: return [] # Немає вузлів для активації

        queue = deque([node_id for node_id in relevant_node_ids if in_degree[node_id] == 0])
        sorted_nodes = []
        processed_count = 0

        while queue:
            current_node_id = queue.popleft()
            processed_count += 1

            # Додаємо до результату тільки приховані та вихідні
            if current_node_id in nodes_to_activate:
                 sorted_nodes.append(current_node_id)

            # Обробляємо сусідів
            if current_node_id in out_connections:
                # Сортування для детермінізму
                for neighbor_id in sorted(out_connections[current_node_id]):
                     if neighbor_id in in_degree:
                        in_degree[neighbor_id] -= 1
                        if in_degree[neighbor_id] == 0:
                            queue.append(neighbor_id)

        if processed_count != len(relevant_node_ids):
            print(f"Warning: Cycle detected or unconnected nodes in genome {genome.id}. "
                  f"Processed {processed_count} nodes, relevant nodes {len(relevant_node_ids)}. ")
            # Повернемо частковий порядок, якщо він не порожній
            pass # Або return [] якщо це критично

        # Перевірка, чи всі вузли, які потрібно активувати, є у відсортованому списку
        if len(sorted_nodes) != len(nodes_to_activate):
             # Це може статися, якщо приховані/вихідні вузли недосяжні з входів
             missing_nodes = nodes_to_activate - set(sorted_nodes)
             print(f"Warning: Cannot activate all required nodes in genome {genome.id}. Missing: {missing_nodes}")
             # Повертаємо лише ті, що досяжні
             pass


        return sorted_nodes

    except Exception as e:
         print(f"ERROR during determine_evaluation_order for genome {genome.id}: {e}")
         traceback.print_exc() # Друкуємо повний traceback
         return [] # Повертаємо порожній список при помилці


def activate_network(genome: Genome, inputs: list[float]) -> Optional[list[float]]:
    """
    Активує нейронну мережу (фенотип), представлену геномом.
    Повертає список вихідних значень або None у разі внутрішньої помилки.
    """
    # === Додаємо зовнішній try...except ===
    try:
        if not isinstance(genome, Genome):
             raise TypeError("Expected a Genome object.")

        input_ids, output_ids, bias_id = genome.get_input_output_bias_ids()

        if len(inputs) != len(input_ids):
            raise ValueError(f"Genome {genome.id}: Number of inputs ({len(inputs)}) "
                             f"does not match network input nodes ({len(input_ids)})")

        # 1. Скидаємо стан вузлів
        for node in genome.nodes.values():
            node.output_value = 0.0
            node._input_sum = 0.0

        # 2. Встановлюємо значення входів/біасу
        for i, node_id in enumerate(input_ids):
            if node_id in genome.nodes:
                 genome.nodes[node_id].output_value = inputs[i]
            # else: print(f"Warning: Input node ID {node_id} not found in genome {genome.id}.")

        if bias_id is not None and bias_id in genome.nodes:
            genome.nodes[bias_id].output_value = 1.0
        # elif bias_id is not None: print(f"Warning: Bias node ID {bias_id} not found in genome {genome.id}.")

        # 3. Визначаємо порядок активації
        eval_order = determine_evaluation_order(genome)
        if not eval_order and any(n.type != 'INPUT' and n.type != 'BIAS' for n in genome.nodes.values()):
             # Якщо порядок порожній, але є приховані/вихідні вузли, щось не так
             print(f"Warning: Evaluation order is empty for genome {genome.id}, but hidden/output nodes exist.")
             # У цьому випадку мережа не може нічого обчислити коректно

        # 4. Активуємо вузли
        for node_id in eval_order:
            # Перевіряємо, чи вузол існує (про всяк випадок)
            if node_id not in genome.nodes:
                 print(f"ERROR: Node {node_id} from eval_order not found in genome {genome.id}. Skipping.")
                 continue

            node = genome.nodes[node_id]
            node_input_sum = 0.0

            # Сумуємо входи
            # Оптимізація: краще мати pre-computed список вхідних з'єднань для вузла
            for conn in genome.connections.values():
                 if conn.enabled and conn.out_node_id == node_id:
                     if conn.in_node_id in genome.nodes:
                          in_node = genome.nodes[conn.in_node_id]
                          node_input_sum += in_node.output_value * conn.weight
                     # else: print(f"Warning: Input node {conn.in_node_id} for connection {conn.innovation} not found.")

            # Додаємо біас
            node_input_sum += node.bias
            node._input_sum = node_input_sum # Зберігаємо суму перед активацією

            # Застосовуємо функцію активації
            if node.activation_function:
                 # Додаємо try-except навколо виклику функції активації
                 try:
                    node.output_value = node.activation_function(node_input_sum)
                 except Exception as act_e:
                      print(f"ERROR during activation function {node.activation_function_name} for node {node_id} (genome {genome.id}) with input {node_input_sum}: {act_e}")
                      node.output_value = 0.0 # Значення за замовчуванням при помилці
            else:
                 # Наприклад, для вузла без визначеної функції (хоча це мало б бути оброблено в NodeGene)
                 node.output_value = node_input_sum

        # 5. Збираємо результати
        output_values = []
        # Перевіряємо, чи список output_ids існує і не порожній
        if output_ids:
             # Сортуємо для стабільного порядку
             sorted_output_ids = sorted(output_ids)
             for node_id in sorted_output_ids:
                 if node_id in genome.nodes:
                     output_values.append(genome.nodes[node_id].output_value)
                 else:
                      print(f"Warning: Output node ID {node_id} not found in genome {genome.id}. Appending 0.0.")
                      output_values.append(0.0)
        else:
             print(f"Warning: Genome {genome.id} has no output nodes defined in _output_node_ids.")
             # Повертаємо порожній список або список нулів відповідної довжини?
             # Повернемо порожній, це явна помилка.
             return [] # Або None, якщо це краще обробляється вище

        return output_values

    # === Обробка будь-яких інших непередбачених помилок всередині функції ===
    except Exception as e:
        print(f"\n--- UNHANDLED EXCEPTION IN activate_network (Genome ID: {genome.id}) ---")
        print(f"Error Type: {type(e)}")
        print(f"Error Args: {e.args}")
        print("Genome structure that caused error:")
        try:
             print(f" Nodes ({len(genome.nodes)}): {list(genome.nodes.keys())}")
             # print(f" Connections ({len(genome.connections)}): {list(genome.connections.keys())}")
             # for innov, conn in genome.connections.items(): print(f"  {conn}")
        except:
             print(" (Could not print genome details)")
        print("Inputs provided:")
        print(f" {inputs}")
        print("Traceback:")
        traceback.print_exc()
        print("--- END OF EXCEPTION ---")
        # Повертаємо None, щоб зовнішній код міг це обробити
        return None