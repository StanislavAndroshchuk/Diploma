# ui_components.py - Компоненти інтерфейсу користувача
from tkinter import Frame, Label, CENTER, W, E, LEFT
from utils import rgbtohex

def create_frames(main_container):
    """Створює фрейми для всіх екранів"""
    frames = {}
    
    # Екран 1 - Наш основний інтерфейс з зонами A і B
    frames[1] = Frame(main_container, bg=rgbtohex(r=34, g=34, b=34))
    
    # Екран 2 - Простий екран з заголовком та іншим вмістом
    frames[2] = Frame(main_container, bg=rgbtohex(r=44, g=44, b=54))
    
    # Екран 3 - Ще один екран з іншим кольором
    frames[3] = Frame(main_container, bg=rgbtohex(r=54, g=44, b=44))
    
    # Екран 4 - І ще один екран
    frames[4] = Frame(main_container, bg=rgbtohex(r=44, g=54, b=44))
    
    return frames

def setup_screen_layouts(frames, circle_manager, fonts):
    """Налаштовує макети для всіх екранів"""
    # Створюємо UI компоненти для всіх екранів
    ui_elements = {
        'labels': {},
        'zones': {}
    }
    
    # Налаштування Екрану 1 (наш основний інтерфейс з зонами)
    setup_main_screen(frames[1], ui_elements, circle_manager, fonts)
    
    # Налаштування Екрану 2
    setup_statistics_screen(frames[2], ui_elements, fonts)
    
    # Налаштування Екрану 3
    setup_settings_screen(frames[3], ui_elements, fonts)
    
    # Налаштування Екрану 4
    setup_help_screen(frames[4], ui_elements, fonts)
    
    # Додаємо підказку про повернення на головний екран для всіх додаткових екранів
    for frame_num in [2, 3, 4]:
        return_hint = Label(
            frames[frame_num], 
            text="Press '1' to return to main screen", 
            bg=frames[frame_num]['bg'], 
            fg='white', 
            font=fonts['info']
        )
        return_hint.place(relx=0.5, rely=0.9, anchor=CENTER)
        ui_elements['labels'][f'return_hint_{frame_num}'] = return_hint
    
    return ui_elements

def setup_main_screen(frame, ui_elements, circle_manager, fonts):
    """Налаштовує основний екран (Екран 1) з зонами A і B"""
    # Створюємо головні зони A і B на Екрані 1
    zoneA = Frame(frame, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
    zoneB = Frame(frame, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
    
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
    
    # Зберігаємо зони для подальшого використання
    ui_elements['zones'] = {
        'zoneA': zoneA,
        'zoneB': zoneB,
        'zoneA_top': zoneA_top,
        'zoneA_bottom': zoneA_bottom,
        'zoneB_top': zoneB_top,
        'zoneB_bottom': zoneB_bottom
    }
    
    # Створюємо мітку для відображення ID кружечка в Zone B TOP
    circle_id_label = Label(
        zoneB_top, 
        text="Circle: None", 
        bg=rgbtohex(r=34, g=34, b=34), 
        fg='white', 
        font=fonts['info']
    )
    circle_id_label.place(relx=0.5, rely=0.3, anchor=CENTER)
    ui_elements['labels']['circle_id'] = circle_id_label
    
    # Додаємо мітку для відображення значення fitness
    fitness_label = Label(
        zoneB_top,
        text="Fitness: None",
        bg=rgbtohex(r=34, g=34, b=34),
        fg='white',
        font=fonts['info']
    )
    fitness_label.place(relx=0.5, rely=0.45, anchor=CENTER)
    ui_elements['labels']['fitness'] = fitness_label
    
    # Додаємо мітку для відображення species
    species_label = Label(
        zoneB_top,
        text="Species: Default",
        bg=rgbtohex(r=34, g=34, b=34),
        fg='white',
        font=fonts['info']
    )
    species_label.place(relx=0.5, rely=0.6, anchor=CENTER)
    ui_elements['labels']['species'] = species_label
    
    # Додаємо мітку для відображення поточної кількості видів
    species_count_label = Label(
        zoneB_bottom,
        text="Species count: 1",
        bg=rgbtohex(r=34, g=34, b=34),
        fg='white',
        font=fonts['info']
    )
    species_count_label.place(relx=0.5, rely=0.3, anchor=CENTER)
    ui_elements['labels']['species_count'] = species_count_label
    
    # Додаємо підказку про гарячі клавіші в Zone B Bottom
    key_hint_label = Label(
        zoneB_bottom, 
        text="M - highlight mutated\nF - show fitness colors\nI - add new species\nS - assign new species\n1-4 - switch screens", 
        bg=rgbtohex(r=34, g=34, b=34), 
        fg='white', 
        font=fonts['info'],
        justify=LEFT
    )
    key_hint_label.place(relx=0.5, rely=0.6, anchor=CENTER)
    ui_elements['labels']['key_hint'] = key_hint_label
    
    # Створюємо контейнер для заголовків з вертикальним центруванням на Екрані 1
    header_container = Frame(zoneA_top, bg=rgbtohex(r=34, g=34, b=34))
    header_container.place(relwidth=1.0, relheight=1.0)
    
    # Додаємо заголовки
    title_zoneA_left = Label(
        header_container, 
        text="Generation 001", 
        bg=rgbtohex(r=34, g=34, b=34), 
        fg='white', 
        font=fonts['title']
    )
    title_zoneA_left.place(relx=0.05, rely=0.5, anchor=W)  # Центровано по вертикалі
    ui_elements['labels']['title_left'] = title_zoneA_left
    
    title_zoneA_right = Label(
        header_container, 
        text="Transition", 
        bg=rgbtohex(r=34, g=34, b=34), 
        fg='white', 
        font=fonts['subtitle']
    )
    title_zoneA_right.place(relx=0.9, rely=0.5, anchor=E)  # Центровано по вертикалі
    ui_elements['labels']['title_right'] = title_zoneA_right
    
    # Встановлюємо обробник кліку на кружечок
    circle_manager.set_click_handler(lambda circle_data: update_circle_info(ui_elements, circle_data, circle_manager))
    
    return ui_elements
def update_circle_info(ui_elements, circle_data, circle_manager):
    """Оновлює інформацію про кружечок в UI"""
    circle_id = circle_data['id']
    fitness = circle_data['fitness']
    species_id = circle_data['species']
    species_name = circle_manager.species_list.get(species_id, "Unknown")
    
    # Оновлюємо мітки з інформацією
    ui_elements['labels']['circle_id'].config(text=f"Circle: {circle_id}")
    ui_elements['labels']['fitness'].config(text=f"Fitness: {fitness}")
    ui_elements['labels']['species'].config(text=f"Species: {species_name}")

def setup_statistics_screen(frame, ui_elements, fonts):
    """Налаштовує екран статистики (Екран 2)"""
    frame2_title = Label(
        frame, 
        text="Screen 2 - Statistics", 
        bg=rgbtohex(r=44, g=44, b=54), 
        fg='white', 
        font=fonts['title']
    )
    frame2_title.place(relx=0.5, rely=0.1, anchor=CENTER)
    ui_elements['labels']['stats_title'] = frame2_title
    
    frame2_content = Label(
        frame, 
        text="This screen can display statistics and analysis", 
        bg=rgbtohex(r=44, g=44, b=54), 
        fg='white', 
        font=fonts['info']
    )
    frame2_content.place(relx=0.5, rely=0.2, anchor=CENTER)
    ui_elements['labels']['stats_content'] = frame2_content

def setup_settings_screen(frame, ui_elements, fonts):
    """Налаштовує екран налаштувань (Екран 3)"""
    frame3_title = Label(
        frame, 
        text="Screen 3 - Settings", 
        bg=rgbtohex(r=54, g=44, b=44), 
        fg='white', 
        font=fonts['title']
    )
    frame3_title.place(relx=0.5, rely=0.1, anchor=CENTER)
    ui_elements['labels']['settings_title'] = frame3_title
    
    frame3_content = Label(
        frame, 
        text="This screen can display application settings", 
        bg=rgbtohex(r=54, g=44, b=44), 
        fg='white', 
        font=fonts['info']
    )
    frame3_content.place(relx=0.5, rely=0.2, anchor=CENTER)
    ui_elements['labels']['settings_content'] = frame3_content

def setup_help_screen(frame, ui_elements, fonts):
    """Налаштовує екран довідки (Екран 4)"""
    frame4_title = Label(
        frame, 
        text="Screen 4 - Help", 
        bg=rgbtohex(r=44, g=54, b=44), 
        fg='white', 
        font=fonts['title']
    )
    frame4_title.place(relx=0.5, rely=0.1, anchor=CENTER)
    ui_elements['labels']['help_title'] = frame4_title
    
    frame4_content = Label(
        frame, 
        text="This screen can display help and documentation", 
        bg=rgbtohex(r=44, g=54, b=44), 
        fg='white', 
        font=fonts['info']
    )
    frame4_content.place(relx=0.5, rely=0.2, anchor=CENTER)
    ui_elements['labels']['help_content'] = frame4_content