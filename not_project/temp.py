import numpy as np

# --- Функції ---
def f12(x1, x2):
  """Цільова функція суб'єкта 1"""
  return 6*x1**2 - 12*x1 + 4*x2**2 + 8*x2 + 40

def f21(x1, x2):
  """Цільова функція суб'єкта 2"""
  return -3*x2**2 + 6*x2 - 8*x1**2 + 16*x1 + 50

# --- Параметри ---
x1_min, x1_max = -2, 2
x2_min, x2_max = -2, 2
step = 0.01

# Створення сітки
x1_vals = np.arange(x1_min, x1_max + step, step)
x2_vals = np.arange(x2_min, x2_max + step, step)
n1 = len(x1_vals)
n2 = len(x2_vals)

# --- Табличний метод ---
f12_matrix = np.zeros((n1, n2))
f21_matrix = np.zeros((n1, n2))

for i in range(n1):
  for j in range(n2):
    f12_matrix[i, j] = f12(x1_vals[i], x2_vals[j])
    f21_matrix[i, j] = f21(x1_vals[i], x2_vals[j])

# Знаходження гарантованих результатів
min_f12_for_each_x1 = np.min(f12_matrix, axis=1)
f12_star_tabular = np.max(min_f12_for_each_x1)
idx12_x1 = np.argmax(min_f12_for_each_x1)
idx12_x2 = np.argmin(f12_matrix[idx12_x1, :])
x1_at_f12_star = x1_vals[idx12_x1]
x2_at_f12_star = x2_vals[idx12_x2]


min_f21_for_each_x2 = np.min(f21_matrix, axis=0)
f21_star_tabular = np.max(min_f21_for_each_x2)
idx21_x2 = np.argmax(min_f21_for_each_x2)
idx21_x1 = np.argmin(f21_matrix[:, idx21_x2])
x1_at_f21_star = x1_vals[idx21_x1]
x2_at_f21_star = x2_vals[idx21_x2]


print("--- Табличний метод ---")
print(f"f12* = {f12_star_tabular:.4f} (при x1={x1_at_f12_star:.2f}, x2={x2_at_f12_star:.2f})")
print(f"f21* = {f21_star_tabular:.4f} (при x1={x1_at_f21_star:.2f}, x2={x2_at_f21_star:.2f})")
print("-" * 20)

# --- Класичний метод (перевірка) ---
f12_star_classical = 84.0
f21_star_classical = -11.0
print("--- Класичний метод ---")
print(f"f12* = {f12_star_classical:.4f}")
print(f"f21* = {f21_star_classical:.4f}")
print("-" * 20)

# --- Множина Парето та Оптимальні значення ---
pareto_set = []
min_max_delta = float('inf')
optimal_x1 = None
optimal_x2 = None

# Використовуємо значення з класичного методу як більш точні
f12_star = f12_star_classical
f21_star = f21_star_classical
tolerance = 1e-4 # Допуск для порівняння дійсних чисел

for i in range(n1):
    for j in range(n2):
        current_f12 = f12_matrix[i, j]
        current_f21 = f21_matrix[i, j]

        # Перевірка умов Парето
        if current_f12 >= f12_star - tolerance and current_f21 >= f21_star - tolerance:
            pareto_set.append((x1_vals[i], x2_vals[j]))

            # Розрахунок відхилень
            delta1 = abs(current_f12 - f12_star)
            delta2 = abs(current_f21 - f21_star)
            max_delta = max(delta1, delta2)

            # Пошук мінімуму максимального відхилення
            if max_delta < min_max_delta:
                min_max_delta = max_delta
                optimal_x1 = x1_vals[i]
                optimal_x2 = x2_vals[j]

print("--- Множина Парето та Оптимальні значення ---")
if not pareto_set:
    print("Множина Парето порожня.")
else:
    print(f"Знайдено точок у множині Парето: {len(pareto_set)}")
    # print("Деякі точки з множини Парето:", pareto_set[:10]) # Вивести перші 10 точок для прикладу
    print(f"Оптимальні значення (за критерієм min max |fj - fj*|):")
    print(f"x1* = {optimal_x1:.2f}")
    print(f"x2* = {optimal_x2:.2f}")
    print(f"Мінімальне максимальне відхилення Delta = {min_max_delta:.4f}")

    # Перевірка значень функцій в оптимальній точці
    if optimal_x1 is not None:
        opt_f12 = f12(optimal_x1, optimal_x2)
        opt_f21 = f21(optimal_x1, optimal_x2)
        print(f"Значення функцій в оптимальній точці: f12={opt_f12:.4f}, f21={opt_f21:.4f}")
        print(f"Відхилення в оптимальній точці: |f12-f12*|={abs(opt_f12 - f12_star):.4f}, |f21-f21*|={abs(opt_f21 - f21_star):.4f}")

print("-" * 20)