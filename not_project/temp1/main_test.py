# main_test.py
from genotype import Genome
from phenotype import NeuralNetwork
from visualizer import visualize_genome_phenotype, print_genome_textual
import random

# --- Налаштування ---
NUM_INPUTS = 2
NUM_OUTPUTS = 1
random.seed(1000) # Для відтворюваності

# --- Тест ---
print("1. Creating initial minimal genome...")
initial_genome = Genome(NUM_INPUTS, NUM_OUTPUTS)
# print_genome_textual(initial_genome) # Текстовий вивід
network0 = NeuralNetwork(initial_genome)
visualize_genome_phenotype(initial_genome, network0, filename="net_0_initial")

print("\n2. Performing 'Add Node' mutation...")
initial_genome.mutate_add_node()
# print_genome_textual(initial_genome)
network1 = NeuralNetwork(initial_genome)
visualize_genome_phenotype(initial_genome, network1, filename="net_1_add_node")


print("\n3. Performing 'Add Connection' mutation...")
initial_genome.mutate_add_connection()
# print_genome_textual(initial_genome)
network2 = NeuralNetwork(initial_genome)
visualize_genome_phenotype(initial_genome, network2, filename="net_2_add_connection")

print("\n4. Performing another 'Add Connection' mutation...")
initial_genome.mutate_add_connection()
# print_genome_textual(initial_genome)
network3 = NeuralNetwork(initial_genome)
visualize_genome_phenotype(initial_genome, network3, filename="net_3_add_connection_2")


# --- Тестування активації мережі (останньої) ---
print("\n5. Testing network activation...")
final_network = network3
# Приклад вхідних даних (для 2 входів)
input_data = [0.5, -0.2]
output = final_network.activate(input_data)
print(f"Input: {input_data}")
print(f"Output: {output}")

# Можна вивести стан вузлів після активації
# print("\nNode states after activation:")
# for node_id, node_info in final_network.node_map.items():
#      print(f"  Node {node_id} ({node_info['type']}): Input Sum = {node_info['summed_input']:.3f}, Output = {node_info['output']:.3f}")

print("\n--- Test completed ---")