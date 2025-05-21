import tkinter as tk
import time

def rgbtohex(r,g,b):
    return f'#{r:02x}{g:02x}{b:02x}'

class Presentation:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualization")
        root.configure(bg=rgbtohex(r=34, g=34, b=34))  
        self.root.geometry("800x600")
        
        # Розміри екрану
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Основний контейнер
        self.main_container = tk.Frame(root, bg=rgbtohex(r=34, g=34, b=34))
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Frame A
        self.frame_a = tk.Frame(self.main_container, bg=rgbtohex(r=34, g=34, b=34))
        self.frame_a.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Надпис Зона А
        self.zone_a_label = tk.Label(self.frame_a, text="Zone A", font=("Arial", 20), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        self.zone_a_label.place(x=20, y=20)
        
        # Прямокутник (буде картинка)
        self.image_frame = tk.Frame(self.frame_a, bg=rgbtohex(r=34, g=34, b=34), width=200, height=250, highlightbackground='white', highlightthickness=1, relief=tk.SOLID)
        self.image_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.image_label = tk.Label(self.image_frame, text="Image.png", bg=rgbtohex(r=34, g=34, b=34), fg="white")
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Frame B (виключений за дефолтом та БЕЗ контуру)
        self.frame_b = tk.Frame(self.main_container, bg=rgbtohex(r=34, g=34, b=34))
        
        # Надпис "Zone B"
        self.zone_b_label = tk.Label(self.frame_b, text="Zone B", font=("Arial", 20), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        
        # Текст в зоні B
        self.text_label = tk.Label(self.frame_b, text="Text", font=("Arial", 30), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        
        # Канвас для анімації розділової лінії (буде створений пізніше)
        self.separator_canvas = None
        
        # Прив'язка до клавіши H анімації
        self.root.bind("<KeyPress-h>", self.animate_transition)
        self.root.bind("<KeyPress-H>", self.animate_transition)
        
        # Відстежування курсора миші
        self.frame_a.bind("<Enter>", lambda e: print("Курсор в зоні A"))
        self.frame_b.bind("<Enter>", lambda e: print("Курсор в зоні B"))
        
        # Перевірка на стан анімації
        self.animation_in_progress = False
        self.frames_split = False

    def remove_separator(self):
        # Повністю видаляємо розділову лінію (не тільки очищуємо, а й знищуємо віджет)
        if self.separator_canvas:
            self.separator_canvas.delete("all")
            self.separator_canvas.destroy()
            self.separator_canvas = None

    def animate_separator_line(self):
        # Спочатку видаляємо стару лінію, якщо вона існує
        self.remove_separator()
        
        # Створюємо новий канвас для анімації розділової лінії
        border_x = 0.4 * self.root.winfo_width()
        self.separator_canvas = tk.Canvas(
            self.main_container,
            width=2,  # Ширина лінії - 2 пікселя
            height=self.root.winfo_height(),
            bg=rgbtohex(r=34, g=34, b=34),
            highlightthickness=0
        )
        self.separator_canvas.place(x=border_x-1, y=0)
        
        # Кількість точок у лінії (висота вікна / 10)
        num_points = int(self.root.winfo_height() / 10)
        
        # Анімація появи лінії через точки
        for i in range(num_points + 1):
            # Очищаємо канвас
            self.separator_canvas.delete("all")
            
            # Малюємо лінію до поточної точки
            segment_height = i * 10
            self.separator_canvas.create_line(
                1, 0, 1, segment_height, 
                fill="white", width=2
            )
            
            # Оновлюємо інтерфейс
            self.root.update()
            time.sleep(0.01)  # Затримка для анімації
        
        # Після завершення анімації лінії, показуємо вміст зони B
        self.zone_b_label.place(x=20, y=20)
        self.text_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def animate_transition(self, event):
        # Щоб анімація не запускалась знову, поки інша працює
        if self.animation_in_progress:
            return
            
        if not self.frames_split:
            # Прибираємо елементи з зони B перед анімацією
            self.zone_b_label.place_forget()
            self.text_label.place_forget()
            
            # Повністю видаляємо розділову лінію, якщо вона була
            self.remove_separator()
            
            self.animation_in_progress = True
            
            # Показати Frame B (без контуру!)
            self.frame_b.place(x=self.screen_width, y=0, relwidth=0.6, relheight=1)
            
            # Кількість кадрів анімації
            frames = 30
            # Загальна тривалість анімації (в секундах)
            duration = 0.5
            # Час затримки між кадрами
            delay = duration / frames
            
            # Обчислюємо крок зміни для кожного кадру
            a_width_step = (0.4 - 1.0) / frames
            b_x_step = (0.4 * self.root.winfo_width() - self.screen_width) / frames
            
            for i in range(frames + 1):
                # Оновлюємо положення і розмір Frame A
                a_width = 1.0 + a_width_step * i
                self.frame_a.place_configure(relwidth=a_width)
                
                # Обновлюємо положення Frame B
                b_x = self.screen_width + b_x_step * i
                self.frame_b.place_configure(x=b_x)
                
                # Обновлюємо інтерфейс
                self.root.update()
                time.sleep(delay)
            
            # Встановлюємо остаточні значення після анімації
            self.frame_a.place_configure(relwidth=0.4)
            self.frame_b.place_configure(x=0.4 * self.root.winfo_width())
            
            # Анімуємо появу розділової лінії
            self.animate_separator_line()
            
            self.animation_in_progress = False
            self.frames_split = True
        else:
            # Повернення до початкового стану
            self.animation_in_progress = True
            
            # Прибираємо елементи з зони B на час анімації
            self.zone_b_label.place_forget()
            self.text_label.place_forget()
            
            # Повністю видаляємо розділову лінію
            self.remove_separator()
            
            # Кількість кадрів анімації
            frames = 30
            # Загальна тривалість анімації (в секундах)
            duration = 0.5
            # Час затримки між кадрами
            delay = duration / frames
            
            # Обраховуємо крок зміни для кожного кадру
            a_width_step = (1.0 - 0.4) / frames
            b_x_step = (self.screen_width - 0.4 * self.root.winfo_width()) / frames
            
            for i in range(frames + 1):
                # Оновлюємо положення і розмір Frame A
                a_width = 0.4 + a_width_step * i
                self.frame_a.place_configure(relwidth=a_width)
                
                # Обновлюємо положення Frame B
                b_x = 0.4 * self.root.winfo_width() + b_x_step * i
                self.frame_b.place_configure(x=b_x)
                
                # Обновлюємо інтерфейс
                self.root.update()
                time.sleep(delay)
            
            # Встановлюємо остаточні значення після анімації
            self.frame_a.place_configure(relwidth=1.0)
            self.frame_b.place_configure(x=self.screen_width)
            
            # Остаточно переконуємось, що розділова лінія видалена
            self.remove_separator()
            
            self.animation_in_progress = False
            self.frames_split = False

if __name__ == "__main__":
    root = tk.Tk()
    app = Presentation(root)
    root.mainloop()