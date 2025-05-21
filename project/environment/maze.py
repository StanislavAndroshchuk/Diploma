# environment/maze.py

import random
import math

# Константи для типів клітинок (можна винести в окремий файл або config)
CELL_PATH = 0
CELL_WALL = 1
CELL_START = 2
CELL_GOAL = 3
# Можна додати CELL_OBSTACLE за потреби

class Maze:
    """Клас для генерації та представлення 2D лабіринту."""

    def __init__(self, width: int, height: int, seed=None):
        """
        Ініціалізує та генерує лабіринт.

        Args:
            width (int): Ширина лабіринту (має бути непарним числом >= 5).
            height (int): Висота лабіринту (має бути непарним числом >= 5).
            seed (int, optional): Сід для генератора випадкових чисел.
                                  Defaults to None (випадковий сід).
        """
        # Генерація лабіринту коректно працює для непарних розмірів
        if width < 5 or height < 5 or width % 2 == 0 or height % 2 == 0:
            raise ValueError("Width and height must be odd integers >= 5 for Recursive Backtracking.")
        self.width = width
        self.height = height
        self.seed = seed
        self.grid = [[CELL_WALL for _ in range(width)] for _ in range(height)] # Початково всі стіни
        self.start_pos = None # Зберігатиметься як (row, col)
        self.goal_pos = None  # Зберігатиметься як (row, col)
        self.generate()

    def _is_valid(self, r: int, c: int) -> bool:
        """Перевіряє, чи знаходяться координати в межах лабіринту."""
        return 0 <= r < self.height and 0 <= c < self.width

    def _recursive_backtracking(self, r: int, c: int):
        """Допоміжний рекурсивний метод для генерації лабіринту."""
        # Позначаємо поточну клітинку як прохід
        self.grid[r][c] = CELL_PATH
        # Список можливих напрямків (сусіди через одну клітинку)
        neighbors = [(r - 2, c), (r + 2, c), (r, c - 2), (r, c + 2)]
        random.shuffle(neighbors) # Перемішуємо напрямки

        for nr, nc in neighbors:
            # Перевіряємо, чи сусід в межах лабіринту (непарні координати) і є стіною
            if self._is_valid(nr, nc) and self.grid[nr][nc] == CELL_WALL:
                # Пробиваємо стіну між поточною клітинкою та сусідом
                wall_r, wall_c = r + (nr - r) // 2, c + (nc - c) // 2
                if self._is_valid(wall_r, wall_c): # Додаткова перевірка для стіни
                    self.grid[wall_r][wall_c] = CELL_PATH
                    # Рекурсивно викликаємо для сусіда
                    self._recursive_backtracking(nr, nc)

    def generate(self):
        """Генерує новий лабіринт за допомогою Recursive Backtracking."""
        # Встановлюємо сід, якщо він заданий
        if self.seed is not None:
            random.seed(self.seed)
            # print(f"Generating maze with seed: {self.seed}") # Debug
        else:
             # Якщо сід не заданий, можна згенерувати випадковий і зберегти його
             self.seed = random.randint(0, 2**32 - 1)
             random.seed(self.seed)
             print(f"Generated random maze seed: {self.seed}") # Debug


        # Скидаємо сітку до початкового стану (всі стіни)
        self.grid = [[CELL_WALL for _ in range(self.width)] for _ in range(self.height)]

        # Починаємо генерацію з випадкової непарної стартової точки всередині
        start_r = random.randrange(1, self.height, 2)
        start_c = random.randrange(1, self.width, 2)
        self._recursive_backtracking(start_r, start_c)

        # Встановлюємо старт та фініш
        # Варіант 1: Фіксовані кути (але це проходи після генерації)
        self.start_pos = (1, 1)
        self.goal_pos = (self.height - 2, self.width - 2)

        # Переконуємося, що старт і фініш - це проходи (мають бути після генерації)
        # Якщо генератор міг їх не зачепити, примусово робимо проходами
        if self.grid[self.start_pos[0]][self.start_pos[1]] == CELL_WALL:
             self.grid[self.start_pos[0]][self.start_pos[1]] = CELL_PATH # Зробити прохідним
        if self.grid[self.goal_pos[0]][self.goal_pos[1]] == CELL_WALL:
             self.grid[self.goal_pos[0]][self.goal_pos[1]] = CELL_PATH # Зробити прохідним
             # Можливо, треба пробити шлях до фінішу, якщо він ізольований

        # Позначаємо типи клітинок
        self.grid[self.start_pos[0]][self.start_pos[1]] = CELL_START
        self.grid[self.goal_pos[0]][self.goal_pos[1]] = CELL_GOAL

        # Варіант 2: Випадкові проходи (складніше, але краще для різноманіття)
        # paths = []
        # for r in range(1, self.height - 1):
        #     for c in range(1, self.width - 1):
        #         if self.grid[r][c] == CELL_PATH:
        #             paths.append((r, c))
        # if len(paths) >= 2:
        #     self.start_pos = random.choice(paths)
        #     paths.remove(self.start_pos)
        #     self.goal_pos = random.choice(paths)
        #     self.grid[self.start_pos[0]][self.start_pos[1]] = CELL_START
        #     self.grid[self.goal_pos[0]][self.goal_pos[1]] = CELL_GOAL
        # else:
        #     print("Warning: Not enough path cells to place random start/goal.")
        #     # Fallback to fixed positions
        #     self.start_pos = (1, 1)
        #     self.goal_pos = (self.height - 2, self.width - 2)
        #     self.grid[1][1] = CELL_START
        #     self.grid[self.height - 2][self.width - 2] = CELL_GOAL


    def is_walkable(self, r: int, c: int) -> bool:
        """Перевіряє, чи є клітинка прохідною (не стіна)."""
        if self._is_valid(r, c):
            return self.grid[r][c] != CELL_WALL
        return False # За межами лабіринту - не прохідна

    def get_cell_type(self, r: int, c: int) -> int:
         """Повертає тип клітинки."""
         if self._is_valid(r, c):
             return self.grid[r][c]
         return CELL_WALL # Вважаємо стіною за межами

    def display(self):
        """Виводить лабіринт у консоль (для тестування)."""
        for r in range(self.height):
            row_str = ""
            for c in range(self.width):
                cell_type = self.grid[r][c]
                if cell_type == CELL_PATH:
                    row_str += "  "
                elif cell_type == CELL_WALL:
                    # Використовуємо символи Unicode для кращого вигляду стін
                    # row_str += "██"
                    # Або простіше:
                    row_str += "##"
                elif cell_type == CELL_START:
                    row_str += " S"
                elif cell_type == CELL_GOAL:
                    row_str += " G"
                else:
                    row_str += " ?" # Невідомий тип
            print(row_str)