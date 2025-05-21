# main.py - Головний файл програми
from tkinter import *
from tkinter import font as tkfont
import random
import time

# Перевіряємо наявність необхідних бібліотек
try:
    from PIL import Image, ImageTk, ImageDraw
    print("PIL успішно імпортовано")
    PIL_AVAILABLE = True
except ImportError:
    print("УВАГА: PIL не знайдено. Встановіть Pillow через pip install Pillow")
    PIL_AVAILABLE = False

# Імпорт модулів проекту
from utils import rgbtohex
from circle_manager import CircleManager, DEFAULT_SPECIES
from ui_components import create_frames, setup_screen_layouts
from key_handlers import KeyboardManager

class Application:
    def __init__(self, root):
        # Основне вікно
        self.root = root
        self.root.title("NEAT Visualization")
        self.root.geometry('1200x800')
        self.root.configure(bg=rgbtohex(r=34, g=34, b=34))
        
        # Перевіряємо наявність PIL
        if not PIL_AVAILABLE:
            self._show_pil_error()
            return
        
        # Створюємо кастомні шрифти
        self.create_fonts()
        
        # Створюємо головний контейнер
        self.main_container = Frame(self.root, bg=rgbtohex(r=34, g=34, b=34))
        self.main_container.place(relwidth=1.0, relheight=1.0, relx=0, rely=0)
        
        # Змінна для відстеження поточного активного екрану
        self.current_frame = 1
        
        # Створення рамок (екранів)
        self.frames = create_frames(self.main_container)
        
        # Менеджер кружечків (circles)
        self.circle_manager = CircleManager()
        
        # Налаштування UI компонентів для всіх екранів
        self.ui_elements = setup_screen_layouts(
            self.frames, 
            self.circle_manager, 
            fonts={
                'title': self.title_font,
                'subtitle': self.subtitle_font,
                'info': self.info_font,
                'button': self.button_font
            }
        )
        
        # Створюємо менеджер клавіатури
        self.keyboard_manager = KeyboardManager(
            self, 
            self.circle_manager, 
            self.ui_elements
        )
        
        # Прив'язуємо обробники подій
        self.bind_events()
        
        # Ініціалізуємо початковий стан програми
        self.initialize()
    
    def _show_pil_error(self):
        """Відображає повідомлення про помилку, якщо PIL не встановлено"""
        error_frame = Frame(self.root, bg=rgbtohex(r=44, g=44, b=44))
        error_frame.place(relwidth=1.0, relheight=1.0, relx=0, rely=0)
        
        error_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        
        error_label = Label(
            error_frame,
            text="PIL (Pillow) не встановлено!\n\nДля роботи програми необхідна бібліотека PIL (Pillow).\n\nВстановіть її командою:\npip install Pillow",
            bg=rgbtohex(r=44, g=44, b=44),
            fg='white',
            font=error_font,
            justify=CENTER
        )
        error_label.place(relx=0.5, rely=0.4, anchor=CENTER)
        
        exit_button = Button(
            error_frame,
            text="Закрити",
            bg=rgbtohex(r=64, g=105, b=224),
            fg='white',
            font=error_font,
            command=self.root.destroy
        )
        exit_button.place(relx=0.5, rely=0.6, anchor=CENTER, width=150, height=50)
    
    def create_fonts(self):
        """Створення шрифтів для UI"""
        self.title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        self.subtitle_font = tkfont.Font(family="Helvetica", size=24, weight="normal")
        self.info_font = tkfont.Font(family="Helvetica", size=16, weight="normal")
        self.button_font = tkfont.Font(family="Helvetica", size=14, weight="normal")
    
    def bind_events(self):
        """Прив'язка обробників подій"""
        # Обробник натискання клавіш
        self.root.bind('<KeyPress>', self.keyboard_manager.on_key_press)
        
        # Обробник зміни розміру вікна
        self.root.bind('<Configure>', self.on_resize)
        
        # Обробники для зон (якщо потрібно)
        for zone_name, zone in self.ui_elements['zones'].items():
            zone.bind("<Enter>", lambda event, z=zone_name: self.on_enter_zone(event, z))
    
    def on_resize(self, event=None):
        """Обробник зміни розміру вікна"""
        # Перевіряємо, чи розмір змінився для кореневого вікна
        if event and event.widget != self.root:
            return
            
        # Оновлюємо позиції кружечків, якщо ми на основному екрані
        if self.current_frame == 1:
            self.circle_manager.update_circles_positions(self.ui_elements['zones'])
    
    def on_enter_zone(self, event, zone_name):
        """Обробник входу курсора в зону"""
        print(f"You entered Zone {zone_name}")
    
    def switch_to_frame(self, frame_num):
        """Перемикання між екранами"""
        # Приховуємо всі фрейми
        for num, frame in self.frames.items():
            frame.place_forget()
        
        # Показуємо вибраний фрейм
        self.frames[frame_num].place(relwidth=1.0, relheight=1.0, relx=0, rely=0)
        
        self.current_frame = frame_num
        print(f"Switched to Frame {frame_num}")
    
    def initialize(self):
        """Початкова ініціалізація програми"""
        # Оновлюємо геометрію вікна перед додаванням кружечків
        self.root.update()
        
        # Створюємо кружечки
        num_circles = 150
        if num_circles > 0:
            self.circle_manager.create_circles(
                self.ui_elements['zones']['zoneA_bottom'], 
                'zoneA_bottom', 
                num_circles
            )
        
        # Показуємо початковий екран
        self.switch_to_frame(1)

# Точка входу
if __name__ == "__main__":
    root = Tk()
    app = Application(root)
    root.mainloop()