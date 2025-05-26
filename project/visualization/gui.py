# visualization/gui.py

import math
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, Menu
from PIL import Image, ImageTk, ImageDraw
from typing import Optional, TYPE_CHECKING
import pandas as pd  # Для _plot_complexity_analysis
from neat.json_serializer import NEATJSONSerializer  # Для _export_current_data
from neat.data_analyzer import NEATDataAnalyzer 
import threading
# --- Імпорт для type hinting без циклічних залежностей ---
if TYPE_CHECKING:
    from project.neat.genome import Genome
    from project.main import SimulationController

# --- Імпортуємо візуалізатор та константи ---
try:
    from .network_visualizer import visualize_network
except ImportError:
    print("Warning: Could not import visualize_network from network_visualizer.")
    # Функція-заглушка
    # def visualize_network(genome: 'Genome') -> Optional[Image.Image]: # Removed width/height
    #     try:
    #         img = Image.new("RGB", (300, 200), "lightgray")
    #         d = ImageDraw.Draw(img)
    #         d.text((5,5), "Viz Error", fill="red")
    #         return img
    #     except:
    #         return None
    pass

try:
    import os
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from environment.maze import CELL_WALL, CELL_PATH, CELL_START, CELL_GOAL
except ImportError:
    print("Warning: Could not import constants from environment.maze. Using default values.")
    CELL_PATH, CELL_WALL, CELL_START, CELL_GOAL = 0, 1, 2, 3

# --- Константи для кольорів ---
COLOR_WALL = "black"
COLOR_PATH = "white"
COLOR_START = "lightgreen"
COLOR_GOAL = "red"
COLOR_AGENT_DEFAULT = "blue"
COLOR_AGENT_BEST = "yellow"
COLOR_AGENT_OVERALL_BEST = "purple"
COLOR_INFO_BG = "lightgrey"
COLOR_MAZE_OUTLINE = "#CCCCCC"
COLOR_BACKGROUND = "#282c34" # Темно-сірий фон

COLOR_RANGEFINDER_RAY = "rgba(255, 255, 50, 0.3)" # Напівпрозорий жовтий
COLOR_RANGEFINDER_HIT = "rgba(255, 165, 50, 0.6)" # Напівпрозорий оранжевий для точки зіткнення

class PlotWindow(tk.Toplevel):
    """Окреме вікно для відображення графіка."""
    def __init__(self, master, title="Plot"):
        super().__init__(master)
        self.title(title)
        # self.geometry("800x600") # Можна задати розмір

        self.figure = plt.Figure(figsize=(8, 6), dpi=100) # Створюємо фігуру matplotlib
        self.canvas = FigureCanvasTkAgg(self.figure, self) # Вбудовуємо в Tkinter
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # self.protocol("WM_DELETE_WINDOW", self.on_close) # Обробка закриття

    def plot_data(self, x_data, y_data, plot_title, x_label, y_label, line_label="Data"):
        """Малює дані на графіку."""
        self.figure.clear() # Очищаємо попередній графік
        ax = self.figure.add_subplot(111)
        ax.plot(x_data, y_data, label=line_label)
        ax.set_title(plot_title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        if len(x_data) > 1 or len(y_data) > 1: # Показуємо легенду, якщо є дані
            ax.legend()
        ax.grid(True)
        self.canvas.draw()

    def on_close(self):
        plt.close(self.figure) # Важливо закрити фігуру matplotlib
        self.destroy()

class MazeGUI:
    """Клас для графічного інтерфейсу симуляції NEAT у лабіринті."""

    def __init__(self, master: tk.Tk, config: dict, main_controller: 'SimulationController'):
        """
        Ініціалізація GUI.
        """
        self.master = master
        self.main_controller = main_controller
        self.config = config
        self.master.title("NEAT Maze Navigation")

        self._cell_size = config.get('CELL_SIZE_PX', 20)
        maze_width_px = config.get('MAZE_WIDTH', 21) * self._cell_size
        maze_height_px = config.get('MAZE_HEIGHT', 15) * self._cell_size
        info_panel_width = config.get('INFO_PANEL_WIDTH_PX', 300)


        self.is_running = False
        self.genome_to_display_id = None

        # --- Основні фрейми ---
        self.maze_frame = tk.Frame(master, bd=1, relief=tk.SUNKEN)
        self.maze_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.control_frame = tk.Frame(master, width=info_panel_width, bg=COLOR_INFO_BG, bd=1, relief=tk.RAISED)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.control_frame.pack_propagate(False)

        # --- Канвас для лабіринту ---
        self.maze_canvas = tk.Canvas(self.maze_frame, bg=COLOR_PATH,
                                     width=maze_width_px, height=maze_height_px,
                                     scrollregion=(0, 0, maze_width_px, maze_height_px))
        self.maze_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Словник для зберігання тегів агентів
        self.agent_tags = {}
        self.network_photo = None # Tkinter PhotoImage
        self._current_network_pil_image: Optional[Image.Image] = None # Оригінал PIL
        # --- Атрибути для зуму та панорамування мережі ---
        self._network_zoom = 1.0
        self._network_offset_x = 0.0 # Зсув зображення по X на канвасі
        self._network_offset_y = 0.0 # Зсув зображення по Y на канвасі
        self._network_canvas_width = 1 # Поточна ширина канвасу
        self._network_canvas_height = 1 # Поточна висота канвасу
        self._network_drag_start_x = 0
        self._network_drag_start_y = 0
        # --- Віджети на панелі керування ---
        self._create_control_widgets(self.control_frame)
        # Одразу оновимо візуалізацію мережі при старті
        self.update_network_visualization()
        self._create_menubar() # Створюємо меню

    def _create_menubar(self):
        """Створює головне меню програми (тулбар)."""
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        # --- Меню "File" ---
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="Save State (JSON)", 
                            command=lambda: self.main_controller.save_simulation() if self.main_controller else None)
        file_menu.add_command(label="Load State", 
                            command=lambda: self.main_controller.load_simulation() if self.main_controller else None)
        file_menu.add_separator()
        file_menu.add_command(label="Export Current Data to CSV", command=self._export_current_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

        # --- Меню "Plots" ---
        plots_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plots", menu=plots_menu)

        plots_menu.add_command(label="Average Fitness per Generation",
                            command=self._plot_avg_fitness)
        plots_menu.add_command(label="Max Fitness per Generation",
                            command=self._plot_max_fitness)
        plots_menu.add_command(label="Species Diversity",
                            command=self._plot_species_diversity)
        plots_menu.add_separator()
        plots_menu.add_command(label="Complexity Analysis",
                            command=self._plot_complexity_analysis)
        
        # --- Меню "Analysis" ---
        analysis_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        
        analysis_menu.add_command(label="Load & Analyze JSON File",
                                command=self._analyze_json_file)
        analysis_menu.add_command(label="Compare Two Runs",
                                command=self._compare_runs)

    def _plot_species_diversity(self):
        """Відображає графік кількості видів."""
        stats = self._get_plot_data()
        if not stats:
            messagebox.showinfo("No Data", "No generation data available to plot.")
            return

        generations = [s['generation'] for s in stats]
        num_species = [s.get('num_species', 0) for s in stats]

        plot_win = PlotWindow(self.master, title="Species Diversity")
        
        # Використовуємо matplotlib напряму для кращого контролю
        plot_win.figure.clear()
        ax = plot_win.figure.add_subplot(111)
        ax.plot(generations, num_species, label='Number of Species', linewidth=2, color='green')
        ax.fill_between(generations, num_species, alpha=0.3, color='green')
        ax.set_xlabel('Generation')
        ax.set_ylabel('Number of Species')
        ax.set_title('Species Diversity Over Generations')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plot_win.canvas.draw()

    def _plot_complexity_analysis(self):
        """Аналізує складність мереж у поточному запуску."""
        if not self.main_controller or not self.main_controller.neat:
            messagebox.showerror("Error", "No active simulation.")
            return
        
        # Збираємо дані про складність
        complexity_data = []
        for genome in self.main_controller.neat.population:
            if genome:
                num_nodes = len(genome.nodes)
                num_connections = sum(1 for c in genome.connections.values() if c.enabled)
                complexity_data.append({
                    'nodes': num_nodes,
                    'connections': num_connections,
                    'fitness': genome.fitness
                })
        
        if not complexity_data:
            messagebox.showinfo("No Data", "No genome data available.")
            return
        
        # Створюємо графік
        plot_win = PlotWindow(self.master, title="Network Complexity Analysis")
        plot_win.figure.clear()
        
        nodes = [d['nodes'] for d in complexity_data]
        connections = [d['connections'] for d in complexity_data]
        fitness = [d['fitness'] for d in complexity_data]
        
        ax = plot_win.figure.add_subplot(111)
        scatter = ax.scatter(nodes, connections, c=fitness, cmap='viridis', s=50, alpha=0.6)
        ax.set_xlabel('Number of Nodes')
        ax.set_ylabel('Number of Active Connections')
        ax.set_title('Network Complexity (Current Generation)')
        
        # Додаємо colorbar
        cbar = plot_win.figure.colorbar(scatter, ax=ax)
        cbar.set_label('Fitness')
        
        plot_win.canvas.draw()
    def _export_current_data(self):
        """Експортує поточні дані тренування в JSON."""
        if not self.main_controller or not self.main_controller.neat:
            messagebox.showerror("Error", "No active simulation to export.")
            return
        
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Export Training Data"
        )
        
        if filepath:
            try:
                from neat.json_serializer import NEATJSONSerializer
                NEATJSONSerializer.save_neat_state(
                    filepath, 
                    self.main_controller.neat, 
                    self.main_controller.config.copy()
                )
                messagebox.showinfo("Success", f"Data exported to {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data:\n{e}")

    def _analyze_json_file(self):
        """Завантажує та аналізує JSON файл."""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Select JSON File to Analyze"
        )
        
        if not filepath:
            return
        
        try:
            from neat.data_analyzer import NEATDataAnalyzer
            analyzer = NEATDataAnalyzer(filepath)
            
            # Створюємо нове вікно для відображення аналізу
            analysis_window = tk.Toplevel(self.master)
            analysis_window.title(f"Analysis: {os.path.basename(filepath)}")
            analysis_window.geometry("600x400")
            
            # Текстове поле для виводу інформації
            text_widget = tk.Text(analysis_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Виводимо базову інформацію
            info = analyzer.get_basic_info()
            text_widget.insert(tk.END, "=== Basic Information ===\n")
            for key, value in info.items():
                text_widget.insert(tk.END, f"{key}: {value}\n")
            
            # Статистика фітнесу
            df = analyzer.get_fitness_statistics()
            if not df.empty:
                text_widget.insert(tk.END, "\n=== Fitness Statistics ===\n")
                text_widget.insert(tk.END, f"Final Max Fitness: {df['max_fitness'].iloc[-1]:.4f}\n")
                text_widget.insert(tk.END, f"Average Max Fitness: {df['max_fitness'].mean():.4f}\n")
                text_widget.insert(tk.END, f"Fitness Improvement: {df['max_fitness'].iloc[-1] - df['max_fitness'].iloc[0]:.4f}\n")
            
            # Кнопки для графіків
            button_frame = ttk.Frame(analysis_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(button_frame, text="Show Fitness Plot",
                    command=lambda: analyzer.plot_fitness_over_time()).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Show Species Plot", 
                    command=lambda: analyzer.plot_species_diversity()).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Show Complexity Plot",
                    command=lambda: analyzer.plot_complexity_vs_fitness()).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to analyze file:\n{e}")

    def _compare_runs(self):
        """Порівнює два запуски NEAT."""
        from tkinter import filedialog
        from neat.data_analyzer import NEATDataAnalyzer
        
        # Вибираємо перший файл
        file1 = filedialog.askopenfilename(
            title="Select First JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file1:
            return
        
        # Вибираємо другий файл
        file2 = filedialog.askopenfilename(
            title="Select Second JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not file2:
            return
        
        try:
            analyzer1 = NEATDataAnalyzer(file1)
            analyzer2 = NEATDataAnalyzer(file2)
            
            # Імена файлів для міток
            label1 = os.path.basename(file1).replace('.json', '')
            label2 = os.path.basename(file2).replace('.json', '')
            
            analyzer1.compare_runs(analyzer2, labels=(label1, label2))
        except Exception as e:
            messagebox.showerror("Comparison Error", f"Failed to compare files:\n{e}")
    def _get_plot_data(self) -> list:
        """Отримує дані для графіків з SimulationController."""
        if self.main_controller and hasattr(self.main_controller.neat, 'generation_statistics'):
            return self.main_controller.neat.generation_statistics
        return []

    def _plot_avg_fitness(self):
        """Відображає графік середнього фітнесу."""
        stats = self._get_plot_data()
        if not stats:
            messagebox.showinfo("No Data", "No generation data available to plot.")
            return

        generations = [s['generation'] for s in stats]
        avg_fitness = [s.get('average_fitness', 0) if s.get('average_fitness') is not None else 0 for s in stats] # Додав .get та обробку None

        plot_win = PlotWindow(self.master, title="Average Fitness per Generation")
        plot_win.plot_data(generations, avg_fitness,
                            "Average Fitness Over Generations",
                            "Generation", "Average Fitness",
                            line_label="Avg Fitness")

    def _plot_max_fitness(self):
        """Відображає графік максимального фітнесу."""
        stats = self._get_plot_data()
        if not stats:
            messagebox.showinfo("No Data", "No generation data available to plot.")
            return

        generations = [s['generation'] for s in stats]
        max_fitness = [s.get('max_fitness', 0) if s.get('max_fitness') is not None else 0 for s in stats] # Додав .get та обробку None

        plot_win = PlotWindow(self.master, title="Max Fitness per Generation")
        plot_win.plot_data(generations, max_fitness,
                            "Maximum Fitness Over Generations",
                            "Generation", "Max Fitness",
                            line_label="Max Fitness")
        
    def _draw_rangefinder_rays(self, agent_id: int):
        """Малює промені rangefinder для конкретного агента."""
        agent = self.main_controller.agents.get(agent_id)
        if not agent or not hasattr(agent, 'last_rangefinder_rays'):
            return

        tag_rays = f"agent_{agent_id}_rays"
        self.maze_canvas.delete(tag_rays) # Видаляємо старі промені цього агента

        cell_s = self._cell_size
        # Колір променя - можна зробити залежним від відстані, але поки що фіксований
        # ray_color = "#FFFF99" # Світло-жовтий
        ray_color_str = "yellow" # Tkinter не підтримує rgba напряму для create_line, але ми можемо емулювати
                               # через stipple або використовувати спеціальні бібліотеки.
                               # Для простоти, зробимо їх тоншими і менш яскравими.
        hit_point_radius = max(1, int(cell_s * 0.05)) # Маленький радіус для точки зіткнення

        for sx, sy, ex, ey, actual_dist in agent.last_rangefinder_rays:
            # Переводимо координати лабіринту в координати канвасу
            sx_px, sy_px = sx * cell_s, sy * cell_s
            ex_px, ey_px = ex * cell_s, ey * cell_s
            
            # Малюємо лінію променя
            # Для напівпрозорості можна спробувати stipple або просто тоншу лінію
            # Tkinter не має прямої підтримки alpha-каналу для ліній.
            # Як варіант, можна малювати кілька ліній різної товщини/кольору.
            # Або використовувати бібліотеку, що розширює Tkinter, наприклад, tkextrafont, cairo.
            # Для простоти зараз:
            line_width = 1 # Тонка лінія
            line_color = "yellow"
            if actual_dist < agent.rangefinder_max_dist - 0.1: # Якщо промінь щось зачепив
                line_color = "orange" # Яскравіший колір для променя, що вдарився
            
            self.maze_canvas.create_line(sx_px, sy_px, ex_px, ey_px,
                                         fill=line_color, width=line_width, tags=(tag_rays, "rangefinder_ray"))
            
            # Позначаємо точку, де промінь зупинився (якщо не на максимальній відстані)
            # if actual_dist < agent.rangefinder_max_dist - 0.1: # Невеликий допуск для точності float
            #     self.maze_canvas.create_oval(ex_px - hit_point_radius, ey_px - hit_point_radius,
            #                                  ex_px + hit_point_radius, ey_px + hit_point_radius,
            #                                  fill=COLOR_RANGEFINDER_HIT, outline="", tags=(tag_rays, "rangefinder_hit"))


    def _create_control_widgets(self, parent_frame):
        """Створює віджети на панелі керування."""
        # 1. --- Create Canvas and Scrollbar ---
        # --- THIS IS THE FIX ---
        # Configure the grid of the parent_frame (the control_frame) itself.
        # This makes its first row and column expand to fill the available space.
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        # --- END OF FIX ---

        # 1. --- Create Canvas and Scrollbar ---
        canvas = tk.Canvas(parent_frame, borderwidth=0, highlightthickness=0) # Added highlightthickness=0
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        # Add padding directly to the frame that holds the content. This is the correct place for it.
        scrollable_frame = ttk.Frame(canvas, padding=(5, 5)) 

        canvas.configure(yscrollcommand=scrollbar.set)

        # This binding updates the scrollregion when the size of the inner frame changes.
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # --- NEW AND IMPORTANT PART ---
        # This part makes the inner frame resize horizontally with the canvas.
        # 1. Create the window and save its ID.
        scrollable_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 2. Create a function that resizes the inner frame to the canvas width.
        def _configure_scrollable_window(event):
            canvas.itemconfig(scrollable_window, width=event.width)

        # 3. Bind that function to the canvas's <Configure> event.
        canvas.bind("<Configure>", _configure_scrollable_window)
        # --- END OF NEW PART ---

        canvas.grid(row=0, column=0, sticky="nswe") # The reverted line from Step 1
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- From here on, all widgets are parented to 'scrollable_frame' ---
        
        scrollable_frame.grid_columnconfigure(0, weight=1)
        current_row = 0

         # --- Керування Симуляцією ---
        
        sim_control_frame = ttk.LabelFrame(scrollable_frame, text="Simulation Control", padding=(5, 5))
        sim_control_frame.grid(row=current_row, column=0, sticky="ew", padx=5, pady=5); current_row += 1
        sim_control_frame.columnconfigure(0, weight=1)
        self.start_pause_button = ttk.Button(sim_control_frame, text="Start Viz", command=self._on_start_pause)
        self.start_pause_button.grid(row=0, column=0, sticky="ew", pady=2)
        self.next_gen_button = ttk.Button(sim_control_frame, text="Next Generation", command=self._on_next_generation, state=tk.NORMAL)
        self.next_gen_button.grid(row=1, column=0, sticky="ew", pady=2)
        
        run_n_frame = ttk.Frame(sim_control_frame)
        run_n_frame.grid(row=2, column=0, sticky="ew", pady=(5, 2))
        run_n_frame.columnconfigure(1, weight=1)

        ttk.Label(run_n_frame, text="Run").grid(row=0, column=0, padx=(0, 2))
        self.num_gens_var = tk.StringVar(value="50")
        self.num_gens_entry = ttk.Entry(run_n_frame, textvariable=self.num_gens_var, width=5)
        self.num_gens_entry.grid(row=0, column=1, padx=(0, 2), sticky="ew")
        ttk.Label(run_n_frame, text="Gens").grid(row=0, column=2, padx=(0, 5))
        self.run_n_button = ttk.Button(run_n_frame, text="Go", width=4, command=self._on_run_n_generations)
        self.run_n_button.grid(row=0, column=3)

        self.reset_button = ttk.Button(sim_control_frame, text="Reset Simulation", command=self._on_reset)
        self.reset_button.grid(row=3, column=0, sticky="ew", pady=2)

        # --- Налаштування Лабіринту ---
        settings_frame = ttk.LabelFrame(scrollable_frame, text="Maze Settings", padding=(5, 5))
        settings_frame.grid(row=current_row, column=0, sticky="ew", padx=5, pady=5); current_row += 1
        settings_frame.columnconfigure(1, weight=1)
        ttk.Label(settings_frame, text="Maze Seed:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        initial_seed = self.config.get("MAZE_SEED", "")
        self.seed_var = tk.StringVar(value=str(initial_seed) if initial_seed is not None else "")
        self.seed_entry = ttk.Entry(settings_frame, textvariable=self.seed_var, width=15)
        self.seed_entry.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        self.new_maze_button = ttk.Button(settings_frame, text="Generate New Maze", command=self._on_new_maze)
        self.new_maze_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 2))
        
        # --- Статистика ---
        stats_frame = ttk.LabelFrame(scrollable_frame, text="Statistics", padding=(5, 5))
        stats_frame.grid(row=current_row, column=0, sticky="ew", padx=5, pady=5); current_row += 1
        stats_frame.columnconfigure(0, weight=1)
        self.gen_label = ttk.Label(stats_frame, text="Generation: 0")
        self.gen_label.pack(anchor=tk.W)
        self.species_label = ttk.Label(stats_frame, text="Species: 0")
        self.species_label.pack(anchor=tk.W)
        self.best_fitness_label = ttk.Label(stats_frame, text="Best Fitness (Gen): N/A")
        self.best_fitness_label.pack(anchor=tk.W)
        self.avg_fitness_label = ttk.Label(stats_frame, text="Avg Fitness (Gen): N/A")
        self.avg_fitness_label.pack(anchor=tk.W)
        self.best_overall_fitness_label = ttk.Label(stats_frame, text="Best Fitness (Overall): N/A")
        self.best_overall_fitness_label.pack(anchor=tk.W)

         # --- Save/Load Training ---
        save_load_frame = ttk.LabelFrame(scrollable_frame, text="Save/Load Training", padding=(5, 5))
        save_load_frame.grid(row=current_row, column=0, sticky="ew", padx=5, pady=5); current_row += 1
        save_load_frame.columnconfigure(0, weight=1)
        save_load_frame.columnconfigure(1, weight=1)

        self.save_button = ttk.Button(save_load_frame, text="Save State", command=self._on_save_simulation)
        self.save_button.grid(row=0, column=0, sticky="ew", padx=(0,2), pady=2)
        self.load_button = ttk.Button(save_load_frame, text="Load State", command=self._on_load_simulation)
        self.load_button.grid(row=0, column=1, sticky="ew", padx=(2,0), pady=2)
        # --- Налаштування Візуалізації (сенсори) ---
        # Створюємо цей фрейм ПЕРЕД network_frame, якщо він має бути над ним
        viz_settings_frame = ttk.LabelFrame(scrollable_frame, text="Visualization Settings", padding=(5,5))
        viz_settings_frame.grid(row=current_row, column=0, sticky="ew", padx=5, pady=5); current_row += 1
        
        self.show_sensors_var = tk.BooleanVar(value=False)
        self.show_sensors_check = ttk.Checkbutton(viz_settings_frame, text="Show Agent Sensors",
                                                  variable=self.show_sensors_var,
                                                  command=self._on_toggle_show_sensors)
        self.show_sensors_check.pack(anchor=tk.W, padx=5, pady=2)
        # --- Відображення Топології ---
        self.network_frame = ttk.LabelFrame(scrollable_frame, text="Network Topology", padding=(5, 5))
        self.network_frame.grid(row=current_row, column=0, sticky="nsew", padx=5, pady=5)
        scrollable_frame.grid_rowconfigure(current_row, weight=1)
        current_row += 1

        self.network_canvas = tk.Canvas(self.network_frame, bg=COLOR_BACKGROUND, bd=0, highlightthickness=0)
        self.network_canvas.pack(fill=tk.BOTH, expand=True)
        # Прив'язки для зуму та панорамування
        self.network_canvas.bind("<Configure>", self._on_network_canvas_resize) # Оновлення розмірів
        self.network_canvas.bind("<MouseWheel>", self._on_mouse_wheel)       # Windows/MacOS
        self.network_canvas.bind("<Button-4>", self._on_mouse_wheel)         # Linux (zoom in)
        self.network_canvas.bind("<Button-5>", self._on_mouse_wheel)         # Linux (zoom out)
        self.network_canvas.bind("<ButtonPress-1>", self._on_network_drag_start)
        self.network_canvas.bind("<B1-Motion>", self._on_network_drag_motion)


        # --- Вибір Геному для Візуалізації ---
        select_frame = ttk.Frame(self.network_frame, padding=(0, 2)) # Зменшено відступ
        select_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(2,0))
        select_frame.columnconfigure(1, weight=1)

        ttk.Label(select_frame, text="ID:").grid(row=0, column=0, padx=(0, 2), sticky='w')
        self.genome_id_var = tk.StringVar()
        self.genome_id_entry = ttk.Entry(select_frame, textvariable=self.genome_id_var, width=8)
        self.genome_id_entry.grid(row=0, column=1, sticky='ew')
        self.visualize_id_button = ttk.Button(select_frame, text="Show", width=5, command=self._on_visualize_genome_id)
        self.visualize_id_button.grid(row=0, column=2, padx=(2, 0))
        # Слайдер зуму ВИДАЛЕНО

    def _on_toggle_show_sensors(self):
        """Обробник зміни стану чекбокса "Show Agent Sensors"."""
        # Цей метод викликається, коли користувач клікає на чекбокс.
        # Якщо симуляція на паузі, ми можемо одразу оновити візуалізацію.
        # Якщо симуляція запущена, зміна буде врахована при наступному кроці оновлення.
        if not self.is_running and self.main_controller and hasattr(self.main_controller, '_update_agents_visuals'):
            # Примусово оновлюємо візуалізацію агентів, щоб показати/сховати сенсори
            self.main_controller._update_agents_visuals()
            self.update_gui() # Оновлюємо Tkinter GUI
        # В іншому випадку (якщо is_running), _update_agents_visuals в simulation_step
        # підхопить новий стан self.show_sensors_var.get()
    def _on_save_simulation(self):
        if self.main_controller:
            if self.is_running: # Зупиняємо візуалізацію перед збереженням
                self.is_running = False
                self.set_controls_state(False) # Оновлюємо стан кнопок
                # self.main_controller.toggle_simulation(False) # Повідомляємо контролер
            self.main_controller.save_simulation()

    def _on_load_simulation(self):
        if self.main_controller:
            if self.is_running: # Зупиняємо візуалізацію перед завантаженням
                self.is_running = False
                self.set_controls_state(False)
                # self.main_controller.toggle_simulation(False)
            self.main_controller.load_simulation()
            # Оновлюємо сід в GUI після завантаження
            if hasattr(self.main_controller, 'config') and 'MAZE_SEED' in self.main_controller.config:
                self.seed_var.set(str(self.main_controller.config['MAZE_SEED']))
            # Оновлюємо візуалізацію мережі, щоб показати завантажений геном
            self.update_network_visualization()
    # --- Обробники подій для зуму та панорамування ---


    def _on_run_n_generations(self):
        if self.is_running: # Не запускаємо, якщо йде візуалізація
            messagebox.showwarning("Simulation Running", "Cannot run multiple generations while visualization is active. Pause first.")
            return
        if not self.main_controller:
            print("Error: Main controller missing.")
            return

        try:
            num_gens_to_run = int(self.num_gens_var.get())
            if num_gens_to_run <= 0:
                messagebox.showerror("Invalid Input", "Number of generations must be positive.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", f"Invalid number of generations: '{self.num_gens_var.get()}'.")
            return

        # Блокуємо кнопки керування
        self.set_controls_state(running=True, running_multiple=True)
        # Запускаємо в окремому потоці, щоб не блокувати GUI
        thread = threading.Thread(target=self.main_controller.run_multiple_generations,
                                 args=(num_gens_to_run,), daemon=True)
        thread.start()

    def _on_network_canvas_resize(self, event):
        """Обробник зміни розміру канвасу мережі."""
        self._network_canvas_width = event.width
        self._network_canvas_height = event.height
        # Перемальовуємо з поточним зумом/зсувом
        self._redraw_network_image()
    def _on_mouse_wheel(self, event):
        """Обробник прокрутки колеса миші над канвасом мережі."""
        if not self._current_network_pil_image: return

        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor
        zoom_change = 0

        # Визначаємо напрямок прокрутки
        if event.num == 5 or event.delta < 0: # Zoom out (Linux or Windows/MacOS)
            zoom_change = zoom_out_factor
        elif event.num == 4 or event.delta > 0: # Zoom in (Linux or Windows/MacOS)
            zoom_change = zoom_in_factor

        if zoom_change != 0:
            # Координати миші відносно канвасу
            mouse_x, mouse_y = event.x, event.y

            # Поточні розміри оригінального зображення
            img_w, img_h = self._current_network_pil_image.size
            if img_w <= 0 or img_h <= 0: return

            # Поточні розміри відображуваного зображення
            current_display_w = img_w * self._network_zoom
            current_display_h = img_h * self._network_zoom

            # Координати миші в системі координат оригінального зображення (до зуму)
            # Враховуємо поточний зсув
            img_coord_x = (mouse_x - self._network_offset_x) / self._network_zoom
            img_coord_y = (mouse_y - self._network_offset_y) / self._network_zoom

            # Оновлюємо зум
            new_zoom = self._network_zoom * zoom_change
            # Обмежуємо зум
            new_zoom = max(0.1, min(new_zoom, 10.0)) # Приклад обмежень

            # Розраховуємо новий зсув, щоб точка під мишею залишилась на місці
            # mouse_x = new_offset_x + img_coord_x * new_zoom
            # mouse_y = new_offset_y + img_coord_y * new_zoom
            self._network_offset_x = mouse_x - img_coord_x * new_zoom
            self._network_offset_y = mouse_y - img_coord_y * new_zoom

            self._network_zoom = new_zoom
            self._redraw_network_image() # Перемальовуємо з новими параметрами
    def _on_network_drag_start(self, event):
        """Початок перетягування зображення мережі."""
        self.network_canvas.scan_mark(event.x, event.y)
        self._network_drag_start_x = event.x
        self._network_drag_start_y = event.y

    def _on_network_drag_motion(self, event):
        """Переміщення під час перетягування зображення мережі."""
        if not self._current_network_pil_image: return

        dx = event.x - self._network_drag_start_x
        dy = event.y - self._network_drag_start_y

        # Оновлюємо зсув
        self._network_offset_x += dx
        self._network_offset_y += dy

        # Зберігаємо нову стартову точку
        self._network_drag_start_x = event.x
        self._network_drag_start_y = event.y

        self._redraw_network_image() # Перемальовуємо з новим зсувом

    # --- Методи візуалізації ---

    def update_network_visualization(self, genome_id_to_show: Optional[int] = None):
         """Оновлює візуалізацію мережі для заданого ID (або найкращого)."""
         genome_to_visualize = None
         actual_genome_id = None

         # --- Логіка вибору геному (без змін) ---
         if genome_id_to_show is not None and self.main_controller:
             genome_to_visualize = self.main_controller.get_genome_by_id(genome_id_to_show)
             if genome_to_visualize: actual_genome_id = genome_id_to_show
         if not genome_to_visualize and self.main_controller:
             best_overall = self.main_controller.neat.best_genome_overall
             if best_overall:
                  genome_to_visualize = best_overall
                  actual_genome_id = best_overall.id
             elif self.main_controller.neat.population:
                  valid_pop = [g for g in self.main_controller.neat.population if g is not None]
                  if valid_pop:
                       best_current = max(valid_pop, key=lambda g: g.fitness, default=None)
                       if best_current:
                            genome_to_visualize = best_current
                            actual_genome_id = best_current.id
             if not genome_to_visualize and self.main_controller.neat.population:
                   valid_pop = [g for g in self.main_controller.neat.population if g is not None]
                   if valid_pop:
                       genome_to_visualize = random.choice(valid_pop)
                       actual_genome_id = genome_to_visualize.id

         # --- Оновлення GUI (без змін) ---
         title_text = "Network Topology"
         if actual_genome_id is not None:
             title_text += f" (Genome ID: {actual_genome_id})"
             self.genome_id_var.set(str(actual_genome_id))
         else:
             self.genome_id_var.set("")
         self.genome_to_display_id = actual_genome_id # Зберігаємо ID

         if isinstance(self.network_frame, ttk.LabelFrame):
              self.network_frame.config(text=title_text)

         # --- Генеруємо ОРИГІНАЛЬНЕ зображення (без зуму) ---
         network_image_pil = None
         if genome_to_visualize:
               network_image_pil = visualize_network(genome_to_visualize, zoom_factor=1.0) # Завжди генеруємо базове

         self.display_network(network_image_pil) # Зберігаємо і викликаємо перемальовку

    def draw_maze(self, maze_grid: list[list[int]], cell_size: int):
        """Малює лабіринт на канвасі."""
        self._cell_size = cell_size
        self.maze_canvas.delete("maze") # Видаляємо попередній лабіринт

        height = len(maze_grid)
        width = len(maze_grid[0]) if height > 0 else 0
        if width == 0: return

        canvas_width = width * cell_size
        canvas_height = height * cell_size
        self.maze_canvas.config(scrollregion=(0, 0, canvas_width, canvas_height),
                               width=canvas_width, height=canvas_height) # Оновлюємо розмір канвасу

        for r in range(height):
            for c in range(width):
                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                fill_color = COLOR_PATH
                cell_type = maze_grid[r][c]

                if cell_type == CELL_WALL: fill_color = COLOR_WALL
                elif cell_type == CELL_START: fill_color = COLOR_START
                elif cell_type == CELL_GOAL: fill_color = COLOR_GOAL

                self.maze_canvas.create_rectangle(x1, y1, x2, y2,
                                                  fill=fill_color,
                                                  outline=COLOR_MAZE_OUTLINE,
                                                  tags="maze")

    def update_agent_visual(self, agent_id: int, x: float, y: float, angle_rad: float,
                              is_best_gen: bool = False, is_best_overall: bool = False,
                              show_sensors: bool = False): # Додамо параметр show_sensors
        """Оновлює або створює візуальне представлення агента ТА його сенсорів."""
        if self._cell_size <= 0: return

        radius = self._cell_size * 0.35
        x_pixel = x * self._cell_size
        y_pixel = y * self._cell_size

        if is_best_overall: color, line_color, z = COLOR_AGENT_OVERALL_BEST, "white", 3
        elif is_best_gen: color, line_color, z = COLOR_AGENT_BEST, "black", 2
        else: color, line_color, z = COLOR_AGENT_DEFAULT, "white", 1

        x1, y1 = x_pixel - radius, y_pixel - radius
        x2, y2 = x_pixel + radius, y_pixel + radius
        line_len = radius
        end_x_heading = x_pixel + math.cos(angle_rad) * line_len
        end_y_heading = y_pixel + math.sin(angle_rad) * line_len

        tag_agent_body = f"agent_{agent_id}_body"
        tag_agent_heading = f"agent_{agent_id}_heading"
        
        # Видаляємо старі частини тіла та напрямку
        self.maze_canvas.delete(tag_agent_body)
        self.maze_canvas.delete(tag_agent_heading)

        # Малюємо нове тіло та напрямок
        self.maze_canvas.create_oval(x1, y1, x2, y2, fill=color, outline="black", width=1, tags=(tag_agent_body, "agent_body"))
        self.maze_canvas.create_line(x_pixel, y_pixel, end_x_heading, end_y_heading, fill=line_color, width=max(1, int(self._cell_size * 0.1)), tags=(tag_agent_heading, "agent_heading"))

        # Піднімаємо шар відповідно до z
        for _ in range(z):
             self.maze_canvas.tag_raise(tag_agent_body)
             self.maze_canvas.tag_raise(tag_agent_heading)
        
        # Малюємо промені сенсорів, якщо потрібно
        tag_rays = f"agent_{agent_id}_rays"
        self.maze_canvas.delete(tag_rays) # Завжди видаляємо старі промені

        if show_sensors:
            agent = self.main_controller.agents.get(agent_id) # Отримуємо об'єкт агента
            if agent and hasattr(agent, 'last_rangefinder_rays'):
                cell_s = self._cell_size
                for sx, sy, ex, ey, actual_dist in agent.last_rangefinder_rays:
                    sx_px, sy_px = sx * cell_s, sy * cell_s
                    ex_px, ey_px = ex * cell_s, ey * cell_s
                    
                    ray_line_color = "yellow"
                    ray_line_width = 1
                    if actual_dist < agent.rangefinder_max_dist - 0.1:
                        ray_line_color = "orange"
                    
                    self.maze_canvas.create_line(sx_px, sy_px, ex_px, ey_px,
                                                 fill=ray_line_color, width=ray_line_width, tags=(tag_rays, "rangefinder_ray"))
                    # Можна підняти промені над агентом, або опустити під нього
                    self.maze_canvas.tag_lower(tag_rays, tag_agent_body)


    def remove_agent_visual(self, agent_id: int):
        """Видаляє візуальне представлення агента."""
        tag = self.agent_tags.pop(agent_id, None)
        if tag:
            self.maze_canvas.delete(tag)

    def clear_all_agents(self):
        """Видаляє всіх агентів (тіла, напрямки, промені) з канвасу."""
        self.maze_canvas.delete("agent_body")
        self.maze_canvas.delete("agent_heading")
        self.maze_canvas.delete("rangefinder_ray") # Додаємо видалення тегу променів
        # self.agent_tags.clear() # Це було для старих тегів, тепер не так використовується


    def update_stats(self, generation: int, num_species: int, best_fitness_gen: Optional[float], avg_fitness_gen: Optional[float], best_fitness_overall: Optional[float], best_genome_id_to_show: Optional[int]):
        """Оновлює текстові мітки зі статистикою та ініціює візуалізацію мережі."""
        # Оновлення текстових міток
        self.gen_label.config(text=f"Generation: {generation}")
        self.species_label.config(text=f"Species: {num_species}")
        bfg_text = f"{best_fitness_gen:.4f}" if best_fitness_gen is not None else "N/A"
        afg_text = f"{avg_fitness_gen:.4f}" if avg_fitness_gen is not None else "N/A"
        bfo_text = f"{best_fitness_overall:.4f}" if best_fitness_overall is not None else "N/A"
        self.best_fitness_label.config(text=f"Best Fitness (Gen): {bfg_text}")
        self.avg_fitness_label.config(text=f"Avg Fitness (Gen): {afg_text}")
        self.best_overall_fitness_label.config(text=f"Best Fitness (Overall): {bfo_text}")

        # Оновлення візуалізації мережі
        genome_to_visualize = None
        if best_genome_id_to_show is not None and self.main_controller:
            genome_to_visualize = self.main_controller.get_genome_by_id(best_genome_id_to_show)

        title_text = "Network Topology"
        if genome_to_visualize:
             title_text += f" (Genome ID: {genome_to_visualize.id})"
             self.genome_id_var.set(str(genome_to_visualize.id))
        else:
             self.genome_id_var.set("")

        if isinstance(self.network_frame, ttk.LabelFrame):
             self.network_frame.config(text=title_text)

       
        self.update_network_visualization(self.genome_to_display_id)
       # self.display_network(network_image) # Передаємо PIL Image у GUI

    def display_network(self, network_image_pil: Optional[Image.Image]):
        """Зберігає ОРИГІНАЛЬНЕ PIL зображення мережі та ініціює перемалювання."""
        # Скидаємо зум та зсув при відображенні НОВОГО геному
        if network_image_pil is not None and self._current_network_pil_image is not network_image_pil:
             self._network_zoom = 1.0
             # Центруємо нове зображення
             if hasattr(self, 'network_canvas'): # Перевіряємо чи канвас створено
                 self._network_offset_x = self._network_canvas_width / 2 - (network_image_pil.width / 2) if network_image_pil else 0
                 self._network_offset_y = self._network_canvas_height / 2 - (network_image_pil.height / 2) if network_image_pil else 0
             else:
                 self._network_offset_x = 0
                 self._network_offset_y = 0

        self._current_network_pil_image = network_image_pil
        self._redraw_network_image()
    def _redraw_network_image(self, event=None):
        """
        Перемальовує зображення мережі на канвасі з урахуванням
        поточного масштабу (_network_zoom) та зсуву (_network_offset_x/y).
        """
        self.network_canvas.delete("network_img") # Видаляємо старе
        if not self._current_network_pil_image:
            # ... (код для тексту-заглушки, без змін) ...
            canvas_width = self._network_canvas_width
            canvas_height = self._network_canvas_height
            if canvas_width > 1 and canvas_height > 1:
                 self.network_canvas.create_text(canvas_width / 2, canvas_height / 2, text="No network to display", fill="grey", anchor=tk.CENTER, tags="network_img")
            return

        # Отримуємо поточні розміри канвасу, якщо вони не збережені
        if self._network_canvas_width <= 1: self._network_canvas_width = self.network_canvas.winfo_width()
        if self._network_canvas_height <= 1: self._network_canvas_height = self.network_canvas.winfo_height()
        canvas_width = self._network_canvas_width
        canvas_height = self._network_canvas_height
        if canvas_width <= 1 or canvas_height <= 1: return # Все ще невідомі розміри

        img_original = self._current_network_pil_image
        original_width, original_height = img_original.size
        if original_width <= 0 or original_height <= 0: return

        # --- Розрахунок розміру масштабованого зображення ---
        display_width = int(original_width * self._network_zoom)
        display_height = int(original_height * self._network_zoom)

        if display_width <= 0 or display_height <= 0: return # Уникаємо помилок масштабування

        try:
             # Масштабуємо ОРИГІНАЛЬНЕ зображення до розрахованого розміру
             img_resized = img_original.resize((display_width, display_height), Image.Resampling.LANCZOS)
             self.network_photo = ImageTk.PhotoImage(img_resized)
        except Exception as e:
             print(f"Error resizing network image: {e}")
             try: self.network_photo = ImageTk.PhotoImage(img_original) # Показуємо оригінал
             except: return

        # --- Відображаємо зображення зі зсувом ---
        # Координати верхнього лівого кута масштабованого зображення
        draw_x = self._network_offset_x
        draw_y = self._network_offset_y

        # Створюємо зображення на канвасі
        self.network_canvas.create_image(draw_x, draw_y, anchor=tk.NW, # Прив'язка до верхнього лівого кута
                                         image=self.network_photo, tags="network_img")


    # --- Обробники подій кнопок ---
    # _on_start_pause, _on_new_maze, _on_reset, _on_visualize_genome_id
    # ЗАЛИШАЮТЬСЯ БЕЗ ЗМІН (але тепер викликають _update_network_visualization)

    def update_gui_from_thread(self, stats):
         """Безпечно оновлює GUI зі стану, переданого з іншого потоку."""
         # Використовуємо master.after для виконання в головному потоці Tkinter
         self.master.after(0, self._update_gui_safe, stats)
    def _update_gui_safe(self, stats):
         """Метод, що фактично оновлює GUI."""
         if not stats: return
         try:
              # Оновлюємо мітки статистики
              self.gen_label.config(text=f"Generation: {stats.get('generation', 'N/A')}")
              self.species_label.config(text=f"Species: {stats.get('num_species', 'N/A')}")
              bfg = stats.get('max_fitness')
              afg = stats.get('average_fitness')
              bfo = stats.get('best_overall_fitness')
              bfg_text = f"{bfg:.4f}" if bfg is not None else "N/A"
              afg_text = f"{afg:.4f}" if afg is not None else "N/A"
              bfo_text = f"{bfo:.4f}" if bfo is not None else "N/A"
              self.best_fitness_label.config(text=f"Best Fitness (Gen): {bfg_text}")
              self.avg_fitness_label.config(text=f"Avg Fitness (Gen): {afg_text}")
              self.best_overall_fitness_label.config(text=f"Best Fitness (Overall): {bfo_text}")

              # Оновлюємо візуалізацію мережі для найкращого геному
              best_overall_genome = stats.get('best_genome_overall')
              best_gen_genome = stats.get('best_genome_current_gen')
              genome_to_show = best_overall_genome if best_overall_genome else best_gen_genome
              genome_id_to_show = genome_to_show.id if genome_to_show else None

              self.update_network_visualization(genome_id_to_show) # Викличе генерацію та display_network

              self.update_gui() # Оновлюємо саме вікно

         except Exception as e:
              print(f"Error updating GUI from thread: {e}")

    def set_controls_state(self, running: bool, running_multiple: bool = False):
         """Встановлює стан кнопок керування."""
         self.is_running = running # Стан візуалізації

         # Блокуємо все, якщо виконується run_multiple_generations
         sim_controls_state = tk.DISABLED if running_multiple else tk.NORMAL
         viz_controls_state = tk.DISABLED if running_multiple or running else tk.NORMAL

         self.start_pause_button.config(text="Pause Viz" if running else "Start Viz", state=sim_controls_state if not running_multiple else tk.DISABLED)
         self.next_gen_button.config(state=sim_controls_state)
         self.run_n_button.config(state=sim_controls_state)
         self.num_gens_entry.config(state=sim_controls_state)
         self.reset_button.config(state=sim_controls_state)
         self.new_maze_button.config(state=sim_controls_state)
         # Керування візуалізацією ID блокуємо, якщо йде візуалізація або batch run
         self.visualize_id_button.config(state=viz_controls_state)
         self.genome_id_entry.config(state=viz_controls_state)

    # --- Обробники подій ---
    def _on_start_pause(self):
        if self.main_controller:
            self.is_running = not self.is_running
            self.set_controls_state(self.is_running)
            self.main_controller.toggle_simulation(self.is_running)
        else: print("Error: Main controller missing.")

    def _on_next_generation(self):
        if not self.is_running and self.main_controller:
            self.set_controls_state(True)
            self.master.update()
            try:
                self.main_controller.run_one_generation()
                # ОНОВЛЮЄМО ВІЗУАЛІЗАЦІЮ ПІСЛЯ ГЕНЕРАЦІЇ
                self.update_network_visualization() # Покаже найкращий за замовчуванням
            finally:
                self.set_controls_state(False)
        elif not self.main_controller: print("Error: Main controller missing.")

    def _on_new_maze(self):
         if not self.is_running and self.main_controller:
            seed_str = self.seed_var.get().strip()
            seed = None
            if seed_str:
                try: seed = int(seed_str)
                except ValueError:
                    messagebox.showerror("Invalid Seed", f"Cannot parse seed: '{seed_str}'. Using random.")
                    self.seed_var.set("")
            new_seed = self.main_controller.generate_new_maze(seed)
            if new_seed is not None: self.seed_var.set(str(new_seed))
         elif not self.main_controller: print("Error: Main controller missing.")

    def _on_reset(self):
        if not self.is_running and self.main_controller:
             if messagebox.askyesno("Confirm Reset", "Reset NEAT simulation to generation 0?"):
                self.set_controls_state(True)
                self.master.update()
                try:
                    self.main_controller.reset_simulation()
                    new_seed = self.config.get('MAZE_SEED', '')
                    self.seed_var.set(str(new_seed) if new_seed is not None else "")
                    # ОНОВЛЮЄМО ВІЗУАЛІЗАЦІЮ ПІСЛЯ СКИДАННЯ
                    self.update_network_visualization() # Покаже випадковий геном
                finally:
                    self.set_controls_state(False)
        elif not self.main_controller: print("Error: Main controller missing.")

    def _on_visualize_genome_id(self):
        """Обробник кнопки 'Show' для візуалізації геному за ID."""
        if self.is_running or not self.main_controller: return

        genome_id_str = self.genome_id_var.get().strip()
        if not genome_id_str:
             messagebox.showwarning("Input Error", "Please enter a Genome ID.")
             return

        try:
             genome_id = int(genome_id_str)
             self.update_network_visualization(genome_id) # Оновлюємо візуалізацію
             if str(self.genome_to_display_id) != genome_id_str: # Перевіряємо чи вдалось
                 messagebox.showerror("Genome Not Found", f"Genome with ID '{genome_id_str}' not found.")
        except ValueError:
             messagebox.showerror("Invalid ID", f"Cannot parse Genome ID: '{genome_id_str}'.")
        except Exception as e:
             messagebox.showerror("Visualization Error", f"Could not visualize genome {genome_id_str}:\n{e}")

    def update_gui(self):
         """Оновлює GUI Tkinter."""
         try:
            self.master.update()
            self.master.update_idletasks()
         except tk.TclError as e:
              if "application has been destroyed" not in str(e):
                   print(f"Tkinter update error: {e}")