# main.py

import os
import tkinter as tk
import time
import pickle
import random
import math
import importlib
from tkinter import filedialog,messagebox
from tkinter import ttk
from typing import Optional, Tuple
#import threading
#from concurrent.futures import ProcessPoolExecutor, as_completed


try:
    import config as cfg # Завантажуємо початковий конфіг
except ImportError:
    print("ERROR: config.py not found. Make sure it's in the project root.")
    exit()

from environment.maze import Maze
from environment.agent import Agent
from neat.species import Species # Потрібно для доступу до _species_counter
from neat.neat_algorithm import NeatAlgorithm
from neat.genome import Genome
from neat.nn import activate_network
from visualization.gui import MazeGUI
from visualization.network_visualizer import visualize_network

# --- Функція Оцінки (Fitness Function) ---
# (Залишаємо calculate_fitness та evaluation_function без змін, як у попередньому повідомленні)
def calculate_fitness(agent: Agent, maze: Maze, max_steps: int) -> float:
    """
    Розраховує фітнес агента на основі його стану після симуляції.
    Чим кращий результат, тим вищий фітнес.
    """
    fitness = 0.0
    base_reward = 1000.0 # Базова винагорода за досягнення

    if agent.reached_goal:
        fitness += base_reward
        # Додаємо бонус за швидкість (менше кроків = більший бонус)
        speed_bonus = (base_reward / 2.0) * (1.0 - (agent.steps_taken / max_steps))
        fitness += max(0.0, speed_bonus) # Додаємо бонус, не менше 0
    else:
        # Якщо не досяг цілі, оцінюємо за близькістю
        max_dist = math.hypot(maze.width, maze.height)
        if agent.min_dist_to_goal != float('inf') and max_dist > 0:
             proximity = 1.0 - (agent.min_dist_to_goal / max_dist)
             fitness += (base_reward / 2.0) * max(0.0, proximity)**2
        # Штраф за кроки?
        # fitness -= agent.steps_taken * 0.01 # Маленький штраф

    # Штраф за зіткнення
    if agent.collided:
        fitness *= 0.8 # Зменшуємо фітнес на 20%

    return max(0.001, fitness) # Фітнес трохи більший за 0, щоб уникнути ділення на 0 у NEAT

def evaluate_single_genome(genome_tuple: Tuple[int, Genome], config: dict) -> Tuple[int, float]:
    """
    Оцінює ОДИН геном. Приймає кортеж (id, genome) та конфіг.
    Повертає кортеж (id, fitness).
    Важливо: ця функція виконуватиметься в окремому процесі,
    тому не може напряму змінювати стан головної програми чи GUI.
    """
    genome_id, genome = genome_tuple
    if not genome:
        return genome_id, 0.001 # Мінімальний фітнес для None

    try:
        # Створюємо *нову* копію лабіринту та агента для цього процесу
        eval_maze = Maze(config['MAZE_WIDTH'], config['MAZE_HEIGHT'], config.get('MAZE_SEED'))
        if not eval_maze.start_pos:
             print(f"Error (process): Maze generation failed for genome {genome_id}")
             return genome_id, 0.001

        # Передаємо КОПІЮ конфігу на всякий випадок
        agent = Agent(genome_id, eval_maze.start_pos, config.copy())
        max_steps = config.get('MAX_STEPS_PER_EVALUATION', 500)
        colisions = 0
        for step in range(max_steps):
            if agent.reached_goal:
                break
            sensor_readings = agent.get_sensor_readings(eval_maze)
            # Важливо: передаємо копію геному, бо activate_network може його змінювати (хоча не повинна)
            network_outputs = activate_network(genome.copy(), sensor_readings)
            if network_outputs is None: # Перевірка на помилку активації
                 print(f"Error (process): activate_network failed for genome {genome_id}")
                 return genome_id, 0.001
            agent.update(eval_maze, network_outputs, dt=1)
            if(agent.collided):
                colisions += 1
            agent.steps_taken = step + 1

        # --- Розрахунок фітнесу (перенесено сюди з main.py) ---
        fitness = 0.0
        base_reward = 1000.0
        if agent.reached_goal:
            fitness += base_reward
            speed_bonus = (base_reward / 2.0) * (1.0 - (agent.steps_taken / max_steps))
            fitness += max(0.0, speed_bonus)
        else:
            max_dist = math.hypot(eval_maze.width, eval_maze.height)
            if agent.min_dist_to_goal != float('inf') and max_dist > 0:
                 proximity = 1.0 - (agent.min_dist_to_goal / max_dist)
                 fitness += (base_reward / 2.0) * max(0.0, proximity)**2
        if agent.reached_goal:
            fitness -= agent.steps_taken * 0.7 # Маленький штраф за кроки
        # if agent.velocity > 0.8:
        #     fitness *= 1.6
        # if colisions < 10:
        #     fitness *= 1.2
        if agent.collided:
            fitness *= 0.5
        if agent.velocity < 0.1:
            fitness *= 0.5
        # -------------------------------------------------------
        return genome_id, max(0.001, fitness)

    except Exception as e:
        print(f"Error evaluating genome {genome_id} in parallel process: {e}")
        import traceback
        traceback.print_exc()
        return genome_id, 0.001 # Мінімальний фітнес при помилці

def evaluation_function(genome: Genome, config: dict) -> float:
    """
    Функція, що оцінює пристосованість одного геному.
    """
    eval_maze = Maze(config['MAZE_WIDTH'], config['MAZE_HEIGHT'], config.get('MAZE_SEED'))
    if eval_maze.start_pos is None:
         print("Error: Maze generation failed, cannot evaluate.")
         return 0.0

    agent = Agent(agent_id=genome.id, start_pos=eval_maze.start_pos, config=config)
    max_steps = config.get('MAX_STEPS_PER_EVALUATION', 500)

    for step in range(max_steps):
        if agent.reached_goal:
            break

        sensor_readings = agent.get_sensor_readings(eval_maze)
        try:
            network_outputs = activate_network(genome, sensor_readings)
        except Exception as e:
            print(f"Error activating network for genome {genome.id}: {e}")
            return 0.0 # Низький фітнес при помилці

        agent.update(eval_maze, network_outputs, dt=1.0)
        # Зберігаємо фактичну кількість кроків
        agent.steps_taken = step + 1

    fitness = calculate_fitness(agent, eval_maze, max_steps)
    # Оновлюємо фітнес в геномі (може бути корисно для дебагу)
    genome.fitness = fitness
    return fitness

# --- Головний клас контролера симуляції ---

class SimulationController:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.config = self._load_config()
        self.config['NUM_PROCESSES'] = os.cpu_count()
        print(f"Using {self.config['NUM_PROCESSES']} processes for evaluation.")

        try:
            num_inputs = (
                self.config['NUM_RANGEFINDERS'] +
                self.config['NUM_RADAR_SLICES'] +
                2 +  # heading_vector (x, y)
                1    # current_velocity_reading
            )
            # --- ЗЧИТУВАННЯ ОНОВЛЕНОГО NUM_OUTPUTS ---
            num_outputs = self.config['NUM_OUTPUTS'] # Зчитає 4 з конфігу
            # ------------------------------------------
            print(f"Network configuration: {num_inputs} Inputs, {num_outputs} Outputs") # Debug
        except KeyError as e:
             print(f"FATAL ERROR: Missing configuration key needed for NN setup: {e}")
             master.quit()
             return

        self.config['NUM_INPUTS'] = num_inputs
        # Передаємо 0 для initial_genome_id_start, бо NeatAlgorithm сам керує лічильником
        self.neat = NeatAlgorithm(self.config, num_inputs, num_outputs, initial_genome_id_start=0)
        # self.config['num_outputs'] = num_outputs # Вже завантажено

        # Ініціалізація компонентів
        #self.neat = NeatAlgorithm(self.config, num_inputs, num_outputs) # Передаємо обчислені значення
        self.maze = Maze(self.config['MAZE_WIDTH'], self.config['MAZE_HEIGHT'], self.config.get('MAZE_SEED'))
        self.config['MAZE_SEED'] = self.maze.seed # Зберігаємо фактичний сід в конфіг
        self.agents = {} # Словник {genome_id: Agent}

        # Ініціалізація GUI
        self.gui = MazeGUI(master, self.config, self)

        # Стан для керування виконанням багатьох поколінь
        self._is_running_multiple = False
        self._stop_multiple_requested = False
        # Стан симуляції
        self.is_running = False
        self.current_simulation_step = 0
        self.max_steps_per_gen_vis = self.config.get('MAX_STEPS_PER_EVALUATION', 500)

        # Ініціалізація відображення
        self._redraw_maze()
        self._update_gui_stats()

    def _load_config(self) -> dict:
        """Завантажує конфігурацію з config.py."""
        try:
            importlib.reload(cfg)
            config_dict = {key: getattr(cfg, key) for key in dir(cfg) if not key.startswith('_')}
        except Exception as e:
             print(f"ERROR loading config.py: {e}")
             # Повертаємо порожній словник або значення за замовчуванням
             return {}

        # Встановлення значень за замовчуванням для КРИТИЧНИХ параметрів, якщо їх немає
        config_dict.setdefault('POPULATION_SIZE', 150)
        config_dict.setdefault('MAZE_WIDTH', 21)
        config_dict.setdefault('MAZE_HEIGHT', 15)
        config_dict.setdefault('NUM_RANGEFINDERS', 8)
        config_dict.setdefault('NUM_RADAR_SLICES', 8)
        config_dict.setdefault('NUM_OUTPUTS', 7) # Важливо для ініціалізації
        # ... додати інші ...
        return config_dict

    # --- Решта методів класу SimulationController залишаються без змін ---
    # _redraw_maze, _reset_agents_for_visualization, _update_agents_visuals,
    # _update_gui_stats, toggle_simulation, simulation_step, run_one_generation,
    # generate_new_maze, reset_simulation

    def _redraw_maze(self):
        """Перемальовує лабіринт на GUI."""
        self.gui.draw_maze(self.maze.grid, self.config.get('CELL_SIZE_PX', 20))

    def _reset_agents_for_visualization(self):
        """Скидає агентів для візуалізації на основі поточної популяції NEAT."""
        self.agents.clear()
        self.gui.clear_all_agents()
        # --- DEBUG ---
        pop_size = len(self.neat.population) if self.neat and self.neat.population else 0
        print(f"Resetting agents for visualization. Population size: {pop_size}")
        # -------------
        if not self.neat.population: return

        for genome in self.neat.population:
             if self.maze.start_pos:
                 # Перевіряємо, чи genome не None
                 if genome:
                     self.agents[genome.id] = Agent(genome.id, self.maze.start_pos, self.config)
                 else:
                     print("Warning: Found None genome while resetting agents.")
             else:
                  print("Error: Cannot reset agents, maze has no start position.")
        # --- DEBUG ---
        print(f"Agents created for visualization: {len(self.agents)}")
        # -------------

    def _update_agents_visuals(self):
         """Оновлює позиції всіх агентів на GUI."""
         best_gen_genome_id = None
         if self.neat.population:
             current_best_gen = max(self.neat.population, key=lambda g: g.fitness if g else -float('inf'), default=None) # Додав перевірку на None
             if current_best_gen: best_gen_genome_id = current_best_gen.id

         best_overall_genome_id = self.neat.best_genome_overall.id if self.neat.best_genome_overall else None

         self.gui.clear_all_agents() 
         
         # Отримуємо стан чекбокса з GUI
         show_sensors_flag = self.gui.show_sensors_var.get() if hasattr(self.gui, 'show_sensors_var') else False

         agents_to_draw = list(self.agents.keys())
         for agent_id in agents_to_draw:
             agent = self.agents.get(agent_id)
             if agent:
                 is_best_gen = (agent_id == best_gen_genome_id)
                 is_best_overall = (agent_id == best_overall_genome_id)
                 self.gui.update_agent_visual(
                     agent.id, agent.x, agent.y, agent.angle,
                     is_best_gen=is_best_gen, is_best_overall=is_best_overall,
                     show_sensors=show_sensors_flag # Передаємо стан чекбокса
                 )
         # --- DEBUG ---
         # print(f"Updated visuals for {len(self.agents)} agents.")
         # -------------
    def get_genome_by_id(self, genome_id: int) -> Optional[Genome]:
        """Шукає геном за ID у поточній популяції."""
        if not self.neat or not self.neat.population:
            return None
        for genome in self.neat.population:
            # Геноми можуть мати рядкові ID після кросоверу, порівнюємо обережно
            if str(genome.id) == str(genome_id):
                return genome
        # Можливо, перевіряємо і найкращий загальний
        if self.neat.best_genome_overall and str(self.neat.best_genome_overall.id) == str(genome_id):
             return self.neat.best_genome_overall
        return None 
    
    def _update_gui_stats(self):
         """Отримує статистику та передає в GUI для безпечного оновлення."""
         if not hasattr(self, 'neat'): return # Якщо neat ще не створено

         stats = {
             "generation": self.neat.generation,
             "num_species": len(self.neat.species),
             "max_fitness": None,
             "average_fitness": None,
             "best_overall_fitness": None,
             "best_genome_current_gen": None,
             "best_genome_overall": self.neat.best_genome_overall
         }
         current_best_genome = None
         if self.neat.population:
             valid_genomes = [g for g in self.neat.population if g is not None]
             if valid_genomes:
                  current_best_genome = max(valid_genomes, key=lambda g: g.fitness, default=None)
                  if current_best_genome:
                       stats["max_fitness"] = current_best_genome.fitness
                  total_fitness = sum(g.fitness for g in valid_genomes)
                  stats["average_fitness"] = total_fitness / len(valid_genomes) if valid_genomes else 0.0
                  stats["best_genome_current_gen"] = current_best_genome

         if self.neat.best_genome_overall:
             stats["best_overall_fitness"] = self.neat.best_genome_overall.fitness

         # Викликаємо безпечне оновлення GUI
         self.gui.update_gui_from_thread(stats)

    def toggle_simulation(self, run: bool):
        """Запускає або ставить на паузу ВІЗУАЛІЗАЦІЮ."""
        if self._is_running_multiple:
            print("Cannot start visualization while batch run is active.")
            return
        # --- Логіка візуалізації (simulation_step) без змін ---
        self.gui.is_running = run # Оновлюємо стан в GUI
        # print(f"Visualization {'Started' if run else 'Paused'}")
        if run:
            self.current_simulation_step = 0
            if not self.agents: # Створюємо агентів, якщо їх немає
                self._reset_agents_for_visualization()
            if self.agents: # Запускаємо, тільки якщо є агенти
                 self.master.after(50, self.simulation_step)
            else: # Якщо агентів немає, одразу зупиняємо
                 self.gui.is_running = False
                 self.gui.set_controls_state(running=False, running_multiple=False)
        # Зупинка відбувається автоматично, коли self.gui.is_running стає False
                 
    def simulation_step(self):
        """Виконує один крок симуляції для візуалізації."""
        if not self.gui.is_running or self._is_running_multiple:
            self.gui.set_controls_state(running=False, running_multiple=self._is_running_multiple)
            return

        start_time = time.time()

        active_agents = 0
        genomes_map = {genome.id: genome for genome in self.neat.population if genome}
        agents_to_remove = [] # Зберігаємо ID агентів для видалення

        agents_alive_this_step = list(self.agents.items()) # Копіюємо перед ітерацією

        for agent_id, agent in agents_alive_this_step:
            if agent_id not in self.agents: continue

            if agent.reached_goal or self.current_simulation_step >= self.max_steps_per_gen_vis:
                agents_to_remove.append(agent_id)
                continue

            active_agents += 1
            genome = genomes_map.get(agent_id)
            if not genome:
                # print(f"Warning: Genome for agent {agent_id} not found during visualization step.")
                agents_to_remove.append(agent_id)
                continue

            # Отримуємо сенсорні дані
            sensor_readings = agent.get_sensor_readings(self.maze) 
            if not isinstance(sensor_readings, list): # Додаткова перевірка
                print(f"ERROR: agent.get_sensor_readings for agent {agent_id} returned {type(sensor_readings)}, expected list.")
                agents_to_remove.append(agent_id)
                continue

            # --- Блок ДІАГНОСТИКИ ---
            network_outputs = None # Ініціалізуємо як None
            try:
                # Викликаємо активацію
                network_outputs = activate_network(genome, sensor_readings)

                # !!! Перевіряємо результат ПЕРЕД викликом update !!!
                if network_outputs is None:
                    print(f"FATAL ERROR: activate_network for genome {genome.id} returned None!")
                    # Можна тут додати детальніший дебаг геному/входів, якщо потрібно
                    # print(f"    Genome: {genome}")
                    # print(f"    Inputs: {sensor_readings}")
                    raise TypeError("activate_network returned None unexpectedly.") # Генеруємо помилку явно

                if not isinstance(network_outputs, list):
                     print(f"FATAL ERROR: activate_network for genome {genome.id} returned {type(network_outputs)}, expected list!")
                     raise TypeError("activate_network did not return a list.")

                # Якщо перевірки пройдені, викликаємо update
                agent.update(self.maze, network_outputs, dt=1)

            except Exception as e:
                # Ловимо помилку або з activate_network, або з agent.update
                print(f"Error updating agent {agent_id} with genome {genome.id}: {e}")
                # Додатковий дебаг: що було в network_outputs під час помилки?
                # print(f"    network_outputs was: {network_outputs} (type: {type(network_outputs)})")
                # traceback.print_exc() # Розкоментуйте для повного стеку викликів
                agents_to_remove.append(agent_id)
            # --- Кінець блоку ДІАГНОСТИКИ ---

        # Видаляємо агентів, що завершили
        for agent_id in agents_to_remove:
             if agent_id in self.agents:
                 del self.agents[agent_id]
             # self.gui.remove_agent_visual(agent_id) # Видаляти не треба, бо наступний _update_agents_visuals їх не оновить

        # Оновлюємо GUI
        self._update_agents_visuals() # Перемальовуємо всіх активних
        self.gui.update_gui()

        self.current_simulation_step += 1

        # Перевірка умов зупинки візуалізації
        if not self.agents or self.current_simulation_step >= self.max_steps_per_gen_vis:
             # print(f"Visualization step limit reached ({self.current_simulation_step}) or no active agents left.")
             self.gui.is_running = False
             self.gui.set_controls_state(running=False, running_multiple=False)
             return

        # Плануємо наступний крок візуалізації
        elapsed = time.time() - start_time
        delay = max(1, 30 - int(elapsed * 1000))
        self.master.after(delay, self.simulation_step)


    def run_one_generation(self):
        """Запускає ОДИН повний цикл покоління NEAT з паралельною оцінкою."""
        if self._is_running_multiple: # Не запускаємо вручну, якщо йде batch run
            print("Cannot run single generation while multiple generations are running.")
            return

        print(f"\n--- Running Generation {self.neat.generation + 1} ---")
        start_time = time.time()

        # Викликаємо метод NEAT, передаючи ГЛОБАЛЬНУ функцію оцінки
        # Ця функція тепер буде використовувати ProcessPoolExecutor
        stats = self.neat.run_generation(evaluate_single_genome)

        end_time = time.time()
        gen_num = stats.get('generation', '?')
        max_fit = stats.get('max_fitness', float('nan'))
        avg_fit = stats.get('average_fitness', float('nan'))
        num_sp = stats.get('num_species', '?')

        print(f"Generation {gen_num} finished in {end_time - start_time:.2f} seconds.")
        print(f"Stats: MaxFit={max_fit:.4f}, AvgFit={avg_fit:.4f}, Species={num_sp}")

        # Оновлюємо GUI зібраною статистикою
        self._update_gui_stats()
        # Скидаємо агентів для візуалізації на основі НОВОЇ популяції
        self._reset_agents_for_visualization()
        self._update_agents_visuals()
        self.gui.update_gui()

    def run_multiple_generations(self, num_generations: int):
        """Запускає вказану кількість поколінь NEAT у фоновому потоці."""
        print(f"Starting batch run for {num_generations} generations...")
        self._is_running_multiple = True
        self._stop_multiple_requested = False

        start_gen = self.neat.generation + 1
        end_gen = start_gen + num_generations

        try:
            for gen in range(start_gen, end_gen):
                 if self._stop_multiple_requested:
                     print("Batch run interrupted by user.")
                     break

                 print(f"\n--- Running Generation {gen} (Batch) ---")
                 start_time_gen = time.time()

                 # Викликаємо основний метод run_generation з NeatAlgorithm
                 stats = self.neat.run_generation(evaluate_single_genome) # Використовуємо глобальну функцію

                 end_time_gen = time.time()
                 max_fit = stats.get('max_fitness', float('nan'))
                 avg_fit = stats.get('average_fitness', float('nan'))
                 num_sp = stats.get('num_species', '?')

                 print(f"Generation {gen} finished in {end_time_gen - start_time_gen:.2f} sec. MaxFit={max_fit:.4f}, AvgFit={avg_fit:.4f}, Sp={num_sp}")

                 # Оновлюємо GUI через безпечний метод
                 self._update_gui_stats() # Передаємо статистику в головний потік

                 # Невелике очікування, щоб GUI встиг оновитись (опціонально)
                 # time.sleep(0.01)

        except Exception as e:
            print(f"\n--- ERROR during batch run at generation {self.neat.generation} ---")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Batch Run Error", f"An error occurred:\n{e}")
        finally:
            print("Batch run finished.")
            self._is_running_multiple = False
            self._stop_multiple_requested = False
            # Розблоковуємо кнопки керування через головний потік GUI
            self.master.after(0, self.gui.set_controls_state, False, False)
             # Оновлюємо візуалізацію для кінцевого стану
            self.master.after(0, self._reset_agents_for_visualization)
            self.master.after(0, self._update_agents_visuals)


    def generate_new_maze(self, seed=None) -> int | None:
        """Генерує новий лабіринт і оновлює GUI."""
        print(f"Generating new maze with seed: {seed}")
        self.config['MAZE_SEED'] = seed # Зберігаємо бажаний сід
        try:
              # --- Перевірка розмірів перед генерацією ---
             w = self.config['MAZE_WIDTH']
             h = self.config['MAZE_HEIGHT']
             if w % 2 == 0: w += 1; print(f"Adjusted MAZE_WIDTH to {w} (must be odd)")
             if h % 2 == 0: h += 1; print(f"Adjusted MAZE_HEIGHT to {h} (must be odd)")
             w = max(5, w); h = max(5, h)
             self.config['MAZE_WIDTH'] = w
             self.config['MAZE_HEIGHT'] = h
             # ------------------------------------------
             self.maze = Maze(w, h, seed)
             self.config['MAZE_SEED'] = self.maze.seed
             self._redraw_maze()
             self._reset_agents_for_visualization() # Важливо після нової сітки
             self._update_agents_visuals()
             self.gui.update_gui()
             return self.maze.seed
        except ValueError as e:
             messagebox.showerror("Maze Generation Error", f"Failed to generate maze: {e}\nCheck MAZE_WIDTH/MAZE_HEIGHT in config (must be odd >= 5).")
             return self.config.get('MAZE_SEED') # Повертаємо старий сід

    def save_simulation(self):
        if self._is_running_multiple: # Перевірка, чи не запущений пакетний прогін
            messagebox.showwarning("Saving Denied", "Cannot save state while multiple generations are running. Please wait for completion or stop the batch process.")
            return

        if not self.neat:
            messagebox.showerror("Error", "NEAT algorithm not initialized.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".neat_save",
            filetypes=[("NEAT Save Files", "*.neat_save"), ("All Files", "*.*")],
            title="Save NEAT Simulation State"
        )
        if not filepath:
            return

        try:
            neat_state_data = self.neat.get_state_data()
            
            simulation_data = {
                'version': "1.0", # Додаємо версію для майбутньої сумісності
                'config': self.config.copy(),
                'maze_seed': self.maze.seed, # Актуальний сід використаного лабіринту
                'neat_algorithm_state': neat_state_data,
                'num_inputs_for_neat': self.neat.num_inputs,
                'num_outputs_for_neat': self.neat.num_outputs
            }

            with open(filepath, 'wb') as f:
                pickle.dump(simulation_data, f)
            messagebox.showinfo("Success", f"Simulation state saved to {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save simulation state:\n{e}")
            print(f"Error saving simulation: {e}")
            import traceback
            traceback.print_exc()

    def load_simulation(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".neat_save",
            filetypes=[("NEAT Save Files", "*.neat_save"), ("All Files", "*.*")],
            title="Load NEAT Simulation State"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'rb') as f:
                simulation_data = pickle.load(f)

            save_version = simulation_data.get('version', 'unknown')
            print(f"Loading save file version: {save_version}")
            # Тут можна додати перевірку версій

            loaded_config = simulation_data.get('config')
            if loaded_config:
                # Оновлюємо поточний конфіг, але зберігаємо деякі runtime налаштування
                num_processes_current = self.config.get('NUM_PROCESSES')
                self.config.update(loaded_config)
                self.config['NUM_PROCESSES'] = num_processes_current # Відновлюємо, бо це залежить від машини
                self.gui.seed_var.set(str(self.config.get('MAZE_SEED', '')))
            else:
                print("Warning: No config found in save file. Using current config.")

            maze_seed = simulation_data.get('maze_seed', self.config.get('MAZE_SEED'))
            # Перевіряємо та виправляємо розміри лабіринту з конфігу перед генерацією
            w = self.config.get('MAZE_WIDTH', 11)
            h = self.config.get('MAZE_HEIGHT', 11)
            if w % 2 == 0: w += 1
            if h % 2 == 0: h += 1
            w = max(5, w); h = max(5, h)
            self.config['MAZE_WIDTH'] = w
            self.config['MAZE_HEIGHT'] = h
            self.maze = Maze(w, h, maze_seed) # Генеруємо лабіринт
            self.config['MAZE_SEED'] = self.maze.seed # Зберігаємо фактичний сід
            self._redraw_maze()


            neat_state_data = simulation_data.get('neat_algorithm_state')
            # Беремо num_inputs/outputs зі збереженого файлу, якщо є, інакше з поточного конфігу
            num_inputs = simulation_data.get('num_inputs_for_neat', self.config['NUM_INPUTS'])
            num_outputs = simulation_data.get('num_outputs_for_neat', self.config['NUM_OUTPUTS'])
            self.config['NUM_INPUTS'] = num_inputs # Оновлюємо конфіг, якщо значення змінились
            self.config['NUM_OUTPUTS'] = num_outputs


            if neat_state_data:
                # Передаємо оновлений self.config
                self.neat = NeatAlgorithm.load_from_state_data(neat_state_data, self.config, num_inputs, num_outputs)
            else:
                messagebox.showerror("Load Error", "NEAT algorithm data not found in save file.")
                return
            
            self._update_gui_stats()
            self._reset_agents_for_visualization()
            self._update_agents_visuals()
            self.gui.set_controls_state(running=False, running_multiple=False)
            self.gui.update_gui()

            messagebox.showinfo("Success", f"Simulation state loaded from {os.path.basename(filepath)}")
            print(f"Simulation loaded. Current generation: {self.neat.generation}")

        except FileNotFoundError:
            messagebox.showerror("Load Error", f"Save file not found: {filepath}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load simulation state:\n{e}")
            print(f"Error loading simulation: {e}")
            import traceback
            traceback.print_exc()
    def reset_simulation(self):
        """Скидає симуляцію NEAT до початкового стану."""
        print("Resetting NEAT simulation...")
        try:
            self.config = self._load_config()
            self.config['NUM_PROCESSES'] = os.cpu_count() # Оновлюємо к-сть процесів
            num_inputs = (self.config['NUM_RANGEFINDERS'] + self.config['NUM_RADAR_SLICES'] + 2 + 1)
            num_outputs = self.config['NUM_OUTPUTS']
            self.config['NUM_INPUTS'] = num_inputs

            self.neat = NeatAlgorithm(self.config, num_inputs, num_outputs) # Новий NEAT
            new_seed = self.generate_new_maze(self.config.get('MAZE_SEED')) # Новий лабіринт

            self._update_gui_stats() # Оновлюємо статистику та візуалізацію мережі
            # _reset_agents_for_visualization() та _update_agents_visuals() викликаються в generate_new_maze
            self.gui.update_gui()
            print("Simulation reset complete.")
        except Exception as e:
            print(f"FATAL ERROR during reset: {e}")
            messagebox.showerror("Reset Error", f"Could not reset simulation: {e}")



# --- Точка входу ---
if __name__ == "__main__":
    # ВАЖЛИВО для ProcessPoolExecutor на Windows
    import multiprocessing
    multiprocessing.freeze_support() # Потрібно викликати перед створенням вікна

    root = tk.Tk()
    try:
        controller = SimulationController(root)
        root.mainloop()
    except Exception as e:
        # ... (обробка помилок як раніше) ...
        print(f"\n--- Unhandled Exception ---")
        import traceback
        traceback.print_exc()
        print(f"---------------------------\n")
        try:
             messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{e}\n\nCheck console output.")
        except: pass