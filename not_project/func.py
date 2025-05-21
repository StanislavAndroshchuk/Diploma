import numpy as np
from math import pi, cos, sin

# --- Цільові функції (без ризику) ---
def I_12(x, y):
    """Цільова функція суб'єкта 1 (без ризику)"""
    function = sin(pi * (x / 2)) + 0.01 * sin(pi * (x / 2)) * y - 0.1 * y
    return function

def I_21(x, y):
    """Цільова функція суб'єкта 2 (без ризику)"""
    function = -cos(pi * (x / 2)) + 0.1 * cos(pi * (x / 2)) * y + 0.2 * y + 1
    return function

# --- Функції збитку (J) - Варіант 1 ---
def J12_ns(x,y):
    function = 0.04*y - 0.05*x*y - 0.03*x - 0.06
    return function

def J12_fm(x,y):
    function = 0.1*y - 0.01*x*y + 0.014*x + 0.2
    return function

def J12_in(x,y):
    function = 0.12*y - 0.33*x*y - 0.03*x + 0.11
    return function

def J21_ns(x,y):
    function = -0.015*y - 0.03*x*y + 0.14*x - 0.11
    return function

def J21_fm(x,y):
    function = 0.18*y - 0.01*x*y + 0.1*x - 0.44
    return function

def J21_in(x,y):
    function = -0.095*y - 0.009*x*y + 0.032*x + 0.64
    return function

# --- Матриці ймовірностей ризиків (R) - Варіант 1 ---
# R1[ситуація_y, тип_ризику] (0: ns, 1: fm, 2: in)
# Ситуації S1 (y=0), S2 (y=1), S3 (y=2)
R1 = np.array([
    [0.03, 0.01, 0.04], # S1 (y=0)
    [0.03, 0.015, 0.01],# S2 (y=1)
    [0.05, 0.02, 0.01]  # S3 (y=2)
])

# R2[ситуація_x, тип_ризику] (0: ns, 1: fm, 2: in)
# Ситуації S1 (x=0), S2 (x=1), S3 (x=2)
R2 = np.array([
    [0.07, 0.04, 0.002],# S1 (x=0)
    [0.09, 0.01, 0.004],# S2 (x=1)
    [0.12, 0.03, 0.015] # S3 (x=2)
])

# --- Функція для визначення індексу ситуації ---
def get_situation_index(value):
    """Визначає індекс ситуації (0, 1, 2) на основі значення x або y"""
    index = int(round(value))
    if index < 0: index = 0
    elif index > 2: index = 2
    return index

# --- Функції для обчислення F12 та F21 ---
def calculate_F12(x, y):
    """Обчислює F12 з урахуванням ризиків"""
    base_value = I_12(x, y)
    sit_index_r1 = get_situation_index(y)
    eta_1_ns, eta_1_fm, eta_1_in = R1[sit_index_r1]
    loss = (eta_1_ns * J12_ns(x, y) +
            eta_1_fm * J12_fm(x, y) +
            eta_1_in * J12_in(x, y))
    return base_value - loss

def calculate_F21(x, y):
    """Обчислює F21 з урахуванням ризиків"""
    base_value = I_21(x, y)
    sit_index_r2 = get_situation_index(x)
    eta_2_ns, eta_2_fm, eta_2_in = R2[sit_index_r2]
    loss = (eta_2_ns * J21_ns(x, y) +
            eta_2_fm * J21_fm(x, y) +
            eta_2_in * J21_in(x, y))
    return base_value - loss

# --- Допоміжна функція друку таблиць ---
def print_table(function, x_vals, y_vals, title_func_name=None):
    """Друкує таблицю значень функції"""
    name = title_func_name if title_func_name else function.__name__
    print("============================")
    print(f"Таблиця значень для {name}(x,y)")
    print("x\\y\t" + "\t".join(map(lambda val: f"{val:.2f}", y_vals)))
    print("----------------------------")
    is_matrix = isinstance(function, np.ndarray)
    for i in range(len(x_vals)):
        row = []
        for j in range(len(y_vals)):
             if is_matrix: val = function[i, j]
             else: val = function(x_vals[i], y_vals[j])
             row.append(f"{val:.4f}")
        print(f"{x_vals[i]:.2f}\t" + "\t".join(row))
    print("============================")

# --- Основна частина ---
if __name__ == "__main__":
    x_min, x_max = 0, 2
    y_min, y_max = 0, 2
    step = 0.5

    x_vals = np.arange(x_min, x_max + step, step)
    y_vals = np.arange(y_min, y_max + step, step)
    n_x = len(x_vals)
    n_y = len(y_vals)

    # --- 1. Обчислення матриць значень I (без ризику) ---
    i12_matrix = np.zeros((n_x, n_y))
    i21_matrix = np.zeros((n_x, n_y))
    for i in range(n_x):
        for j in range(n_y):
            i12_matrix[i, j] = I_12(x_vals[i], y_vals[j])
            i21_matrix[i, j] = I_21(x_vals[i], y_vals[j])

    # --- 2. Визначення найбільш несприятливих ситуацій ---
    # На основі аналізу суми ймовірностей, обидві S3 є найбільш несприятливими
    unfav_sit_idx_r1 = 2 # Ситуація S3 для R1 (y=2)
    unfav_sit_idx_r2 = 2 # Ситуація S3 для R2 (x=2)
    y_unfav_r1 = y_vals[unfav_sit_idx_r1] # y=2.0
    x_unfav_r2 = x_vals[unfav_sit_idx_r2] # x=2.0

    print(f"\nНайбільш несприятлива ситуація для Коаліції 1: S{unfav_sit_idx_r1+1} (y={y_unfav_r1:.1f})")
    print(f"Найбільш несприятлива ситуація для Коаліції 2: S{unfav_sit_idx_r2+1} (x={x_unfav_r2:.1f})")

    # --- 3. Розрахунок "Worst" (максимальних виграшів I в несприятливих ситуаціях) ---
    # I12 worst: max I_12(x, y=2)
    i12_in_unfav_sit = i12_matrix[:, unfav_sit_idx_r1] # Значення I_12 при y=2
    i12_worst = np.max(i12_in_unfav_sit)
    x_idx_i12_worst = np.argmax(i12_in_unfav_sit)
    x_at_i12_worst = x_vals[x_idx_i12_worst]

    # I21 worst: max I_21(x=2, y)
    i21_in_unfav_sit = i21_matrix[unfav_sit_idx_r2, :] # Значення I_21 при x=2
    i21_worst = np.max(i21_in_unfav_sit)
    y_idx_i21_worst = np.argmax(i21_in_unfav_sit)
    y_at_i21_worst = y_vals[y_idx_i21_worst]

    print("\n--- Результати для найбільш несприятливих умов (без ризику) ---")
    print(f"I12 worst = {i12_worst:.4f} (досягається при x={x_at_i12_worst:.2f}, y={y_unfav_r1:.1f})")
    print(f"I21 worst = {i21_worst:.4f} (досягається при x={x_unfav_r2:.1f}, y={y_at_i21_worst:.2f})")
    print("----------------------------------------------------------------")

    # --- 4. Розрахунок F (з ризиком) у точках "Worst" ---
    # F12 в точці (x_at_i12_worst, y_unfav_r1)
    f12_at_worst = calculate_F12(x_at_i12_worst, y_unfav_r1)

    # F21 в точці (x_unfav_r2, y_at_i21_worst)
    f21_at_worst = calculate_F21(x_unfav_r2, y_at_i21_worst)

    print("\n--- Значення F в точках 'Worst' (з урахуванням ризику) ---")
    print(f"F12({x_at_i12_worst:.2f}, {y_unfav_r1:.1f}) = {f12_at_worst:.4f}")
    print(f"F21({x_unfav_r2:.1f}, {y_at_i21_worst:.2f}) = {f21_at_worst:.4f}")
    print("-------------------------------------------------------------")