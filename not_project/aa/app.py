import tkinter as tk
from tkinter import ttk
import genome as neat_genome # Use alias to avoid conflict with Tkinter module name
from visualization import draw_network
import tkinter.scrolledtext as scrolledtext # For scrollable genotype text

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("NEAT Genome Visualizer")
        self.genome = None
        self.canvas_width = 600 # Adjusted width for left pane
        self.canvas_height = 600
        self.pack(expand=True, fill="both") # Allow frame to expand

        self.create_widgets()

    def create_widgets(self):
        # Create a Panedwindow to hold the two main sections
        self.paned_window = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill="both", padx=5, pady=5)

        # Left Frame for Visualization
        left_frame = ttk.Frame(self.paned_window, width=self.canvas_width)
        self.paned_window.add(left_frame, weight=1) # Give weight so it expands

        # Control Frame for Visualization
        viz_control_frame = ttk.Frame(left_frame)
        viz_control_frame.pack(pady=5)

        ttk.Label(viz_control_frame, text="Input Nodes:").grid(row=0, column=0, padx=5)
        self.input_nodes_entry = ttk.Entry(viz_control_frame, width=5)
        self.input_nodes_entry.insert(0, "2")
        self.input_nodes_entry.grid(row=0, column=1, padx=5)

        ttk.Label(viz_control_frame, text="Output Nodes:").grid(row=0, column=2, padx=5)
        self.output_nodes_entry = ttk.Entry(viz_control_frame, width=5)
        self.output_nodes_entry.insert(0, "1")
        self.output_nodes_entry.grid(row=0, column=3, padx=5)

        create_button = ttk.Button(viz_control_frame, text="Create Initial Network", command=self.create_initial_network)
        create_button.grid(row=0, column=4, padx=10)

        # Canvas for visualization
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(expand=True, fill="both")


        # Right Frame for Genotype Display and Mutations
        right_frame = ttk.Frame(self.paned_window, width=400) # Set a preferred width
        self.paned_window.add(right_frame, weight=0) # Don't give weight so it stays fixed (or give less weight)

        # Mutation Control Frame
        mutation_control_frame = ttk.LabelFrame(right_frame, text="Mutations")
        mutation_control_frame.pack(pady=10, padx=5, fill="x")

        mutate_conn_button = ttk.Button(mutation_control_frame, text="Mutate (Add Connection)", command=self.mutate_add_connection)
        mutate_conn_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        mutate_node_button = ttk.Button(mutation_control_frame, text="Mutate (Add Node)", command=self.mutate_add_node)
        mutate_node_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        mutate_weights_button = ttk.Button(mutation_control_frame, text="Mutate (Weights)", command=self.mutate_mutate_weights)
        mutate_weights_button.pack(side="left", padx=5, pady=5, expand=True, fill="x")


        # Genotype Display
        ttk.Label(right_frame, text="Genotype:").pack(pady=5)
        self.genotype_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=30) # Adjust width/height as needed
        self.genotype_text.pack(pady=5, padx=5, expand=True, fill="both")
        self.genotype_text.config(state='disabled') # Make read-only

        # Status label
        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(pady=5)

    def update_display(self):
        """Updates both the network visualization and the genotype text."""
        if self.genome:
            draw_network(self.genome, self.canvas, self.canvas.winfo_width(), self.canvas.winfo_height())
            genotype_string = self.genome.get_genotype_string()
            self.genotype_text.config(state='normal') # Enable editing to insert text
            self.genotype_text.delete('1.0', tk.END)
            self.genotype_text.insert(tk.END, genotype_string)
            self.genotype_text.config(state='disabled') # Disable editing
        else:
            self.canvas.delete("all")
            self.genotype_text.config(state='normal')
            self.genotype_text.delete('1.0', tk.END)
            self.genotype_text.config(state='disabled')


    def create_initial_network(self):
        try:
            num_inputs = int(self.input_nodes_entry.get())
            num_outputs = int(self.output_nodes_entry.get())
            if num_inputs <= 0 or num_outputs <= 0:
                self.status_label.config(text="Помилка: Кількість вузлів має бути додатною.")
                return
            self.genome = neat_genome.Genome()
            self.genome.create_initial_network(num_inputs, num_outputs)
            self.update_display()
            self.status_label.config(text=f"Створено початкову мережу: {num_inputs} вхідних, {num_outputs} вихідних вузлів.")
        except ValueError:
            self.status_label.config(text="Помилка: Невірний формат кількості вузлів.")

    def mutate_add_connection(self):
        if self.genome:
            success, message = self.genome.mutate_add_connection()
            if success:
                 self.update_display()
                 self.status_label.config(text=f"Мутація (додати зв'язок): {message}")
            else:
                 self.status_label.config(text=f"Мутація (додати зв'язок) не вдалася: {message}")

        else:
            self.status_label.config(text="Створіть мережу спочатку.")

    def mutate_add_node(self):
         if self.genome:
            success, message = self.genome.mutate_add_node()
            if success:
                 self.update_display()
                 self.status_label.config(text=f"Мутація (додати вузол): {message}")
            else:
                 self.status_label.config(text=f"Мутація (додати вузол) не вдалася: {message}")
         else:
             self.status_label.config(text="Створіть мережу спочатку.")

    def mutate_mutate_weights(self):
        if self.genome:
            # You can add inputs for probability and step later if needed
            success, message = self.genome.mutate_mutate_weights(probability=0.8, perturb_probability=0.9, step=0.1)
            if success:
                 self.update_display()
                 self.status_label.config(text=f"Мутація (ваги): {message}")
            else:
                 self.status_label.config(text=f"Мутація (ваги): {message}") # Message will say 0 weights changed if none were selected

        else:
            self.status_label.config(text="Створіть мережу спочатку.")


if __name__ == "__main__":
    root = tk.Tk()
    # Set a minimum size for the window
    root.geometry("1000x700")
    app = Application(master=root)
    app.mainloop()