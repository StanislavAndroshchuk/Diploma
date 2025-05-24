# config.py

# --- Параметри популяції та еволюції ---
POPULATION_SIZE = 150
MAX_GENERATIONS = 1000
FITNESS_THRESHOLD = 10000.0 # Приклад - змінити на реалістичне значення

# --- Параметри видоутворення (Speciation) ---
C1_EXCESS = 1.0
C2_DISJOINT = 1.0
C3_WEIGHT = 0.9
COMPATIBILITY_THRESHOLD = 5.0
MAX_STAGNATION = 20

# --- Параметри мутацій ---
ADD_CONNECTION_RATE = 0.19
ADD_NODE_RATE = 0.09
WEIGHT_MUTATE_RATE = 0.6
WEIGHT_REPLACE_RATE = 0.1
WEIGHT_MUTATE_POWER = 0.5
WEIGHT_CAP = 8.0
WEIGHT_INIT_RANGE = 1.0


# --- Параметри початкової структури ---
INITIAL_CONNECTIONS = 8 # Кількість випадкових початкових з'єднань

# --- Параметри кросоверу та відбору ---
CROSSOVER_RATE = 0.75
INHERIT_DISABLED_GENE_RATE = 0.75
ELITISM = 0
SELECTION_PERCENTAGE = 0.20

# --- Параметри середовища та симуляції ---
MAZE_WIDTH = 11
MAZE_HEIGHT = 11
# Перевірка на непарність (можна додати в main.py при завантаженні)
if MAZE_WIDTH % 2 == 0: MAZE_WIDTH += 1
if MAZE_HEIGHT % 2 == 0: MAZE_HEIGHT += 1
MAZE_WIDTH = max(5, MAZE_WIDTH)
MAZE_HEIGHT = max(5, MAZE_HEIGHT)
MAZE_SEED = None
MAX_STEPS_PER_EVALUATION = 400

# --- Параметри агента ---
NUM_RANGEFINDERS = 4
RANGEFINDER_MAX_DIST = 8.0
NUM_RADAR_SLICES = 2
AGENT_MAX_SPEED = 0.5

# --- Параметри візуалізації ---
CELL_SIZE_PX = 20
INFO_PANEL_WIDTH_PX = 300

# --- КІЛЬКІСТЬ ВИХОДІВ ЗАФІКСОВАНА В agent.py ---
# АЛЕ можемо визначити константу тут для ясності
NUM_OUTPUTS = 4 # [TurnL, TurnR, Brake, Accel] - порядок з agent.py