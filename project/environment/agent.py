# environment/agent.py

import math
import random
from .maze import Maze, CELL_WALL, CELL_GOAL # Імпортуємо Maze для перевірки типу

class Agent:
    """
    Клас, що представляє агента, керованого нейромережею,
    який рухається в лабіринті.
    """

    def __init__(self, agent_id: int, start_pos: tuple[int, int], config: dict):
        """
        Ініціалізує агента.

        Args:
            agent_id (int): Унікальний ідентифікатор агента.
            start_pos (tuple[int, int]): Початкова позиція (row, col).
            config (dict): Словник з конфігурацією (з config.py).
        """
        self.id = agent_id
        self.x = float(start_pos[1]) + 0.5
        self.y = float(start_pos[0]) + 0.5
        self.angle = random.uniform(0, 2 * math.pi)
        self.velocity = 0.0
        self.max_speed = config.get('agent_max_speed', config.get('AGENT_MAX_SPEED', 0.5)) # Додав fallback до config
        self.radius = 0.3

        self.num_rangefinders = config['NUM_RANGEFINDERS']
        self.rangefinder_angles_relative = [i * (2 * math.pi / self.num_rangefinders) for i in range(self.num_rangefinders)]
        self.rangefinder_max_dist = config['RANGEFINDER_MAX_DIST']
        self.num_radar_slices = config['NUM_RADAR_SLICES']
        self.radar_slice_angle = 2 * math.pi / self.num_radar_slices

        # Оновлення перевірки NUM_INPUTS (HeadX, HeadY, Vel = 3)
        expected_inputs = self.num_rangefinders + self.num_radar_slices + 3
        if config['NUM_INPUTS'] != expected_inputs:
             print(f"Warning: config['NUM_INPUTS'] ({config['NUM_INPUTS']}) doesn't match calculated inputs ({expected_inputs}) for Agent.")
             # config['NUM_INPUTS'] = expected_inputs # Можна примусово оновити

        self.rangefinder_readings = [1.0] * self.num_rangefinders
        self.radar_readings = [0.0] * self.num_radar_slices
        self.heading_vector = (math.cos(self.angle), math.sin(self.angle)) # Оновлено на основі кута
        self.current_velocity_reading = 0.0
        self.last_rangefinder_rays = []
        self.steps_taken = 0
        self.collided = False
        self.reached_goal = False
        self.min_dist_to_goal = float('inf')

    def _cast_ray(self, maze: Maze, angle_offset: float, max_dist: float) -> tuple[float, float, float, float, float]:
        """
        Кидає промінь з поточної позиції під заданим кутом відносно напрямку агента.
        Повертає: (start_x, start_y, end_x_on_maze, end_y_on_maze, actual_dist_to_obstacle)
        де end_x/y - це точка, де промінь зупинився (стіна або max_dist) в координатах лабіринту.
        """
        ray_angle_global = self.angle + angle_offset # Глобальний кут променя
        cos_a = math.cos(ray_angle_global)
        sin_a = math.sin(ray_angle_global)
        # Крок перевірки можна зробити меншим для більшої точності, але це вплине на продуктивність
        step_size = 0.1 # Крок перевірки вздовж променя

        # Початкова точка променя - це поточна позиція агента
        start_x_ray, start_y_ray = self.x, self.y
        
        current_dist = 0.0
        # Кінцева точка променя, яку ми будемо оновлювати
        ray_end_x, ray_end_y = start_x_ray, start_y_ray 

        while current_dist < max_dist:
            # Розраховуємо точку перевірки вздовж променя
            check_x = start_x_ray + cos_a * current_dist
            check_y = start_y_ray + sin_a * current_dist
            
            map_r, map_c = int(check_y), int(check_x)

            # Перевіряємо, чи точка перевірки все ще в межах лабіринту
            if not maze._is_valid(map_r, map_c):
                # Промінь вийшов за межі лабіринту. Зупиняємось на межі max_dist або на фактичній межі.
                # Кінцева точка - це остання валідна точка перед виходом за межі max_dist.
                ray_end_x = start_x_ray + cos_a * current_dist # Точка на промені
                ray_end_y = start_y_ray + sin_a * current_dist
                return start_x_ray, start_y_ray, ray_end_x, ray_end_y, current_dist

            # Перевіряємо на зіткнення зі стіною
            if maze.grid[map_r][map_c] == CELL_WALL:
                # Промінь вдарився в стіну.
                ray_end_x = start_x_ray + cos_a * current_dist # Точка на промені
                ray_end_y = start_y_ray + sin_a * current_dist
                return start_x_ray, start_y_ray, ray_end_x, ray_end_y, current_dist
            
            current_dist += step_size

        # Якщо стіна не знайдена в межах max_dist, промінь йде на максимальну відстань
        ray_end_x = start_x_ray + cos_a * max_dist
        ray_end_y = start_y_ray + sin_a * max_dist
        return start_x_ray, start_y_ray, ray_end_x, ray_end_y, max_dist

    def get_sensor_readings(self, maze: Maze) -> list[float]:
        self.last_rangefinder_rays = [] # Очищаємо перед новим розрахунком

        # 1. Датчики відстані (Rangefinders)
        for i, angle_offset in enumerate(self.rangefinder_angles_relative):
            # Тепер _cast_ray повертає 5 значень, і ми їх коректно розпаковуємо
            start_x, start_y, end_x, end_y, actual_dist = self._cast_ray(maze, angle_offset, self.rangefinder_max_dist)
            
            # Зберігаємо нормовану відстань для нейромережі
            self.rangefinder_readings[i] = actual_dist / self.rangefinder_max_dist
            
            # Зберігаємо повні дані про промінь для візуалізації
            self.last_rangefinder_rays.append((start_x, start_y, end_x, end_y, actual_dist))

        # 2. Радар до цілі (Goal Radar)
        goal_pos = maze.goal_pos
        if goal_pos:
             goal_center_x = float(goal_pos[1]) + 0.5
             goal_center_y = float(goal_pos[0]) + 0.5
             dx_goal = goal_center_x - self.x
             dy_goal = goal_center_y - self.y
             angle_to_goal_global = math.atan2(dy_goal, dx_goal)
             relative_angle = (angle_to_goal_global - self.angle + math.pi) % (2 * math.pi) - math.pi
             self.radar_readings = [0.0] * self.num_radar_slices
             half_slice = self.radar_slice_angle / 2.0
             # Визначаємо, в який сектор потрапляє кут до цілі відносно напрямку агента
             # Нормалізуємо кут до цілі до діапазону [0, 2*pi) відносно "східного" напрямку (+X)
             # Потім нормалізуємо відносно напрямку агента, також до [0, 2*pi)
             # Кут агента self.angle вже в [0, 2*pi) або [-pi, pi) - треба узгодити
             # Припустимо, self.angle [-pi, pi), relative_angle [-pi, pi)
             
             # Перетворюємо relative_angle в діапазон [0, 2*pi) для простого розрахунку індексу
             positive_relative_angle = (relative_angle + 2 * math.pi) % (2 * math.pi)
             
             target_sector_index = int(positive_relative_angle / self.radar_slice_angle)
             # Перевірка, чи індекс не виходить за межі (мало б бути добре через %)
             target_sector_index = min(target_sector_index, self.num_radar_slices - 1)


             if 0 <= target_sector_index < self.num_radar_slices:
                 self.radar_readings[target_sector_index] = 1.0
        else:
             self.radar_readings = [0.0] * self.num_radar_slices

        self.heading_vector = (math.cos(self.angle), math.sin(self.angle))
        self.current_velocity_reading = self.velocity / self.max_speed if self.max_speed != 0 else 0.0 # Додав перевірку на 0

        sensor_data = []
        sensor_data.extend(self.rangefinder_readings)
        sensor_data.extend(self.radar_readings)
        sensor_data.extend(list(self.heading_vector))
        sensor_data.append(self.current_velocity_reading)

        return sensor_data

    def update(self, maze: Maze, network_outputs: list[float], dt: float = 0.5):
        """
        Оновлює стан агента (кут, швидкість, позиція) на основі виходів нейромережі.
        Враховує просту фізику та колізії зі стінами.
        Тепер приймає 4 виходи: [TurnL, TurnR, Accel, Brake].

        Args:
            maze (Maze): Об'єкт лабіринту для перевірки колізій.
            network_outputs (list[float]): Список з 4 вихідних значень з нейромережі.
                                           Порядок: [TurnL, TurnR, Accel, Brake]
            dt (float): Часовий крок симуляції (для фізики).
        """
        expected_outputs = 4
        if len(network_outputs) != expected_outputs: # Перевірка на 4 виходи
             print(f"Warning: Agent {self.id} received {len(network_outputs)} outputs, expected {expected_outputs}.")
             # Якщо кількість неправильна, використовуємо значення за замовчуванням (напр., нічого не робимо)
             # Або можна спробувати взяти перші 4, якщо їх більше? Краще нічого не робити.
             network_outputs = [0.5] * expected_outputs # Нейтральні значення

        # --- Інтерпретація 4 виходів ---
        # Припускаємо, що виходи в діапазоні [0, 1] (після sigmoid)
        # 0: Turn Left Signal
        # 1: Turn Right Signal
        # 2: Acceleration Signal
        # 3: Brake Signal
        turn_left_signal = network_outputs[0]
        turn_right_signal = network_outputs[1]
        accel_signal = network_outputs[2]
        brake_signal = network_outputs[3]

        # 1. Розрахунок зміни кута
        # Максимальна швидкість повороту залежить від dt
        max_turn_rate = math.pi / 2 * dt # Приклад: 90 градусів за 1 сек (якщо dt=1)
        turn_request = 0.0

        # Просте віднімання сигналів. 0.5 = нейтрально. > 0.5 = поворот.
        turn_strength_left = max(0.0, turn_left_signal - 0.5) * 2
        turn_strength_right = max(0.0, turn_right_signal - 0.5) * 2
        turn_request = (turn_strength_right - turn_strength_left) * max_turn_rate

        self.angle = (self.angle + turn_request) % (2 * math.pi)

        # 2. Розрахунок зміни швидкості
        accel_power = 0.2 * self.max_speed * dt # Макс. зміна швидкості за крок
        brake_power = 0.4 * self.max_speed * dt # Сила гальмування
        friction = 0.05 * dt # Коефіцієнт тертя

        # Прискорення, якщо сигнал > 0.5
        acceleration = max(0.0, accel_signal - 0.5) * 2 * accel_power
        # Гальмування, якщо сигнал > 0.5
        braking = max(0.0, brake_signal - 0.5) * 2 * brake_power

        self.velocity += acceleration
        self.velocity -= braking
        self.velocity *= (1.0 - friction) # Застосовуємо тертя

        # Обмежуємо швидкість
        self.velocity = max(0.0, min(self.max_speed, self.velocity))

        # 3. Розрахунок переміщення
        move_dist = self.velocity * dt
        dx = math.cos(self.angle) * move_dist
        dy = math.sin(self.angle) * move_dist
        new_x = self.x + dx
        new_y = self.y + dy

        # 4. Перевірка колізій
        target_r, target_c = int(new_y), int(new_x)

        self.collided = False # Скидаємо прапорець колізії
        if not maze.is_walkable(target_r, target_c):
            self.velocity = 0 # Зупинка при зіткненні
            self.collided = True
            # Не оновлюємо позицію
        else:
            # Рух можливий
            self.x = new_x
            self.y = new_y

        # 5. Оновлення стану для оцінки
        # self.steps_taken += 1 # Перенесено в main.py/evaluation_function
        goal_pos = maze.goal_pos
        if goal_pos:
            dist = math.hypot(self.x - (goal_pos[1] + 0.5), self.y - (goal_pos[0] + 0.5))
            self.min_dist_to_goal = min(self.min_dist_to_goal, dist)
            current_r, current_c = self.get_position_int()
            if current_r == goal_pos[0] and current_c == goal_pos[1]:
                self.reached_goal = True

    def get_position_int(self) -> tuple[int, int]:
         """Повертає цілочисельні координати (row, col) агента."""
         return (int(self.y), int(self.x))

    def reset(self, start_pos: tuple[int, int]):
        """Скидає стан агента до початкового."""
        self.x = float(start_pos[1]) + 0.5
        self.y = float(start_pos[0]) + 0.5
        self.angle = random.uniform(0, 2 * math.pi)
        self.velocity = 0.0
        self.rangefinder_readings = [1.0] * self.num_rangefinders
        self.radar_readings = [0.0] * self.num_radar_slices
        self.heading_vector = (math.cos(self.angle), math.sin(self.angle)) # Оновлюємо
        self.current_velocity_reading = 0.0
        self.steps_taken = 0
        self.collided = False
        self.reached_goal = False
        self.min_dist_to_goal = float('inf')