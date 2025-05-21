import tkinter as tk
import time
import random
import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import NEAT modules
from neat.genome import Genome
from neat.visualization import draw_genome

def rgbtohex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

class Presentation:
    def __init__(self, root):
        self.root = root
        self.root.title("NEAT Visualization")
        root.configure(bg=rgbtohex(r=34, g=34, b=34))  
        self.root.geometry("800x600")
        
        # Screen dimensions
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Main container
        self.main_container = tk.Frame(root, bg=rgbtohex(r=34, g=34, b=34))
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Frame A
        self.frame_a = tk.Frame(self.main_container, bg=rgbtohex(r=34, g=34, b=34))
        self.frame_a.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Zone A label
        self.zone_a_label = tk.Label(self.frame_a, text="Zone A", font=("Arial", 20), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        self.zone_a_label.place(x=20, y=20)
        
        # Image frame
        self.image_frame = tk.Frame(self.frame_a, bg=rgbtohex(r=34, g=34, b=34), width=200, height=250, highlightbackground='white', highlightthickness=1, relief=tk.SOLID)
        self.image_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.image_label = tk.Label(self.image_frame, text="Image.png", bg=rgbtohex(r=34, g=34, b=34), fg="white")
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Frame B
        self.frame_b = tk.Frame(self.main_container, bg=rgbtohex(r=34, g=34, b=34))
        
        # Zone B label
        self.zone_b_label = tk.Label(self.frame_b, text="Zone B - Genotype", font=("Arial", 20), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        
        # Create the canvas for genome visualization
        self.genome_canvas = tk.Canvas(self.frame_b, bg=rgbtohex(r=34, g=34, b=34), highlightthickness=0)
        
        # Create sections for genome visualization
        self.node_genes_label = tk.Label(self.frame_b, text="Node Genes", font=("Arial", 16), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        self.node_genes_frame = tk.Frame(self.frame_b, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
        
        self.connection_genes_label = tk.Label(self.frame_b, text="Connection Genes", font=("Arial", 16), bg=rgbtohex(r=34, g=34, b=34), fg="white")
        self.connection_genes_frame = tk.Frame(self.frame_b, bg=rgbtohex(r=34, g=34, b=34), highlightbackground='white', highlightthickness=1)
        
        # Separator canvas
        self.separator_canvas = None
        
        # Key bindings
        self.root.bind("<KeyPress-h>", self.animate_transition)
        self.root.bind("<KeyPress-H>", self.animate_transition)
        self.root.bind("<KeyPress-m>", self.mutate_genome)
        self.root.bind("<KeyPress-M>", self.mutate_genome)
        
        # Mouse tracking
        self.frame_a.bind("<Enter>", lambda e: print("Cursor in zone A"))
        self.frame_b.bind("<Enter>", lambda e: print("Cursor in zone B"))
        
        # Animation state
        self.animation_in_progress = False
        self.frames_split = False
        
        # Create initial genome
        self.genome = Genome(1)
        self.genome.create_initial_minimal(4, 2)  # 4 inputs, 2 outputs
        
        # Initial genome visualization widgets
        self.node_widgets = []
        self.connection_widgets = []
        
        # Status label to show mutation info
        self.status_label = tk.Label(self.frame_b, text="Press 'M' to mutate the genome", 
                                    font=("Arial", 12), bg=rgbtohex(r=34, g=34, b=34), fg="yellow")

    def remove_separator(self):
        # Remove the separator line
        if self.separator_canvas:
            self.separator_canvas.delete("all")
            self.separator_canvas.destroy()
            self.separator_canvas = None

    def animate_separator_line(self):
        # Remove old line if exists
        self.remove_separator()
        
        # Create a new canvas for the separator line animation
        border_x = 0.4 * self.root.winfo_width()
        self.separator_canvas = tk.Canvas(
            self.main_container,
            width=2,
            height=self.root.winfo_height(),
            bg=rgbtohex(r=34, g=34, b=34),
            highlightthickness=0
        )
        self.separator_canvas.place(x=border_x-1, y=0)
        
        # Number of points in the line
        num_points = int(self.root.winfo_height() / 10)
        
        # Animate line appearance through points
        for i in range(num_points + 1):
            # Clear canvas
            self.separator_canvas.delete("all")
            
            # Draw line to current point
            segment_height = i * 10
            self.separator_canvas.create_line(
                1, 0, 1, segment_height, 
                fill="white", width=2
            )
            
            # Update interface
            self.root.update()
            time.sleep(0.01)  # Animation delay
        
        # After animation is complete, show Frame B content
        self.display_genome()

    def animate_transition(self, event):
        # Prevent animation from starting again while another is in progress
        if self.animation_in_progress:
            return
            
        if not self.frames_split:
            # Remove Frame B elements before animation
            self.hide_genome_display()
            
            # Remove separator line if it exists
            self.remove_separator()
            
            self.animation_in_progress = True
            
            # Show Frame B
            self.frame_b.place(x=self.screen_width, y=0, relwidth=0.6, relheight=1)
            
            # Animation frames
            frames = 30
            # Total animation duration (seconds)
            duration = 0.5
            # Delay between frames
            delay = duration / frames
            
            # Calculate step change for each frame
            a_width_step = (0.4 - 1.0) / frames
            b_x_step = (0.4 * self.root.winfo_width() - self.screen_width) / frames
            
            for i in range(frames + 1):
                # Update position and size of Frame A
                a_width = 1.0 + a_width_step * i
                self.frame_a.place_configure(relwidth=a_width)
                
                # Update position of Frame B
                b_x = self.screen_width + b_x_step * i
                self.frame_b.place_configure(x=b_x)
                
                # Update interface
                self.root.update()
                time.sleep(delay)
            
            # Set final values after animation
            self.frame_a.place_configure(relwidth=0.4)
            self.frame_b.place_configure(x=0.4 * self.root.winfo_width())
            
            # Animate separator line appearance
            self.animate_separator_line()
            
            self.animation_in_progress = False
            self.frames_split = True
        else:
            # Return to initial state
            self.animation_in_progress = True
            
            # Remove Frame B elements during animation
            self.hide_genome_display()
            
            # Remove separator line
            self.remove_separator()
            
            # Animation frames
            frames = 30
            # Total animation duration (seconds)
            duration = 0.5
            # Delay between frames
            delay = duration / frames
            
            # Calculate step change for each frame
            a_width_step = (1.0 - 0.4) / frames
            b_x_step = (self.screen_width - 0.4 * self.root.winfo_width()) / frames
            
            for i in range(frames + 1):
                # Update position and size of Frame A
                a_width = 0.4 + a_width_step * i
                self.frame_a.place_configure(relwidth=a_width)
                
                # Update position of Frame B
                b_x = 0.4 * self.root.winfo_width() + b_x_step * i
                self.frame_b.place_configure(x=b_x)
                
                # Update interface
                self.root.update()
                time.sleep(delay)
            
            # Set final values after animation
            self.frame_a.place_configure(relwidth=1.0)
            self.frame_b.place_configure(x=self.screen_width)
            
            # Make sure separator is removed
            self.remove_separator()
            
            self.animation_in_progress = False
            self.frames_split = False
    
    def mutate_genome(self, event=None):
        """Mutate the genome and update the visualization."""
        if not self.frames_split:
            return  # Only allow mutation when Frame B is visible
        
        # Apply mutation
        mutation_happened = self.genome.mutate()
        
        if mutation_happened:
            # Update status label
            self.status_label.config(text="Genome mutated! New structure displayed.")
            
            # Update visualization
            self.hide_genome_display()
            self.display_genome()
            
            # After 2 seconds, reset status text
            self.root.after(2000, lambda: self.status_label.config(text="Press 'M' to mutate the genome"))
        else:
            self.status_label.config(text="Mutation attempted but no changes made.")
            self.root.after(2000, lambda: self.status_label.config(text="Press 'M' to mutate the genome"))
    
    def hide_genome_display(self):
        """Hide all genome visualization elements."""
        self.zone_b_label.place_forget()
        self.genome_canvas.place_forget()
        self.node_genes_label.place_forget()
        self.node_genes_frame.place_forget()
        self.connection_genes_label.place_forget()
        self.connection_genes_frame.place_forget()
        self.status_label.place_forget()
        
        # Clear node and connection widgets
        for widget in self.node_widgets:
            widget.destroy()
        self.node_widgets = []
        
        for widget in self.connection_widgets:
            widget.destroy()
        self.connection_widgets = []
    
    def display_genome(self):
        """Display the genome in Frame B."""
        # Position labels and frames
        self.zone_b_label.place(x=20, y=20)
        
        # Position canvas for network visualization
        self.genome_canvas.configure(width=400, height=300)
        self.genome_canvas.place(x=20, y=60)
        
        # Draw the genome on the canvas
        draw_genome(self.genome_canvas, self.genome)
        
        # Position node genes section
        self.node_genes_label.place(x=20, y=370)
        self.node_genes_frame.place(x=20, y=400, width=400, height=100)
        
        # Position connection genes section
        # Continuing from the previous implementation

        self.connection_genes_label.place(x=20, y=510)
        self.connection_genes_frame.place(x=20, y=540, width=400, height=100)
        
        # Position status label
        self.status_label.place(x=20, y=650)
        
        # Clear previous widgets
        for widget in self.node_widgets:
            widget.destroy()
        self.node_widgets = []
        
        for widget in self.connection_widgets:
            widget.destroy()
        self.connection_widgets = []
        
        # Create node gene widgets
        self.create_node_gene_widgets()
        
        # Create connection gene widgets
        self.create_connection_gene_widgets()
    
    def create_node_gene_widgets(self):
        """Create widgets for displaying node genes."""
        # Sort nodes by ID
        sorted_nodes = sorted(self.genome.nodes.values(), key=lambda n: n.node_id)
        
        # Create a frame for each node
        for i, node in enumerate(sorted_nodes[:8]):  # Display max 8 nodes
            x_pos = (i % 4) * 100
            y_pos = (i // 4) * 50
            
            frame = tk.Frame(self.node_genes_frame, bg=rgbtohex(r=50, g=50, b=50), width=90, height=45)
            frame.place(x=x_pos, y=y_pos)
            self.node_widgets.append(frame)
            
            # Node type color
            from neat.node_gene import NodeGene
            if node.node_type == NodeGene.INPUT:  # INPUT
                color = "blue"
                type_text = "Input Layer"
            elif node.node_type == NodeGene.HIDDEN:  # HIDDEN
                color = "purple"
                type_text = "Hidden Layer"
            else:  # OUTPUT
                color = "orange"
                type_text = "Output Layer"
            
            # Node ID label
            id_label = tk.Label(frame, text=f"Node {node.node_id}", fg="white", bg=rgbtohex(r=50, g=50, b=50), font=("Arial", 8, "bold"))
            id_label.place(x=5, y=5)
            self.node_widgets.append(id_label)
            
            # Node type label
            type_label = tk.Label(frame, text=type_text, fg=color, bg=rgbtohex(r=50, g=50, b=50), font=("Arial", 8))
            type_label.place(x=5, y=25)
            self.node_widgets.append(type_label)
    
    def create_connection_gene_widgets(self):
        """Create widgets for displaying connection genes."""
        # Sort connections by innovation number
        sorted_connections = sorted(self.genome.connections.values(), key=lambda c: c.innovation)
        
        # Create a frame for each connection
        for i, conn in enumerate(sorted_connections[:8]):  # Display max 8 connections
            x_pos = (i % 4) * 100
            y_pos = (i // 4) * 50
            
            frame = tk.Frame(self.connection_genes_frame, bg=rgbtohex(r=50, g=50, b=50), width=90, height=45)
            frame.place(x=x_pos, y=y_pos)
            self.connection_widgets.append(frame)
            
            # Connection label
            conn_label = tk.Label(frame, text=f"In {conn.in_node}\nOut {conn.out_node}", fg="white", bg=rgbtohex(r=50, g=50, b=50), font=("Arial", 8))
            conn_label.place(x=5, y=5)
            self.connection_widgets.append(conn_label)
            
            # Weight label
            weight_color = "red" if conn.weight < 0 else "green"
            weight_label = tk.Label(frame, text=f"Weight: {conn.weight:.2f}", fg=weight_color, bg=rgbtohex(r=50, g=50, b=50), font=("Arial", 8))
            weight_label.place(x=5, y=25)
            self.connection_widgets.append(weight_label)
            
            # Enabled/Disabled status
            status_text = "Enabled" if conn.enabled else "DISABLED"
            status_color = "lime green" if conn.enabled else "red"
            status_label = tk.Label(frame, text=status_text, fg=status_color, bg=rgbtohex(r=50, g=50, b=50), font=("Arial", 7))
            status_label.place(x=40, y=5)
            self.connection_widgets.append(status_label)

if __name__ == "__main__":
    root = tk.Tk()
    app = Presentation(root)
    root.mainloop()