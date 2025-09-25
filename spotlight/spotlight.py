
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import time

# --- Config ---
AI_ENDPOINT = "http://localhost:5001/api/chat"
CLEAR_HISTORY_ENDPOINT = "http://localhost:5001/api/clear_history"
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 220  # Will expand with content
BACKGROUND_COLOR = '#0f0f13'
FOREGROUND_COLOR = '#f0f0f0'
ACCENT_COLOR = '#6c5ce7'
ENTRY_BG = '#1a1a23'
DISABLED_COLOR = '#2a2a33'
FONT_FAMILY = 'Segoe UI'
WINDOW_OPACITY = 0.95

# --- API Functions ---
def get_ai_response(prompt, callback):
    def task():
        try:
            response = requests.post(
                AI_ENDPOINT,
                data={"message": prompt, "web_search": "true"}
            )
            result = response.json()['choices'][0]['message']['content']
        except Exception as e:
            result = f"Error: {str(e)}"
        callback(result)
    threading.Thread(target=task).start()

def clear_chat_history(callback):
    def task():
        try:
            response = requests.post(CLEAR_HISTORY_ENDPOINT)
            if response.status_code == 200:
                callback(True, response.json().get('message', 'History cleared successfully'))
            else:
                callback(False, f"Error: {response.text}")
        except Exception as e:
            callback(False, f"Connection error: {str(e)}")
    threading.Thread(target=task).start()

# --- UI Setup ---
root = tk.Tk()
root.overrideredirect(True)
root.attributes('-topmost', True)
root.attributes('-alpha', WINDOW_OPACITY)
root.configure(bg=BACKGROUND_COLOR)

# Position window
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_pos = screen_width - WINDOW_WIDTH - 20
y_pos = 40
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")

# --- Styles ---
style = ttk.Style()
style.theme_use('clam')

style.configure("TEntry",
                foreground=FOREGROUND_COLOR,
                background=ENTRY_BG,
                fieldbackground=ENTRY_BG,
                borderwidth=0,
                insertwidth=1,
                insertcolor=ACCENT_COLOR,
                font=(FONT_FAMILY, 12),
                padding=(12, 10))

style.map("TEntry",
          fieldbackground=[('readonly', DISABLED_COLOR)],
          foreground=[('readonly', '#666666')])

style.configure("TLabel",
                background=BACKGROUND_COLOR,
                foreground=FOREGROUND_COLOR,
                font=(FONT_FAMILY, 11),
                padding=(0, 5))

style.configure("Welcome.TLabel",
                font=(FONT_FAMILY, 11, 'bold'),
                foreground=ACCENT_COLOR,
                background=BACKGROUND_COLOR)

style.configure("Clear.TButton",
                background=BACKGROUND_COLOR,
                foreground="#888888",  # Less prominent color
                borderwidth=0,
                font=(FONT_FAMILY, 9),  # Smaller font
                padding=(5, 2))

style.map("Clear.TButton",
          foreground=[('active', '#ff5555')],  # Red when hovered
          background=[('active', BACKGROUND_COLOR)])

# --- Main Container ---
container = tk.Frame(root, bg=BACKGROUND_COLOR)
container.pack(fill='both', expand=True, padx=0, pady=0)

# --- Title Bar ---
title_bar = tk.Frame(container, bg=BACKGROUND_COLOR, height=30)
title_bar.pack(fill='x')

def move_window(event):
    root.geometry(f'+{event.x_root}+{event.y_root}')

title_bar.bind('<B1-Motion>', move_window)

# Close Button
def close_app(event=None):
    root.destroy()

close_btn = tk.Label(title_bar, 
                    text='×', 
                    bg=BACKGROUND_COLOR, 
                    fg="#888",
                    font=(FONT_FAMILY, 16), 
                    padx=10, 
                    cursor="hand2")
close_btn.pack(side='right')
close_btn.bind("<Button-1>", close_app)
close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ff5555"))
close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#888"))

# --- Input Field ---
entry_frame = tk.Frame(container, bg=ENTRY_BG, padx=1, pady=1)
entry_frame.pack(fill='x', padx=15, pady=(0, 10))

input_var = tk.StringVar()
entry = ttk.Entry(entry_frame, textvariable=input_var, style="TEntry")
entry.pack(fill='x', ipady=4)
entry.focus()

# --- Loading Animation ---
loading_canvas = tk.Canvas(container, bg=BACKGROUND_COLOR, height=20, highlightthickness=0)
loading_canvas.pack(fill='x', padx=15, pady=(5, 0))

def create_loading_animation():
    loading_canvas.delete("all")
    width = loading_canvas.winfo_width()
    if width < 10:
        return
    
    dot_count = 5
    dot_size = 6
    spacing = 10
    total_width = (dot_count * dot_size) + ((dot_count - 1) * spacing)
    start_x = (width - total_width) // 2
    
    for i in range(dot_count):
        x = start_x + i * (dot_size + spacing)
        loading_canvas.create_oval(x, 5, x+dot_size, 5+dot_size, 
                                 fill=ACCENT_COLOR, tags=f"dot{i}", state='hidden')

loading_canvas.bind("<Configure>", lambda e: create_loading_animation())

def animate_loading():
    global animation_phase
    if not is_thinking:
        loading_canvas.delete("all")
        return
    
    for i in range(5):
        state = 'normal' if i == animation_phase % 5 else 'hidden'
        loading_canvas.itemconfig(f"dot{i}", state=state)
    
    animation_phase += 1
    if is_thinking:
        root.after(150, animate_loading)

# --- Output Area ---
output_frame = tk.Frame(container, bg=BACKGROUND_COLOR)
output_frame.pack(fill='x', padx=15, pady=(0, 5))  # Reduced bottom padding

welcome_message = """Hello, I'm SeeleAI. How can I assist you today?

I can help with:
• Coding questions in multiple languages
• File analysis (terminal access/code files)
• Web searches (enable below)
• Terminal Access
• Creative writing and brainstorming"""

welcome_heading = ttk.Label(output_frame, 
                           text="SeeleAI Assistant", 
                           style="Welcome.TLabel")
welcome_heading.pack(fill='x', pady=(0, 5))

output_label = ttk.Label(output_frame, 
                        text=welcome_message, 
                        wraplength=WINDOW_WIDTH - 40, 
                        justify='left', 
                        style="TLabel")
output_label.pack(fill='x')

# --- Clear History Button (Bottom Left) ---
button_frame = tk.Frame(container, bg=BACKGROUND_COLOR)
button_frame.pack(fill='x', padx=5, pady=(10, 0))

def on_clear_history():
    # Confirm before clearing
    if messagebox.askyesno("Clear History", 
                          "Are you sure you want to clear the chat history?",
                          parent=root):
        def callback(success, message):
            if success:
                output_label.config(text=welcome_message)
                welcome_heading.config(text="SeeleAI Assistant")
                messagebox.showinfo("Success", message, parent=root)
                adjust_window_height()
            else:
                messagebox.showerror("Error", message, parent=root)
        
        clear_chat_history(callback)

clear_btn = ttk.Button(button_frame,
                      text="Clear History",
                      command=on_clear_history,
                      style="Clear.TButton")
clear_btn.pack(side='left')

def adjust_window_height():
    root.update_idletasks()
    text_height = output_label.winfo_reqheight() + welcome_heading.winfo_reqheight()
    new_height = max(220, 160 + text_height)
    root.geometry(f"{WINDOW_WIDTH}x{new_height}")

# --- State Management ---
is_thinking = False
animation_phase = 0

def set_thinking_state(thinking):
    global is_thinking
    is_thinking = thinking
    
    if thinking:
        entry.configure(style='Disabled.TEntry', state='readonly')
        welcome_heading.config(text="Thinking...")
        create_loading_animation()
        animate_loading()
    else:
        entry.configure(style='TEntry', state='normal')
        welcome_heading.config(text="SeeleAI Response")
        loading_canvas.delete("all")

style.configure("Disabled.TEntry",
                fieldbackground=DISABLED_COLOR,
                foreground='#666666',
                background=DISABLED_COLOR)

# --- Event Handlers ---
def on_enter(event=None):
    query = input_var.get().strip()
    if query and not is_thinking:
        input_var.set("")
        output_label.config(text="")
        set_thinking_state(True)
        get_ai_response(query, show_response)

def show_response(response_text):
    set_thinking_state(False)
    output_label.config(text=response_text)
    adjust_window_height()

# --- Bindings ---
entry.bind("<Return>", on_enter)
root.bind("<Escape>", close_app)

# --- Initial Setup ---
adjust_window_height()

# --- Run ---
root.mainloop()