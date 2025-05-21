# Fichier principal: neat_maze_simulation.py

import pygame
import sys
import os
import neat
import numpy as np
import random
import time
import pickle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from pygame.locals import *

# Constantes globales
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
MAZE_WIDTH = 600
MAZE_HEIGHT = 600
CELL_SIZE = 20
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

# Classe Labyrinthe
class Maze:
    def __init__(self, width, height, cell_size):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid_width = width // cell_size
        self.grid_height = height // cell_size
        self.grid = self.generate_maze()
        self.start_pos = (1, 1)
        self.end_pos = (self.grid_width - 2, self.grid_height - 2)
        
    def generate_maze(self):
        # Initialiser la grille avec des murs (1 = mur, 0 = chemin)
        grid = [[1 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Algorithme de génération de labyrinthe (DFS récursif)
        def carve_passages(x, y, grid):
            grid[y][x] = 0  # Marquer la cellule comme chemin
            
            # Directions (N, E, S, O)
            directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height and grid[ny][nx] == 1:
                    # Creuser un passage en mettant la cellule entre les deux à 0
                    grid[y + dy//2][x + dx//2] = 0
                    carve_passages(nx, ny, grid)
                    
        # Commencer à partir d'une cellule aléatoire
        start_x = random.randrange(1, self.grid_width, 2)
        start_y = random.randrange(1, self.grid_height, 2)
        carve_passages(start_x, start_y, grid)
        
        # Assurer que les points de départ et d'arrivée sont accessibles
        grid[1][1] = 0
        grid[self.grid_height-2][self.grid_width-2] = 0
        
        return grid
    
    def is_wall(self, x, y):
        grid_x = x // self.cell_size
        grid_y = y // self.cell_size
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.grid[grid_y][grid_x] == 1
        return True
    
    def get_sensor_readings(self, x, y, angle, num_sensors=8, max_distance=100):
        """Obtenir les lectures des capteurs de distance pour un agent"""
        readings = []
        for i in range(num_sensors):
            # Calculer l'angle du capteur
            sensor_angle = angle + (i * (2 * np.pi / num_sensors))
            
            # Calculer les coordonnées du rayon du capteur
            dx = np.cos(sensor_angle)
            dy = np.sin(sensor_angle)
            
            # Tracer le rayon jusqu'à ce qu'il touche un mur
            distance = 0
            while distance < max_distance:
                distance += 1
                check_x = int(x + dx * distance)
                check_y = int(y + dy * distance)
                
                if self.is_wall(check_x, check_y):
                    break
            
            # Normaliser la distance
            readings.append(distance / max_distance)
            
        return readings
    
    def draw(self, surface):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x] == 1:  # Mur
                    pygame.draw.rect(surface, BLACK, 
                                     (x * self.cell_size, y * self.cell_size, 
                                      self.cell_size, self.cell_size))
        
        # Dessiner le point de départ
        pygame.draw.rect(surface, GREEN, 
                         (self.start_pos[0] * self.cell_size, self.start_pos[1] * self.cell_size, 
                          self.cell_size, self.cell_size))
        
        # Dessiner le point d'arrivée
        pygame.draw.rect(surface, RED, 
                         (self.end_pos[0] * self.cell_size, self.end_pos[1] * self.cell_size, 
                          self.cell_size, self.cell_size))

# Classe Agent (contrôlé par un réseau neuronal)
class Agent:
    def __init__(self, maze, net=None):
        self.maze = maze
        self.net = net
        
        # Position et orientation
        self.x = maze.start_pos[0] * maze.cell_size + maze.cell_size // 2
        self.y = maze.start_pos[1] * maze.cell_size + maze.cell_size // 2
        self.angle = 0  # en radians
        self.speed = 2
        
        # Statistiques
        self.distance_to_goal = self.calculate_distance_to_goal()
        self.fitness = 0
        self.steps = 0
        self.max_steps = 500
        self.is_alive = True
        self.reached_goal = False
        
        # Pour tracer le chemin
        self.path = [(self.x, self.y)]
    
    def calculate_distance_to_goal(self):
        goal_x = self.maze.end_pos[0] * self.maze.cell_size + self.maze.cell_size // 2
        goal_y = self.maze.end_pos[1] * self.maze.cell_size + self.maze.cell_size // 2
        return np.sqrt((self.x - goal_x)**2 + (self.y - goal_y)**2)
    
    def update(self):
        if not self.is_alive or self.reached_goal:
            return
        
        self.steps += 1
        
        # Vérifier si le nombre maximal d'étapes est atteint
        if self.steps >= self.max_steps:
            self.is_alive = False
            return
        
        # Obtenir les lectures des capteurs
        sensors = self.maze.get_sensor_readings(self.x, self.y, self.angle)
        
        # Ajouter la distance normalisée au but comme capteur supplémentaire
        goal_x = self.maze.end_pos[0] * self.maze.cell_size + self.maze.cell_size // 2
        goal_y = self.maze.end_pos[1] * self.maze.cell_size + self.maze.cell_size // 2
        angle_to_goal = np.arctan2(goal_y - self.y, goal_x - self.x) - self.angle
        angle_to_goal = (angle_to_goal + np.pi) % (2 * np.pi) - np.pi  # Normaliser entre -pi et pi
        
        # Entrées du réseau
        inputs = sensors + [np.sin(angle_to_goal), np.cos(angle_to_goal)]
        
        # Obtenir la sortie du réseau (changement d'angle et vitesse)
        if self.net:
            output = self.net.activate(inputs)
            turn = output[0]  # -1 à 1, représentant le changement d'angle
            speed = output[1]  # 0 à 1, représentant la vitesse
            
            # Mettre à jour l'angle et la position
            self.angle += turn * 0.2
            self.x += np.cos(self.angle) * speed * self.speed
            self.y += np.sin(self.angle) * speed * self.speed
        
        # Vérifier les collisions avec les murs
        if self.maze.is_wall(int(self.x), int(self.y)):
            self.is_alive = False
            return
        
        # Enregistrer le chemin
        self.path.append((self.x, self.y))
        
        # Mettre à jour la distance au but
        new_distance = self.calculate_distance_to_goal()
        
        # Récompenser l'agent pour s'approcher du but
        improvement = self.distance_to_goal - new_distance
        self.fitness += improvement if improvement > 0 else 0
        self.distance_to_goal = new_distance
        
        # Vérifier si l'agent a atteint le but
        goal_x = self.maze.end_pos[0] * self.maze.cell_size + self.maze.cell_size // 2
        goal_y = self.maze.end_pos[1] * self.maze.cell_size + self.maze.cell_size // 2
        if np.sqrt((self.x - goal_x)**2 + (self.y - goal_y)**2) < self.maze.cell_size:
            self.reached_goal = True
            self.fitness += 1000  # Bonus pour avoir atteint le but
    
    def draw(self, surface):
        # Dessiner le chemin
        if len(self.path) > 1:
            pygame.draw.lines(surface, BLUE, False, self.path, 2)
        
        # Dessiner l'agent
        pygame.draw.circle(surface, RED if not self.is_alive else GREEN, (int(self.x), int(self.y)), 5)
        
        # Dessiner la direction
        end_x = self.x + np.cos(self.angle) * 10
        end_y = self.y + np.sin(self.angle) * 10
        pygame.draw.line(surface, BLACK, (self.x, self.y), (end_x, end_y), 2)
        
        # Dessiner les capteurs
        sensors = self.maze.get_sensor_readings(self.x, self.y, self.angle)
        for i, distance in enumerate(sensors):
            sensor_angle = self.angle + (i * (2 * np.pi / len(sensors)))
            end_x = self.x + np.cos(sensor_angle) * distance * 100
            end_y = self.y + np.sin(sensor_angle) * distance * 100
            pygame.draw.line(surface, (100, 100, 100), (self.x, self.y), (end_x, end_y), 1)

# Classe pour visualiser le génotype et le phénotype
class NeatVisualizer:
    def __init__(self, genome, config):
        self.genome = genome
        self.config = config
        self.phenotype_surface = None
        self.genotype_surface = None
        self.update_surfaces()
    
    def update_surfaces(self):
        # Créer la surface du phénotype (visualisation du réseau neuronal)
        self.phenotype_surface = self.create_phenotype_surface()
        
        # Créer la surface du génotype (visualisation des gènes)
        self.genotype_surface = self.create_genotype_surface()
    
    def create_phenotype_surface(self):
        # Créer une figure matplotlib pour le réseau neuronal
        fig = plt.figure(figsize=(5, 5))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        
        # Dessiner le réseau neuronal
        nodes = {}
        for node_id, node in self.genome.nodes.items():
            # Déterminer la couche du nœud
            if node_id in self.config.genome_config.input_keys:
                layer = 0
            elif node_id in self.config.genome_config.output_keys:
                layer = 2
            else:
                layer = 1
                
            nodes[node_id] = (node_id, layer)
        
        # Positionner les nœuds
        layers = {}
        for node_id, (_, layer) in nodes.items():
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node_id)
        
        positions = {}
        for layer, layer_nodes in layers.items():
            y_positions = np.linspace(0, 1, len(layer_nodes) + 2)[1:-1]
            for i, node_id in enumerate(layer_nodes):
                positions[node_id] = (layer / 2, y_positions[i])
        
        # Dessiner les connexions
        for conn_gene in self.genome.connections.values():
            if conn_gene.enabled:
                input_id, output_id = conn_gene.key
                ax.plot([positions[input_id][0], positions[output_id][0]],
                        [positions[input_id][1], positions[output_id][1]],
                        'k-', alpha=0.5 if conn_gene.weight > 0 else 0.2,
                        linewidth=abs(conn_gene.weight) * 1.5,
                        color='green' if conn_gene.weight > 0 else 'red')
        
        # Dessiner les nœuds
        for node_id, pos in positions.items():
            if node_id in self.config.genome_config.input_keys:
                node_color = 'lightblue'
            elif node_id in self.config.genome_config.output_keys:
                node_color = 'salmon'
            else:
                node_color = 'lightgreen'
            
            ax.plot(pos[0], pos[1], 'o', markersize=15, 
                   markerfacecolor=node_color, markeredgecolor='black')
            ax.text(pos[0], pos[1], str(node_id), ha='center', va='center')
        
        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, 1.1)
        ax.set_title("Phénotype (Réseau Neuronal)")
        ax.axis('off')
        
        canvas.draw()
        buf = canvas.buffer_rgba()
        surface = pygame.image.frombuffer(buf, fig.canvas.get_width_height(), "RGBA")
        plt.close(fig)
        
        return surface
    
    def create_genotype_surface(self):
        # Créer une surface pour représenter le génotype (les gènes)
        width, height = 400, 600
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((240, 240, 240))
        
        # Dessiner le titre
        font = pygame.font.SysFont('Arial', 20)
        title = font.render("Génotype (Gènes)", True, BLACK)
        surface.blit(title, (width // 2 - title.get_width() // 2, 10))
        
        # Dessiner les gènes des nœuds
        font = pygame.font.SysFont('Arial', 16)
        nodes_title = font.render("Node Genes", True, BLACK)
        surface.blit(nodes_title, (width // 2 - nodes_title.get_width() // 2, 40))
        
        node_y = 70
        for node_id, node in self.genome.nodes.items():
            # Déterminer le type de nœud
            if node_id in self.config.genome_config.input_keys:
                node_type = "Input Layer"
            elif node_id in self.config.genome_config.output_keys:
                node_type = "Output Layer"
            else:
                node_type = "Hidden Layer"
            
            # Dessiner le cadre du nœud
            pygame.draw.rect(surface, DARK_GRAY, (20, node_y, 360, 40), 1)
            
            # Ajouter les informations du nœud
            node_text = font.render(f"Node {node_id}", True, BLACK)
            type_text = font.render(node_type, True, BLACK)
            
            surface.blit(node_text, (30, node_y + 10))
            surface.blit(type_text, (200, node_y + 10))
            
            node_y += 45
            
            # Limiter le nombre de nœuds à afficher
            if node_y > 250:
                break
        
        # Dessiner les gènes de connexion
        conn_title = font.render("Connection Genes", True, BLACK)
        surface.blit(conn_title, (width // 2 - conn_title.get_width() // 2, 280))
        
        conn_y = 310
        for i, (key, conn) in enumerate(self.genome.connections.items()):
            # Dessiner le cadre de la connexion
            pygame.draw.rect(surface, DARK_GRAY, (20, conn_y, 360, 70), 1)
            
            # Ajouter les informations de la connexion
            in_id, out_id = key
            in_text = font.render(f"In {in_id}", True, BLACK)
            out_text = font.render(f"Out {out_id}", True, BLACK)
            weight_text = font.render(f"Weight {conn.weight:.2f}", True, BLACK)
            enabled_text = font.render(f"Enabled" if conn.enabled else "Disabled", True, BLACK)
            innov_text = font.render(f"Innov {conn.innovation_number}", True, BLACK)
            
            surface.blit(in_text, (30, conn_y + 10))
            surface.blit(out_text, (30, conn_y + 30))
            surface.blit(weight_text, (150, conn_y + 10))
            surface.blit(enabled_text, (150, conn_y + 30))
            surface.blit(innov_text, (250, conn_y + 10))
            
            conn_y += 75
            
            # Limiter le nombre de connexions à afficher
            if conn_y > 550:
                break
        
        return surface
    
    def draw(self, surface, x, y):
        if self.phenotype_surface:
            surface.blit(self.phenotype_surface, (x, y))
        
        if self.genotype_surface:
            surface.blit(self.genotype_surface, (x + self.phenotype_surface.get_width() + 10, y))

# Classe pour exécuter la simulation NEAT dans le labyrinthe
class NEATMazeSimulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("NEAT Maze Solver Simulation")
        self.clock = pygame.time.Clock()
        
        self.maze = Maze(MAZE_WIDTH, MAZE_HEIGHT, CELL_SIZE)
        self.population = None
        self.generation = 0
        self.best_fitness = 0
        self.best_genome = None
        self.visualizer = None
        
        # Paramètres de la simulation
        self.run_best = False
        self.show_best = False
        self.speed = 1  # Vitesse de simulation
        self.agents = []
        
        # Charger la configuration NEAT
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, "config-neat")
        self.config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                 neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                 config_path)
        
        # Créer la population initiale
        self.population = neat.Population(self.config)
        
        # Ajouter des rapporteurs pour voir les statistiques
        self.population.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        self.population.add_reporter(stats)
        
        # Créer les boutons de l'interface
        self.buttons = []
        self.create_buttons()
    
    def create_buttons(self):
        button_width, button_height = 150, 40
        start_x, start_y = MAZE_WIDTH + 20, 20
        padding = 10
        
        # Bouton pour démarrer la simulation
        self.buttons.append({
            "rect": pygame.Rect(start_x, start_y, button_width, button_height),
            "text": "Lancer Évolution",
            "action": self.start_evolution
        })
        
        # Bouton pour afficher le meilleur
        self.buttons.append({
            "rect": pygame.Rect(start_x, start_y + button_height + padding, button_width, button_height),
            "text": "Afficher Meilleur",
            "action": self.toggle_show_best
        })
        
        # Bouton pour augmenter la vitesse
        self.buttons.append({
            "rect": pygame.Rect(start_x, start_y + 2 * (button_height + padding), button_width, button_height),
            "text": "Augmenter Vitesse",
            "action": self.increase_speed
        })
        
        # Bouton pour diminuer la vitesse
        self.buttons.append({
            "rect": pygame.Rect(start_x, start_y + 3 * (button_height + padding), button_width, button_height),
            "text": "Diminuer Vitesse",
            "action": self.decrease_speed
        })
        
        # Bouton pour générer un nouveau labyrinthe
        self.buttons.append({
            "rect": pygame.Rect(start_x, start_y + 4 * (button_height + padding), button_width, button_height),
            "text": "Nouveau Labyrinthe",
            "action": self.generate_new_maze
        })
    
    def draw_buttons(self):
        font = pygame.font.SysFont('Arial', 16)
        
        for button in self.buttons:
            # Dessiner le bouton
            pygame.draw.rect(self.screen, GRAY, button["rect"])
            pygame.draw.rect(self.screen, BLACK, button["rect"], 2)
            
            # Ajouter le texte
            text = font.render(button["text"], True, BLACK)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)
    
    def handle_button_click(self, pos):
        for button in self.buttons:
            if button["rect"].collidepoint(pos):
                button["action"]()
                break
    
    def start_evolution(self):
        self.run_best = False
        self.show_best = False
        self.generation = 0
        self.agents = []
        
        # Lancer l'évolution sur un thread séparé
        self.population.run(self.eval_genomes, 100)
    
    def toggle_show_best(self):
        self.show_best = not self.show_best
        
        # Si on vient d'activer l'affichage du meilleur, créer l'agent
        if self.show_best and self.best_genome:
            self.agents = []
            net = neat.nn.FeedForwardNetwork.create(self.best_genome, self.config)
            self.agents.append(Agent(self.maze, net))
            self.visualizer = NeatVisualizer(self.best_genome, self.config)
    
    def increase_speed(self):
        self.speed = min(self.speed * 2, 16)
    
    def decrease_speed(self):
        self.speed = max(self.speed / 2, 1)
    
    def generate_new_maze(self):
        self.maze = Maze(MAZE_WIDTH, MAZE_HEIGHT, CELL_SIZE)
        
        # Si on est en mode affichage du meilleur, mettre à jour les agents
        if self.show_best and self.best_genome:
            self.agents = []
            net = neat.nn.FeedForwardNetwork.create(self.best_genome, self.config)
            self.agents.append(Agent(self.maze, net))
    
    def eval_genomes(self, genomes, config):
        self.generation += 1
        
        # Créer les agents pour chaque génome
        self.agents = []
        for genome_id, genome in genomes:
            genome.fitness = 0
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            self.agents.append(Agent(self.maze, net))
        
        # Simuler tous les agents jusqu'à ce qu'ils soient tous morts ou aient atteint le but
        steps = 0
        while any(agent.is_alive and not agent.reached_goal for agent in self.agents) and steps < 500:
            steps += 1
            
            # Mettre à jour les agents
            for i, agent in enumerate(self.agents):
                agent.update()
                genomes[i][1].fitness = agent.fitness
            
            # Dessiner l'état actuel
            self.draw_simulation()
            
            # Ralentir la simulation si nécessaire
            for _ in range(self.speed):
                self.handle_events()
                pygame.time.delay(1)
        
        # Mettre à jour le meilleur génome
        best_genome = None
        best_fitness = 0
        for genome_id, genome in genomes:
            if genome.fitness > best_fitness:
                best_fitness = genome.fitness
                best_genome = genome
        
        if best_fitness > self.best_fitness:
            self.best_fitness = best_fitness
            self.best_genome = best_genome
            
            # Mettre à jour le visualiseur
            if self.visualizer:
                self.visualizer.genome = self.best_genome
                self.visualizer.update_surfaces()
    
    def draw_simulation(self):
        # Effacer l'écran
        self.screen.fill(WHITE)
        
        # Dessiner le labyrinthe
        self.maze.draw(self.screen)
        
        # Dessiner les agents
        if self.show_best:
            # Afficher uniquement le meilleur agent
            if self.agents:
                self.agents[0].draw(self.screen)
        else:
            # Afficher tous les agents
            for agent in self.agents:
                agent.draw(self.screen)
        
        # Dessiner les informations
        font = pygame.font.SysFont('Arial', 16)
        
        # Génération
        gen_text = font.render(f"Génération: {self.generation}", True, BLACK)
        self.screen.blit(gen_text, (MAZE_WIDTH + 20, 200))
        
        # Meilleur fitness
        fitness_text = font.render(f"Meilleur Fitness: {self.best_fitness:.2f}", True, BLACK)
        self.screen.blit(fitness_text, (MAZE_WIDTH + 20, 230))
        
        # Nombre d'agents vivants
        alive_agents = sum(1 for agent in self.agents if agent.is_alive and not agent.reached_goal)
        alive_text = font.render(f"Agents Vivants: {alive_agents}/{len(self.agents)}", True, BLACK)
        self.screen.blit(alive_text, (MAZE_WIDTH + 20, 260))
        
        # Vitesse de simulation
        speed_text = font.render(f"Vitesse: x{self.speed}", True, BLACK)
        self.screen.blit(speed_text, (MAZE_WIDTH + 20, 290))
        
        # Dessiner les boutons
        self.draw_buttons()
        
        # Dessiner le génotype et le phénotype si disponible
        if self.visualizer and self.show_best:
            self.visualizer.draw(self.screen, MAZE_WIDTH + 20, 330)
        
        # Mettre à jour l'affichage
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    self.handle_button_click(event.pos)
    
    def run(self):
        while True:
            self.handle_events()
            self.clock.tick(FPS)
            
            if self.show_best and self.agents:
                # Mettre à jour l'agent
                for _ in range(self.speed):
                    for agent in self.agents:
                        agent.update()
            
            # Dessiner l'état actuel
            self.draw_simulation()

# Point d'entrée principal
if __name__ == "__main__":
    # Créer le fichier de configuration NEAT si ce n'est pas déjà fait
    if not os.path.exists("config-neat"):
        with open("config-neat", "w") as f:
            f.write("""[NEAT]
fitness_criterion     = max
fitness_threshold     = 1000
pop_size              = 50
reset_on_extinction   = False

[DefaultGenome]
# node activation options
activation_default      = sigmoid
activation_mutate_rate  = 0.0
activation_options      = sigmoid

# node aggregation options
aggregation_default     = sum
aggregation_mutate_rate = 0.0
aggregation_options     = sum

# node bias options
bias_init_mean          = 0.0
bias_init_stdev         = 1.0
bias_max_value          = 30.0
bias_min_value          = -30.0
bias_mutate_power       = 0.5
bias_mutate_rate        = 0.7
bias_replace_rate       = 0.1

# genome compatibility options
compatibility_disjoint_coefficient = 1.0
compatibility_weight_coefficient   = 0.5

# connection add/remove rates
conn_add_prob           = 0.5
conn_delete_prob        = 0.5

# connection enable options
                    # Suite du contenu du fichier config-neat
enabled_default         = True
enabled_mutate_rate     = 0.01

feed_forward            = True
initial_connection      = full_direct

# node add/remove rates
node_add_prob           = 0.2
node_delete_prob        = 0.2

# network parameters
num_hidden              = 0
num_inputs              = 10
num_outputs             = 2

# node response options
response_init_mean      = 1.0
response_init_stdev     = 0.0
response_max_value      = 30.0
response_min_value      = -30.0
response_mutate_power   = 0.0
response_mutate_rate    = 0.0
response_replace_rate   = 0.0

# connection weight options
weight_init_mean        = 0.0
weight_init_stdev       = 1.0
weight_max_value        = 30
weight_min_value        = -30
weight_mutate_power     = 0.5
weight_mutate_rate      = 0.8
weight_replace_rate     = 0.1

[DefaultSpeciesSet]
compatibility_threshold = 3.0

[DefaultStagnation]
species_fitness_func = max
max_stagnation       = 20
species_elitism      = 2

[DefaultReproduction]
elitism            = 2
survival_threshold = 0.2
""")

    # Lancer la simulation
    simulation = NEATMazeSimulation()
    simulation.run()