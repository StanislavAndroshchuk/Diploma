# circle_manager.py - Керування кружечками та їх властивостями
from tkinter import Canvas, NW
import random
import math
from PIL import Image, ImageTk, ImageDraw
from utils import rgbtohex, get_color_by_fitness, generate_fitness_value

# Дефолтне значення species
DEFAULT_SPECIES = 0

class CircleManager:
    def __init__(self):
        # Зберігаємо всі створені кружечки та їх ID
        self.circles_data = {
            'zoneA_bottom': [],
            'zoneB_top': [],
            'zoneB_bottom': []
        }
        
        # Лічильник для унікальних ID кружечків
        self.circle_id_counter = 0
        
        # Змінна для відстеження режиму відображення fitness
        self.show_fitness_colors = False
        
        # Значення для керування species
        self.species_list = {
            DEFAULT_SPECIES: "Default"  # Запис дефолтного виду
        }
        self.species_counter = 1  # Почнемо з 1 для нових видів (0 - дефолтний)
        
        # Обробник події для кліку на кружечок
        self.click_handler = None
        
        # Зберігаємо посилання на PIL зображення, щоб вони не знищувались збирачем сміття
        self.pil_images = {}
        
    def set_click_handler(self, handler):
        """Встановлює обробник кліку на кружечок"""
        self.click_handler = handler
        
    def on_circle_click(self, event, frame_name, circle_index):
        """Обробляє клік на кружечок"""
        circle_data = self.circles_data[frame_name][circle_index]
        circle_id = circle_data['id']
        mutated = "Yes" if circle_data['mutated'] else "No"
        fitness = circle_data['fitness']
        species_id = circle_data['species']
        species_name = self.species_list.get(species_id, "Unknown")
        
        print(f"Clicked on circle ID: {circle_id} in {frame_name}, Mutated: {mutated}, Fitness: {fitness}, Species: {species_name} (ID: {species_id})")
        
        # Викликаємо зовнішній обробник, якщо він заданий
        if self.click_handler:
            self.click_handler(circle_data)
    
    def create_smooth_circle_image(self, size, fill_color, outline_color, outline_width=1):
        """Створює гладке зображення кола з антиаліасингом за допомогою PIL"""
        # Збільшуємо розмір для кращої якості
        scale_factor = 4
        scaled_size = int(size * scale_factor)  # Переконуємось, що це ціле число
        
        # Створюємо прозоре зображення з запасом для обводки
        padding = int(outline_width * scale_factor)  # Переконуємось, що це ціле число
        img_size = (scaled_size * 2 + padding * 2, scaled_size * 2 + padding * 2)
        image = Image.new('RGBA', img_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Малюємо коло з обводкою
        if outline_width > 0:
            # Спочатку малюємо обводку (більше коло)
            draw.ellipse(
                (padding, padding, img_size[0]-padding, img_size[1]-padding),
                fill=outline_color,
                outline=None
            )
            
            # Потім малюємо основне коло (трохи менше)
            inner_padding = padding + int(outline_width * scale_factor)  # Переконуємось, що це ціле число
            draw.ellipse(
                (inner_padding, inner_padding, img_size[0]-inner_padding, img_size[1]-inner_padding),
                fill=fill_color,
                outline=None
            )
        else:
            # Малюємо просто коло
            draw.ellipse(
                (padding, padding, img_size[0]-padding, img_size[1]-padding),
                fill=fill_color,
                outline=None
            )
        
        # Зменшуємо до потрібного розміру з антиаліасингом
        final_size = (int(size * 2 + outline_width * 2), int(size * 2 + outline_width * 2))  # Переконуємось, що це ціле число
        image = image.resize(final_size, Image.LANCZOS)
        
        return image
    
    def create_smooth_ellipse_image(self, size, width_mod, height_mod, fill_color, outline_color, outline_width=1):
        """Створює гладке зображення еліпса з антиаліасингом за допомогою PIL"""
        # Збільшуємо розмір для кращої якості
        scale_factor = 4
        scaled_size = int(size * scale_factor)  # Переконуємось, що це ціле число
        
        # Враховуємо модифікатори для еліпса
        width = int(scaled_size * width_mod * 2)  # Переконуємось, що це ціле число
        height = int(scaled_size * height_mod * 2)  # Переконуємось, що це ціле число
        
        # Створюємо прозоре зображення з запасом для обводки
        padding = int(outline_width * scale_factor)  # Переконуємось, що це ціле число
        img_size = (width + padding * 2, height + padding * 2)
        image = Image.new('RGBA', img_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Малюємо еліпс з обводкою
        if outline_width > 0:
            # Спочатку малюємо обводку (більший еліпс)
            draw.ellipse(
                (padding, padding, img_size[0]-padding, img_size[1]-padding),
                fill=outline_color,
                outline=None
            )
            
            # Потім малюємо основний еліпс (трохи менший)
            inner_padding = padding + int(outline_width * scale_factor)  # Переконуємось, що це ціле число
            draw.ellipse(
                (inner_padding, inner_padding, img_size[0]-inner_padding, img_size[1]-inner_padding),
                fill=fill_color,
                outline=None
            )
        else:
            # Малюємо просто еліпс
            draw.ellipse(
                (padding, padding, img_size[0]-padding, img_size[1]-padding),
                fill=fill_color,
                outline=None
            )
        
        # Зменшуємо до потрібного розміру з антиаліасингом
        final_width = int(size * width_mod * 2 + outline_width * 2)  # Переконуємось, що це ціле число
        final_height = int(size * height_mod * 2 + outline_width * 2)  # Переконуємось, що це ціле число
        image = image.resize((final_width, final_height), Image.LANCZOS)
        
        return image
    
    def create_highlight_image(self, size, width_mod, height_mod, highlight_color, outline_width=2):
        """Створює зображення для підсвічування з антиаліасингом за допомогою PIL"""
        # Збільшуємо розмір для кращої якості
        scale_factor = 4
        scaled_size = int(size * scale_factor)  # Переконуємось, що це ціле число
        
        # Враховуємо модифікатори для еліпса і додаємо додатковий розмір для підсвічування
        extra_size = 3  # Додатковий розмір для підсвічування
        width = int(scaled_size * width_mod * 2) + int(extra_size * scale_factor * 2)  # Переконуємось, що це ціле число
        height = int(scaled_size * height_mod * 2) + int(extra_size * scale_factor * 2)  # Переконуємось, що це ціле число
        
        # Створюємо прозоре зображення
        img_size = (width, height)
        image = Image.new('RGBA', img_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Малюємо контур для підсвічування
        outline_width_scaled = int(outline_width * scale_factor)  # Переконуємось, що це ціле число
        draw.ellipse(
            (outline_width_scaled, outline_width_scaled, 
             img_size[0]-outline_width_scaled, img_size[1]-outline_width_scaled),
            fill=None,
            outline=highlight_color,
            width=outline_width_scaled
        )
        
        # Зменшуємо до потрібного розміру з антиаліасингом
        final_width = int(size * width_mod * 2) + int(extra_size * 2)  # Переконуємось, що це ціле число
        final_height = int(size * height_mod * 2) + int(extra_size * 2)  # Переконуємось, що це ціле число
        image = image.resize((final_width, final_height), Image.LANCZOS)
        
        return image
            
    def create_circles(self, frame, frame_name, num_circles, circle_size=12):
        """Створює кружечки у вказаному фреймі"""
        # Очищаємо фрейм від попередніх кружечків
        for widget in frame.winfo_children():
            if isinstance(widget, Canvas):
                widget.destroy()
        
        # Очищаємо старі дані про кружечки для цього фрейму
        self.circles_data[frame_name] = []
        
        # Очищаємо старі зображення для цього фрейму
        if frame_name in self.pil_images:
            self.pil_images[frame_name] = {}
        else:
            self.pil_images[frame_name] = {}
        
        # Отримуємо ширину та висоту фрейму
        frame.update()  # Оновлюємо геометрію фрейму
        width = frame.winfo_width()
        height = frame.winfo_height()
        
        # Створюємо Canvas для малювання кружечків
        canvas = Canvas(frame, bg=rgbtohex(r=34, g=34, b=34), highlightthickness=0)
        canvas.place(relwidth=1, relheight=1)
        
        # Створюємо вказану кількість кружечків
        for i in range(num_circles):
            # Генеруємо випадкові координати у відносних значеннях (0-1)
            rel_x = random.random()  # Відносна позиція X
            rel_y = random.random()  # Відносна позиція Y
            
            # Переводимо у пікселі для початкового розміщення
            x = int(rel_x * width)
            y = int(rel_y * height)
            
            # Обмежуємо координати, щоб кружечки не виходили за межі
            x = max(circle_size, min(width - circle_size, x))
            y = max(circle_size, min(height - circle_size, y))
            
            # Створюємо унікальний ID для кружечка
            circle_id = f"circle_{self.circle_id_counter}"
            self.circle_id_counter += 1
            
            # Визначаємо, чи кружечок мутований (з шансом 0.2 або 20%)
            is_mutated = random.random() < 0.2
            
            # Генеруємо значення fitness для кружечка
            fitness_value = generate_fitness_value()
            
            # Початковий колір кружечка
            fill_color = 'white'
            outline_color = 'black'
            
            # Створюємо PIL зображення кружечка з антиаліасингом
            pil_image = self.create_smooth_circle_image(
                circle_size, 
                fill_color, 
                outline_color, 
                outline_width=1.5
            )
            
            # Конвертуємо в PhotoImage для Tkinter
            tk_image = ImageTk.PhotoImage(pil_image)
            
            # Зберігаємо зображення, щоб воно не було знищене збирачем сміття
            self.pil_images[frame_name][circle_id] = {
                'circle': tk_image,
                'pil_circle': pil_image
            }
            
            # Розраховуємо позицію для розміщення зображення (центр кружечка)
            img_x = x - pil_image.width // 2
            img_y = y - pil_image.height // 2
            
            # Додаємо зображення на Canvas
            circle_obj = canvas.create_image(
                img_x, img_y,
                image=tk_image,
                anchor=NW,
                tags=(circle_id, "mutated" if is_mutated else "normal", "fitness", "species")
            )
            
            # Створюємо додатковий об'єкт для анімації підсвічування мутованих кружечків
            highlight_obj = None
            highlight_image = None
            if is_mutated:
                # Створюємо зображення для підсвічування
                highlight_pil = self.create_highlight_image(
                    circle_size,
                    1.0, 1.0,  # Для звичайного кола
                    rgbtohex(r=64, g=105, b=224),
                    outline_width=2
                )
                
                highlight_image = ImageTk.PhotoImage(highlight_pil)
                
                # Зберігаємо зображення підсвічування
                self.pil_images[frame_name][f"{circle_id}_highlight"] = {
                    'highlight': highlight_image,
                    'pil_highlight': highlight_pil
                }
                
                # Розраховуємо позицію для підсвічування
                highlight_x = x - highlight_pil.width // 2
                highlight_y = y - highlight_pil.height // 2
                
                # Додаємо підсвічування на Canvas (початково приховане)
                highlight_obj = canvas.create_image(
                    highlight_x, highlight_y,
                    image=highlight_image,
                    anchor=NW,
                    tags=("highlight", circle_id),
                    state="hidden"
                )
            
            # Зберігаємо дані про кружечок із відносними координатами та значенням fitness
            circle_data = {
                'id': circle_id,
                'canvas_id': circle_obj,
                'highlight_id': highlight_obj,
                'x': x,
                'y': y,
                'rel_x': rel_x,  # Зберігаємо відносні координати
                'rel_y': rel_y,  # Зберігаємо відносні координати
                'size': circle_size,
                'mutated': is_mutated,
                'fitness': fitness_value,  # Додаємо значення fitness
                'fitness_color': get_color_by_fitness(fitness_value),  # Зберігаємо колір на основі fitness
                'species': DEFAULT_SPECIES,  # Встановлюємо дефолтне значення species
                'width_mod': 1.0,  # Значення за замовчуванням
                'height_mod': 1.0  # Значення за замовчуванням
            }
            self.circles_data[frame_name].append(circle_data)
            
            # Додаємо обробник кліків для цього кружечка
            canvas.tag_bind(
                circle_id, 
                '<Button-1>', 
                lambda event, fn=frame_name, idx=i: self.on_circle_click(event, fn, idx)
            )
        
        return canvas

    def update_circle_shape(self, canvas, circle_data):
        """Оновлює форму кружечка в залежності від його species"""
        circle_id = circle_data['id']
        species_id = circle_data['species']
        circle_size = circle_data['size']
        x, y = circle_data['x'], circle_data['y']
        frame_name = None
        
        # Визначаємо, до якого фрейму належить кружечок
        for fname, circles in self.circles_data.items():
            for circle in circles:
                if circle['id'] == circle_id:
                    frame_name = fname
                    break
            if frame_name:
                break
                
        if not frame_name:
            return
        
        # Визначаємо модифікатори форми в залежності від виду
        width_mod = 1.0
        height_mod = 1.0
        
        if species_id != DEFAULT_SPECIES:
            # Для не-дефолтних видів змінюємо форму, роблячи еліпс замість кола
            
            # Створюємо псевдо-випадковий модифікатор на основі species_id
            shape_modifier = 0.7 + (species_id % 5) * 0.1  # Від 0.7 до 1.3
            
            # Вирішуємо, чи розтягувати по ширині або по висоті
            if species_id % 2 == 0:
                # Розтягуємо по ширині
                width_mod = shape_modifier * 1.3
                height_mod = 1.0 / shape_modifier
            else:
                # Розтягуємо по висоті
                width_mod = 1.0 / shape_modifier
                height_mod = shape_modifier * 1.3
        
        # Зберігаємо нові модифікатори в даних кружечка
        circle_data['width_mod'] = width_mod
        circle_data['height_mod'] = height_mod
        
        # Перевіряємо колір кружечка
        fill_color = 'white'
        if self.show_fitness_colors:
            fill_color = circle_data['fitness_color']
        
        # Створюємо нове зображення - коло або еліпс
        if species_id == DEFAULT_SPECIES:
            pil_image = self.create_smooth_circle_image(
                circle_size, 
                fill_color, 
                'black', 
                outline_width=1.5
            )
        else:
            pil_image = self.create_smooth_ellipse_image(
                circle_size, 
                width_mod, 
                height_mod, 
                fill_color, 
                'black', 
                outline_width=1.5
            )
        
        # Конвертуємо в PhotoImage для Tkinter
        tk_image = ImageTk.PhotoImage(pil_image)
        
        # Оновлюємо зображення в словнику
        self.pil_images[frame_name][circle_id] = {
            'circle': tk_image,
            'pil_circle': pil_image
        }
        
        # Розраховуємо позицію для розміщення зображення
        img_x = x - pil_image.width // 2
        img_y = y - pil_image.height // 2
        
        # Оновлюємо зображення на Canvas
        canvas.itemconfig(circle_data['canvas_id'], image=tk_image)
        canvas.coords(circle_data['canvas_id'], img_x, img_y)
        
        # Якщо є підсвічування, оновлюємо і його
        if circle_data['highlight_id'] is not None:
            # Створюємо нове зображення для підсвічування
            highlight_pil = self.create_highlight_image(
                circle_size,
                width_mod,
                height_mod,
                rgbtohex(r=64, g=105, b=224),
                outline_width=2
            )
            
            highlight_image = ImageTk.PhotoImage(highlight_pil)
            
            # Зберігаємо нове зображення підсвічування
            self.pil_images[frame_name][f"{circle_id}_highlight"] = {
                'highlight': highlight_image,
                'pil_highlight': highlight_pil
            }
            
            # Розраховуємо позицію для підсвічування
            highlight_x = x - highlight_pil.width // 2
            highlight_y = y - highlight_pil.height // 2
            
            # Оновлюємо підсвічування на Canvas
            canvas.itemconfig(circle_data['highlight_id'], image=highlight_image)
            canvas.coords(circle_data['highlight_id'], highlight_x, highlight_y)
    
    def update_circles_positions(self, zones):
        """Оновлює позиції всіх кружечків при зміні розміру вікна"""
        for frame_name, circles in self.circles_data.items():
            if not circles:
                continue
                
            # Знаходимо відповідний фрейм
            if frame_name not in zones:
                continue
                
            frame = zones[frame_name]
            
            # Знаходимо Canvas
            canvas = None
            for widget in frame.winfo_children():
                if isinstance(widget, Canvas):
                    canvas = widget
                    break
                    
            if not canvas:
                continue
                
            # Отримуємо нові розміри фрейму
            frame.update()
            width = frame.winfo_width()
            height = frame.winfo_height()
            
            # Оновлюємо позиції кружечків відповідно до нових розмірів
            for circle_data in circles:
                circle_size = circle_data['size']
                
                # Обчислюємо нові координати на основі відносних значень
                new_x = int(circle_data['rel_x'] * width)
                new_y = int(circle_data['rel_y'] * height)
                
                # Обмежуємо координати
                new_x = max(circle_size, min(width - circle_size, new_x))
                new_y = max(circle_size, min(height - circle_size, new_y))
                
                # Оновлюємо координати в даних
                circle_data['x'] = new_x
                circle_data['y'] = new_y
                
                # Оновлюємо форму і позицію кружечка
                self.update_circle_shape(canvas, circle_data)
    
    def highlight_mutated_circles(self, zones):
        """Підсвічує мутовані кружечки"""
        # Знаходимо всі мутовані кружечки в зоні A (Bottom)
        frame = zones.get('zoneA_bottom')
        if not frame:
            return
            
        canvas = None
        for widget in frame.winfo_children():
            if isinstance(widget, Canvas):
                canvas = widget
                break
        
        if canvas is None:
            return
        
        # Показуємо підсвічування для всіх мутованих кружечків
        mutated_count = 0
        for circle_data in self.circles_data['zoneA_bottom']:
            if circle_data['mutated'] and circle_data['highlight_id'] is not None:
                canvas.itemconfig(circle_data['highlight_id'], state="normal")
                mutated_count += 1
        
        print(f"Highlighting {mutated_count} mutated circles")
        
        # Запускаємо таймер для приховування підсвічування через 3 секунди
        canvas.after(3000, lambda: self.hide_highlights(canvas))
    
    def hide_highlights(self, canvas):
        """Приховує підсвічування мутованих кружечків"""
        canvas.itemconfig("highlight", state="hidden")
        print("Highlights hidden")
    
    def toggle_fitness_colors(self, zones):
        """Перемикає відображення кольорів на основі fitness"""
        self.show_fitness_colors = not self.show_fitness_colors
        
        # Знаходимо канвас в зоні A (Bottom)
        frame = zones.get('zoneA_bottom')
        if not frame:
            return
            
        canvas = None
        for widget in frame.winfo_children():
            if isinstance(widget, Canvas):
                canvas = widget
                break
        
        if canvas is None:
            return
        
        # Оновлюємо форму всіх кружечків (що також оновить їх колір)
        for circle_data in self.circles_data['zoneA_bottom']:
            self.update_circle_shape(canvas, circle_data)
        
        print(f"Fitness colors {'shown' if self.show_fitness_colors else 'hidden'}")
    
    def add_new_species(self):
        """Додає новий вид до списку видів"""
        # Додаємо новий вид до списку
        new_species_id = self.species_counter
        self.species_list[new_species_id] = f"Species_{new_species_id}"
        self.species_counter += 1
        
        # Виводимо інформацію в консоль
        print(f"Added new species: {self.species_list[new_species_id]} (ID: {new_species_id})")
        print(f"Current species list: {self.species_list}")
        
        return len(self.species_list)
    
    def assign_new_species(self, zones):
        """Призначає новий вид деяким кружечкам"""
        # Якщо немає додаткових видів крім дефолтного, нічого не робимо
        if len(self.species_list) <= 1:
            print("No additional species available to assign")
            return
        
        # Знаходимо канвас в зоні A (Bottom)
        frame = zones.get('zoneA_bottom')
        if not frame:
            return
            
        canvas = None
        for widget in frame.winfo_children():
            if isinstance(widget, Canvas):
                canvas = widget
                break
        
        if canvas is None:
            return
        
        # Готуємо список видів для призначення (без дефолтного)
        available_species = [sp_id for sp_id in self.species_list.keys() if sp_id != DEFAULT_SPECIES]
        
        # Змінюємо види для приблизно 10% кружечків
        circles_to_change = int(len(self.circles_data['zoneA_bottom']) * 0.1)
        changed_count = 0
        
        # Вибираємо випадкові кружечки для зміни виду
        selected_circles = random.sample(range(len(self.circles_data['zoneA_bottom'])), circles_to_change)
        
        for i in selected_circles:
            circle_data = self.circles_data['zoneA_bottom'][i]
            
            # Вибираємо випадковий вид зі списку доступних
            new_species_id = random.choice(available_species)
            
            # Якщо вид не змінився, пропускаємо
            if circle_data['species'] == new_species_id:
                continue
            
            # Змінюємо вид кружечка
            old_species = circle_data['species']
            circle_data['species'] = new_species_id
            changed_count += 1
            
            print(f"Circle {circle_data['id']} changed from {self.species_list[old_species]} to {self.species_list[new_species_id]}")
            
            # Оновлюємо форму кружечка відповідно до нового виду
            self.update_circle_shape(canvas, circle_data)
        
        print(f"Changed species for {changed_count} circles")
        
        return changed_count