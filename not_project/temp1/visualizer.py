# visualizer.py
import graphviz # Потрібно встановити: pip install graphviz

def visualize_genome_phenotype(genome, network, filename="genome_phenotype"):
    """
    Створює візуалізацію генотипу та фенотипу за допомогою Graphviz.
    Зберігає результат у файл DOT та PNG.

    Args:
        genome (Genome): Геном для візуалізації.
        network (NeuralNetwork): Фенотип (мережа) для візуалізації.
        filename (str): Ім'я файлу для збереження (без розширення).
    """
    dot = graphviz.Digraph(comment='NEAT Genome and Phenotype')
    dot.attr(rankdir='LR', size='8,5') # Зліва направо

    # Додаємо вузли
    node_attrs = {'shape': 'circle', 'style': 'filled', 'fontsize': '10'}
    output_node_attrs = {'shape': 'doublecircle', 'style': 'filled', 'fontsize': '10'}
    bias_node_attrs = {'shape': 'diamond', 'style': 'filled', 'fontsize': '10', 'fillcolor': 'gray'}

    # Візуалізуємо вузли з геному
    node_labels = {}
    for node_id, node_gene in genome.node_genes.items():
        label = f"ID: {node_id}\nType: {node_gene.type}"
        node_labels[node_id] = label
        attrs = node_attrs.copy()
        if node_gene.type == 'input':
            attrs['fillcolor'] = 'lightblue'
        elif node_gene.type == 'output':
            attrs = output_node_attrs.copy()
            attrs['fillcolor'] = 'lightgreen'
        elif node_gene.type == 'hidden':
             attrs['fillcolor'] = 'lightyellow'
        elif node_gene.type == 'bias':
             attrs = bias_node_attrs.copy()
             label = f"ID: {node_id}\nBias" # Коротший лейбл для bias

        dot.node(str(node_id), label, **attrs)


    # Візуалізуємо зв'язки з геному (відображаємо статус enabled/disabled)
    for innov, conn_gene in genome.connection_genes.items():
        attrs = {'fontsize': '8'}
        label = f"w={conn_gene.weight:.2f}\ni={conn_gene.innovation_number}"
        if conn_gene.enabled:
            attrs['color'] = 'green' if conn_gene.weight >= 0 else 'red'
            attrs['penwidth'] = str(1 + abs(conn_gene.weight) * 1.5) # Товщина залежить від ваги
            attrs['style'] = 'solid'
        else:
            attrs['color'] = 'gray'
            attrs['style'] = 'dashed' # Вимкнені зв'язки пунктиром

        dot.edge(str(conn_gene.in_node_id), str(conn_gene.out_node_id), label=label, **attrs)


    # Збереження та рендеринг
    try:
        dot.render(filename, format='png', view=False, cleanup=True)
        print(f"--- Visualization saved to {filename}.png and {filename}.dot")
    except Exception as e:
        print(f"--- Failed to render visualization with Graphviz: {e}")
        print("--- Make sure Graphviz is installed and in your system's PATH.")
        print("--- Textual representation of the genome:")
        print(genome)


def print_genome_textual(genome):
    """Просто виводить геном у текстовому форматі."""
    print("-" * 30)
    print("Genome (Textual Representation):")
    print("-" * 30)
    print(genome)
    print("-" * 30)