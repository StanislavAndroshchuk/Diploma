# Import Module
from tkinter import *
from tkinter import font as tkfont
import random
import time

def rgbtohex(r,g,b):
    return f'#{r:02x}{g:02x}{b:02x}'

# Функція для обчислення кольору на основі значення fitness
def get_color_by_fitness(fitness_value):
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

# create root window
root = Tk()

# root window title and dimension
root.title("Testing GUI")

# Set geometry (widthxheight)
root.geometry('1200x800')
root.configure(bg=rgbtohex(r=34, g=34, b=34))  # Встановлюємо чорний фон

# Створюємо кастомні шрифти
title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
subtitle_font = tkfont.Font(family="Helvetica", size=24, weight="normal")
info_font = tkfont.Font(family="Helvetica", size=16, weight="normal")
button_font = tkfont.Font(family="Helvetica", size=14, weight="normal")

# Створюємо головний фрейм-контейнер, в якому будуть розміщені всі екрани
main_container = Frame(root, bg=rgbtohex(r=34, g=34, b=34))
main_container.place(relwidth=1.0, relheight=1.0, relx=0, rely=0)

# Створюємо 4 різні фрейми (екрани)
frames = {}

# Екран 1 - Наш основний інтерфейс з зонами A і B
frames[1] = Frame(main_container, bg=rgbtohex(r=34, g=34, b=34))

# Екран 2 - Простий екран з заголовком та іншим вмістом
frames[2] = Frame(main_container, bg=rgbtohex(r=44, g=44, b=54))

# Екран 3 - Ще один екран з іншим кольором
frames[3] = Frame(main_container, bg=rgbtohex(r=54, g=44, b=44))

# Екран 4 - І ще один екран
frames[4] = Frame(main_container, bg=rgbtohex(r=44, g=54, b=44))

# Змінна для відстеження поточного активного екрану
current_frame = 1

# Зберігаємо всі створені кружечки та їх ID
circles_data = {
    'zoneA_bottom': [],
    'zoneB_top': [],
    'zoneB_bottom': []
}

# Значення для керування species
DEFAULT_SPECIES = 0  # Дефолтне значення species
species_counter = 1  # Почнемо з 1 для нових видів (0 - дефолтний)
species_list = {
    DEFAULT_SPECIES: "Default"  # Запис дефолтного виду
}

# Прапорець для відстеження режиму відображення fitness
show_fitness_colors = False

# Лічильник для унікальних ID кружечків
circle_id_counter = 0

# Функція для перемикання між екранами
def switch_to_frame(frame_num):
    global current_frame
    
    # Приховуємо всі фрейми
    for num, frame in frames.items():
        frame.place_forget()
    
    # Показуємо вибраний фрейм
    frames[frame_num].place(relwidth=1.0, relheight=1.0, relx=0, rely=0)
    
    current_frame = frame_num
    print(f"Switched to Frame {frame_num}")

# Функція для генерації значення fitness для кружечка
def generate_fitness_value():
    # Генеруємо випадкове значення від -400 до 400
    return random.randint(-400, 400)

# Функція для обробки кліків на кружечку
def on_circle_click(event, frame_name, circle_index):
    circle_data = circles_data[frame_name][circle_index]
    circle_id = circle_data['id']
    mutated = "Yes" if circle_data['mutated'] else "No"
    fitness = circle_data['fitness']
    species_id = circle_data['species']
    species_name = species_list.get(species_id, "Unknown")
    
    print(f"Clicked on circle ID: {circle_id} in {frame_name}, Mutated: {mutated}, Fitness: {fitness}, Species: {species_name} (ID: {species_id})")
    
    # Оновлюємо текст міток в Zone B TOP
    circle_id_label.config(text=f"Circle: {circle_id}")
    fitness_label.config(text=f"Fitness: {fitness}")
    species_label.config(text=f"Species: {species_name}")

# Функція для оновлення форми кружечка в залежності від його species
def update_circle_shape(canvas, circle_data):
    circle_id = circle_data['canvas_id']
    species_id = circle_data['species']
    circle_size = circle_data['size']
    x, y = circle_data['x'], circle_data['y']
    
    # Якщо це дефолтний вид - залишаємо звичайний круг
    if species_id == DEFAULT_SPECIES:
        # Створюємо звичайний круг
        canvas.coords(
            circle_id,
            x - circle_size, y - circle_size,
            x + circle_size, y + circle_size
        )
    else:
        # Для не-дефолтних видів змінюємо форму, роблячи еліпс замість кола
        # Різні species матимуть різні співвідношення сторін еліпса
        
        # Використовуємо species_id для створення унікальної форми
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
        
        # Оновлюємо координати для еліпса
        canvas.coords(
            circle_id,
            x - circle_size * width_mod, y - circle_size * height_mod,
            x + circle_size * width_mod, y + circle_size * height_mod
        )

# Функція для створення кружечків у вибраному фреймі
def create_circles(frame, frame_name, num_circles, circle_size=12):
    global circle_id_counter
    
    # Очищаємо фрейм від попередніх кружечків
    for widget in frame.winfo_children():
        if isinstance(widget, Canvas):
            widget.destroy()
    
    # Очищаємо старі дані про кружечки для цього фрейму
    circles_data[frame_name] = []
    
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
        circle_id = f"circle_{circle_id_counter}"
        circle_id_counter += 1
        
        # Визначаємо, чи кружечок мутований (з шансом 0.2 або 20%)
        is_mutated = random.random() < 0.2
        
        # Генеруємо значення fitness для кружечка
        fitness_value = generate_fitness_value()
        
        # Початковий колір кружечка
        fill_color = 'white'
        outline_color = 'black'
        
        # Малюємо кружечок з тонким контуром того ж кольору для згладжування
        circle_obj = canvas.create_oval(
            x - circle_size, y - circle_size,
            x + circle_size, y + circle_size,
            fill=fill_color, outline=outline_color, width=1.5,
            tags=(circle_id, "mutated" if is_mutated else "normal", "fitness", "species")
        )
        
        # Створюємо додатковий об'єкт для анімації підсвічування мутованих кружечків
        highlight_obj = None
        if is_mutated:
            # Спочатку створюємо невидимий контур
            highlight_obj = canvas.create_oval(
                x - circle_size - 3, y - circle_size - 3,
                x + circle_size + 3, y + circle_size + 3,
                outline=rgbtohex(r=64, g=105, b=224), width=2,
                state="hidden", tags=("highlight", circle_id)
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
            'species': DEFAULT_SPECIES  # Встановлюємо дефолтне значення species
        }
        circles_data[frame_name].append(circle_data)
        
        # Додаємо обробник кліків для цього кружечка (використовуємо lambda з default args)
        canvas.tag_bind(circle_id, '<Button-1>', lambda event, fn=frame_name, idx=i: on_circle_click(event, fn, idx))
    
    return canvas

# Функція для оновлення позицій кружечків при зміні розміру вікна
def update_circles_positions(event=None):
    # Перевіряємо, чи активний наш основний екран
    if current_frame != 1:
        return
        
    for frame_name, circles in circles_data.items():
        if not circles:
            continue
            
        # Знаходимо відповідний фрейм та канвас
        frame = None
        if frame_name == 'zoneA_bottom':
            frame = zoneA_bottom
        elif frame_name == 'zoneB_top':
            frame = zoneB_top
        elif frame_name == 'zoneB_bottom':
            frame = zoneB_bottom
            
        if not frame:
            continue
            
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
            
            # Оновлюємо позицію кружечка відповідно до його species
            circle_data['x'] = new_x
            circle_data['y'] = new_y
            
            # Оновлюємо форму кружечка залежно від species
            update_circle_shape(canvas, circle_data)
            
            # Оновлюємо позицію підсвічування, якщо воно є
            if circle_data['highlight_id']:
                # Розмір підсвічування має враховувати можливу деформацію кружечка
                # Беремо максимальний радіус для гарантії
                max_size = circle_size * 1.5  # Приблизна оцінка максимального розміру
                canvas.coords(
                    circle_data['highlight_id'],
                    new_x - max_size, new_y - max_size,
                    new_x + max_size, new_y + max_size
                )

# Функція для анімації підсвічування мутованих кружечків
def highlight_mutated_circles():
    # Перевіряємо, чи активний наш основний екран
    if current_frame != 1:
        return
        
    # Знаходимо всі мутовані кружечки в зоні A (Bottom)
    canvas = None
    for widget in zoneA_bottom.winfo_children():
        if isinstance(widget, Canvas):
            canvas = widget
            break
    
    if canvas is None:
        return
    
    # Показуємо підсвічування для всіх мутованих кружечків
    mutated_count = 0
    for circle_data in circles_data['zoneA_bottom']:
        if circle_data['mutated'] and circle_data['highlight_id'] is not None:
            canvas.itemconfig(circle_data['highlight_id'], state="normal")
            mutated_count += 1
    
    print(f"Highlighting {mutated_count} mutated circles")
    
    # Оновлюємо вікно
    root.update()
    
    # Запускаємо таймер для приховування підсвічування через 3 секунди
    root.after(3000, hide_highlights, canvas)

# Функція для приховування підсвічування
def hide_highlights(canvas):
    canvas.itemconfig("highlight", state="hidden")
    print("Highlights hidden")

# Функція для перемикання відображення кольорів на основі fitness
def toggle_fitness_colors():
    # Перевіряємо, чи активний наш основний екран
    if current_frame != 1:
        return
        
    global show_fitness_colors
    show_fitness_colors = not show_fitness_colors
    
    # Знаходимо канвас в зоні A (Bottom)
    canvas = None
    for widget in zoneA_bottom.winfo_children():
        if isinstance(widget, Canvas):
            canvas = widget
            break
    
    if canvas is None:
        return
    
    # Змінюємо кольори всіх кружечків
    for circle_data in circles_data['zoneA_bottom']:
        if show_fitness_colors:
            # Відображаємо колір на основі fitness
            canvas.itemconfig(
                circle_data['canvas_id'],
                fill=circle_data['fitness_color']
            )
        else:
            # Повертаємо білий колір
            canvas.itemconfig(
                circle_data['canvas_id'],
                fill='white'
            )
    
    print(f"Fitness colors {'shown' if show_fitness_colors else 'hidden'}")

# Функція для додавання нового виду (species)
def add_new_species():
    # Перевіряємо, чи активний наш основний екран
    if current_frame != 1:
        return
        
    global species_counter
    
    # Додаємо новий вид до списку
    new_species_id = species_counter
    species_list[new_species_id] = f"Species_{new_species_id}"
    species_counter += 1
    
    # Виводимо інформацію в консоль
    print(f"Added new species: {species_list[new_species_id]} (ID: {new_species_id})")
    print(f"Current species list: {species_list}")
    
    # Оновлюємо мітку з кількістю видів
    species_count_label.config(text=f"Species count: {len(species_list)}")

# Функція для призначення нових видів деяким кружечкам
def assign_new_species():
    # Перевіряємо, чи активний наш основний екран
    if current_frame != 1:
        return
        
    # Якщо немає додаткових видів крім дефолтного, нічого не робимо
    if len(species_list) <= 1:
        print("No additional species available to assign")
        return
    
    # Знаходимо канвас в зоні A (Bottom)
    canvas = None
    for widget in zoneA_bottom.winfo_children():
        if isinstance(widget, Canvas):
            canvas = widget
            break
    
    if canvas is None:
        return
    
    # Готуємо список видів для призначення (без дефолтного)
    available_species = [sp_id for sp_id in species_list.keys() if sp_id != DEFAULT_SPECIES]
    
    # Змінюємо види для приблизно 10% кружечків
    circles_to_change = int(len(circles_data['zoneA_bottom']) * 0.1)
    changed_count = 0
    
    # Вибираємо випадкові кружечки для зміни виду
    selected_circles = random.sample(range(len(circles_data['zoneA_bottom'])), circles_to_change)
    
    for i in selected_circles:
        circle_data = circles_data['zoneA_bottom'][i]
        
        # Вибираємо випадковий вид зі списку доступних
        new_species_id = random.choice(available_species)
        
        # Якщо вид не змінився, пропускаємо
        if circle_data['species'] == new_species_id:
            continue
        
        # Змінюємо вид кружечка
        old_species = circle_data['species']
        circle_data['species'] = new_species_id
        changed_count += 1
        
        print(f"Circle {circle_data['id']} changed from {species_list[old_species]} to {species_list[new_species_id]}")
        
        # Оновлюємо форму кружечка відповідно до нового виду
        update_circle_shape(canvas, circle_data)
    
    print(f"Changed species for {changed_count} circles")

# Функція для обробки натискання клавіш
def on_key_press(event):
    global current_frame
    
    # Отримуємо код клавіші
    key = event.char if hasattr(event, 'char') else event.keysym
    
    # Обробляємо числові клавіші для перемикання екранів
    if key in ('1', '2', '3', '4') and int(key) in frames:
        # Зберігаємо попередній екран для логування
        prev_frame = current_frame
        
        # Перемикаємо на вибраний екран
        switch_to_frame(int(key))
        
        print(f"Switched from Frame {prev_frame} to Frame {key}")
        return
    
    # Інші клавіші обробляємо лише якщо активний основний екран
    if current_frame != 1:
        return
        
    # Обробляємо функціональні клавіші
    if key.lower() == 'm':
        print("M key pressed - highlighting mutated circles")
        highlight_mutated_circles()
    elif key.lower() == 'f':
        print("F key pressed - toggling fitness colors")
        toggle_fitness_colors()
    elif key.lower() == 'i':
        print("I key pressed - adding new species")
        add_new_species()
    elif key.lower() == 's':
        print("S key pressed - assigning new species to circles")
        assign_new_species()

# Налаштування Екрану 1 (наш основний інтерфейс з зонами)
# ---------------------------------------------------

# Створюємо головні зони A і B на Екрані 1
zoneA = Frame(frames[1], bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
zoneB = Frame(frames[1], bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)

# Розміщуємо зони A і B вертикально
zoneA.place(relwidth=0.75, relheight=1.0, relx=0, rely=0)  # Використовуємо всю висоту вікна
zoneB.place(relwidth=0.25, relheight=1.0, relx=0.75, rely=0)

# Розділяємо зону A на верхню і нижню частини
zoneA_top = Frame(zoneA, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
zoneA_bottom = Frame(zoneA, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=0)

# Розміщуємо підзони зони A
zoneA_top.place(relwidth=1.0, relheight=0.15, relx=0, rely=0)
zoneA_bottom.place(relwidth=1.0, relheight=0.85, relx=0, rely=0.15)

# Розділяємо зону B на верхню і нижню частини
zoneB_top = Frame(zoneB, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
zoneB_bottom = Frame(zoneB, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)

# Розміщуємо підзони зони B
zoneB_top.place(relwidth=1.0, relheight=0.5, relx=0, rely=0)
zoneB_bottom.place(relwidth=1.0, relheight=0.5, relx=0, rely=0.5)

# Створюємо мітку для відображення ID кружечка в Zone B TOP
circle_id_label = Label(
    zoneB_top, 
    text="Circle: None", 
    bg=rgbtohex(r=34, g=34, b=34), 
    fg='white', 
    font=info_font
)
circle_id_label.place(relx=0.5, rely=0.3, anchor=CENTER)

# Додаємо мітку для відображення значення fitness
fitness_label = Label(
    zoneB_top,
    text="Fitness: None",
    bg=rgbtohex(r=34, g=34, b=34),
    fg='white',
    font=info_font
)
fitness_label.place(relx=0.5, rely=0.45, anchor=CENTER)

# Додаємо мітку для відображення species
species_label = Label(
    zoneB_top,
    text="Species: Default",
    bg=rgbtohex(r=34, g=34, b=34),
    fg='white',
    font=info_font
)
species_label.place(relx=0.5, rely=0.6, anchor=CENTER)

# Додаємо мітку для відображення поточної кількості видів
species_count_label = Label(
    zoneB_bottom,
    text="Species count: 1",
    bg=rgbtohex(r=34, g=34, b=34),
    fg='white',
    font=info_font
)
species_count_label.place(relx=0.5, rely=0.3, anchor=CENTER)

# Додаємо підказку про гарячі клавіші в Zone B Bottom
key_hint_label = Label(
    zoneB_bottom, 
    text="M - highlight mutated\nF - show fitness colors\nI - add new species\nS - assign new species\n1-4 - switch screens", 
    bg=rgbtohex(r=34, g=34, b=34), 
    fg='white', 
    font=info_font,
    justify=LEFT
)
key_hint_label.place(relx=0.5, rely=0.6, anchor=CENTER)

# Створюємо контейнер для заголовків з вертикальним центруванням на Екрані 1
header_container = Frame(zoneA_top, bg=rgbtohex(r=34, g=34, b=34))
header_container.place(relwidth=1.0, relheight=1.0)

# Додаємо заголовки з новими шрифтами, вертикально центровані
title_zoneA_left = Label(header_container, text="Generation 001", bg=rgbtohex(r=34, g=34, b=34), fg='white', font=title_font)
title_zoneA_left.place(relx=0.05, rely=0.5, anchor=W)  # Центровано по вертикалі

title_zoneA_right = Label(header_container, text="Transition", bg=rgbtohex(r=34, g=34, b=34), fg='white', font=subtitle_font)
title_zoneA_right.place(relx=0.9, rely=0.5, anchor=E)  # Центровано по вертикалі

# Налаштування Екрану 2
# ---------------------------------------------------
frame2_title = Label(
    frames[2], 
    text="Screen 2 - Statistics", 
    bg=rgbtohex(r=44, g=44, b=54), 
    fg='white', 
    font=title_font
)
frame2_title.place(relx=0.5, rely=0.1, anchor=CENTER)

frame2_content = Label(
    frames[2], 
    text="This screen can display statistics and analysis", 
    bg=rgbtohex(r=44, g=44, b=54), 
    fg='white', 
    font=info_font
)
frame2_content.place(relx=0.5, rely=0.2, anchor=CENTER)

# Налаштування Екрану 3
# ---------------------------------------------------
frame3_title = Label(
    frames[3], 
    text="Screen 3 - Settings", 
    bg=rgbtohex(r=54, g=44, b=44), 
    fg='white', 
    font=title_font
)
frame3_title.place(relx=0.5, rely=0.1, anchor=CENTER)

frame3_content = Label(
    frames[3], 
    text="This screen can display application settings", 
    bg=rgbtohex(r=54, g=44, b=44), 
    fg='white', 
    font=info_font
)
frame3_content.place(relx=0.5, rely=0.2, anchor=CENTER)

# Налаштування Екрану 4
# ---------------------------------------------------
frame4_title = Label(
    frames[4], 
    text="Screen 4 - Help", 
    bg=rgbtohex(r=44, g=54, b=44), 
    fg='white', 
    font=title_font
)
frame4_title.place(relx=0.5, rely=0.1, anchor=CENTER)

frame4_content = Label(
    frames[4], 
    text="This screen can display help and documentation", 
    bg=rgbtohex(r=44, g=54, b=44), 
    fg='white', 
    font=info_font
)
frame4_content.place(relx=0.5, rely=0.2, anchor=CENTER)

# Додаємо підказку про повернення на головний екран для всіх додаткових екранів
for frame_num in [2, 3, 4]:
    return_hint = Label(
        frames[frame_num], 
        text="Press '1' to return to main screen", 
        bg=frames[frame_num]['bg'], 
        fg='white', 
        font=info_font
    )
    return_hint.place(relx=0.5, rely=0.9, anchor=CENTER)

# Додаємо обробник натискання клавіш для всього вікна
root.bind('<KeyPress>', on_key_press)

# Додаємо обробник зміни розміру вікна
root.bind('<Configure>', update_circles_positions)

# Функції для відстеження входу курсора у кожну зону
def on_enter_zone(event, Zone):
    print(f"You entered Zone {Zone}")

# Призначення обробників подій входу курсора для кожної зони
zoneA_top.bind("<Enter>", lambda event: on_enter_zone(event, "A Top"))
zoneA_bottom.bind("<Enter>", lambda event: on_enter_zone(event, "A Bottom"))
zoneB_top.bind("<Enter>", lambda event: on_enter_zone(event, "B Top"))
zoneB_bottom.bind("<Enter>", lambda event: on_enter_zone(event, "B Bottom"))

num_circles_zoneA_bottom = 150  # Кількість кружечків для Zone A (Bottom)

# Додаємо кружечки у відповідні фрейми
root.update()  # Оновлюємо геометрію вікна перед додаванням кружечків

# Додаємо кружечки у нижню частину зони A
if num_circles_zoneA_bottom > 0:
    create_circles(zoneA_bottom, 'zoneA_bottom', num_circles_zoneA_bottom)

# Показуємо початковий екран (Frame 1)
switch_to_frame(1)

# Execute Tkinter
root.mainloop()