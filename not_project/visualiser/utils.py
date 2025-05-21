# utils.py - Утиліти та допоміжні функції
import random
from PIL import Image, ImageDraw

def rgbtohex(r, g, b):
    """Конвертує RGB значення в HEX формат кольору"""
    return f'#{r:02x}{g:02x}{b:02x}'

def hex_to_rgb(hex_color):
    """Конвертує HEX значення кольору в кортеж RGB"""
    hex_color = hex_color.strip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_color_by_fitness(fitness_value):
    """Обчислює колір на основі значення fitness"""
    # Обмежуємо значення fitness між -400 та 400
    fitness_value = max(-400, min(400, fitness_value))
    
    # Масштабуємо fitness до діапазону [0, 1]
    normalized = (fitness_value + 400) / 800
    
    # Обчислюємо RGB значення для плавного переходу від червоного до зеленого
    # Червоний: (255, 0, 0) -> Зелений: (0, 255, 0)
    r = int(255 * (1 - normalized))
    g = int(255 * normalized)
    b = 0
    
    return rgbtohex(r, g, b)

def generate_fitness_value():
    """Генерує випадкове значення fitness для кружечка"""
    return random.randint(-400, 400)

def create_image_with_transparency(width, height, background_color=None):
    """Створює прозоре зображення PIL з опційним фоновим кольором"""
    if background_color:
        # Якщо вказано фоновий колір, створюємо зображення з цим кольором
        if isinstance(background_color, str) and background_color.startswith('#'):
            # Конвертуємо HEX в RGB, якщо потрібно
            bg_color = hex_to_rgb(background_color)
            # Додаємо альфа-канал (255 для повної непрозорості)
            bg_color = (*bg_color, 255)
        else:
            bg_color = background_color
        
        image = Image.new('RGBA', (width, height), bg_color)
    else:
        # Створюємо повністю прозоре зображення
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    return image

def interpolate_color(color1, color2, factor):
    """Інтерполює між двома кольорами з вказаним фактором (0-1)"""
    if isinstance(color1, str) and color1.startswith('#'):
        color1 = hex_to_rgb(color1)
    if isinstance(color2, str) and color2.startswith('#'):
        color2 = hex_to_rgb(color2)
    
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    
    return (r, g, b)

def create_fitness_color_gradient():
    """Створює градієнт кольорів для відображення fitness"""
    # Кількість кроків у градієнті
    steps = 100
    gradient = []
    
    for i in range(steps + 1):
        # Фактор інтерполяції від 0 до 1
        factor = i / steps
        # Інтерполяція від червоного до зеленого
        color = interpolate_color((255, 0, 0), (0, 255, 0), factor)
        # Додаємо до градієнту
        gradient.append(color)
    
    return gradient