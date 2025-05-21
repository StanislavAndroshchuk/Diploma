# key_handlers.py - Обробка клавіатурних подій
class KeyboardManager:
    def __init__(self, app, circle_manager, ui_elements):
        self.app = app
        self.circle_manager = circle_manager
        self.ui_elements = ui_elements
    
    def on_key_press(self, event):
        """Головний обробник натискання клавіш"""
        # Отримуємо код клавіші
        key = event.char if hasattr(event, 'char') else event.keysym
        
        # Обробляємо числові клавіші для перемикання екранів
        if key in ('1', '2', '3', '4') and int(key) in self.app.frames:
            # Зберігаємо попередній екран для логування
            prev_frame = self.app.current_frame
            
            # Перемикаємо на вибраний екран
            self.app.switch_to_frame(int(key))
            
            print(f"Switched from Frame {prev_frame} to Frame {key}")
            return
        
        # Інші клавіші обробляємо лише якщо активний основний екран
        if self.app.current_frame != 1:
            return
        
        # Викликаємо відповідну функцію в залежності від натиснутої клавіші
        self._handle_specific_key(key.lower())
    
    def _handle_specific_key(self, key):
        """Обробка конкретних функціональних клавіш"""
        handlers = {
            'm': self._handle_m_key,
            'f': self._handle_f_key,
            'i': self._handle_i_key,
            's': self._handle_s_key
        }
        
        # Викликаємо відповідний обробник, якщо він є
        handler = handlers.get(key)
        if handler:
            handler()
    
    def _handle_m_key(self):
        """Обробник клавіші M - підсвічування мутованих кружечків"""
        print("M key pressed - highlighting mutated circles")
        self.circle_manager.highlight_mutated_circles(self.ui_elements['zones'])
    
    def _handle_f_key(self):
        """Обробник клавіші F - перемикання відображення кольорів fitness"""
        print("F key pressed - toggling fitness colors")
        self.circle_manager.toggle_fitness_colors(self.ui_elements['zones'])
    
    def _handle_i_key(self):
        """Обробник клавіші I - додавання нового виду"""
        print("I key pressed - adding new species")
        species_count = self.circle_manager.add_new_species()
        # Оновлюємо мітку з кількістю видів
        self.ui_elements['labels']['species_count'].config(text=f"Species count: {species_count}")
    
    def _handle_s_key(self):
        """Обробник клавіші S - призначення нових видів деяким кружечкам"""
        print("S key pressed - assigning new species to circles")
        self.circle_manager.assign_new_species(self.ui_elements['zones'])