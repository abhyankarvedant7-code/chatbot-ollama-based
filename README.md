# chatbot-ollama-based
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label, StringVar, OptionMenu, Scrollbar
import shutil
import os
import chromadb
from functions import doc_loader, vector_creator, chat, load_saved_embedding

global content
content = None  
collection = None 

# Function to get saved embeddings
def get_saved_embeddings():
    if not os.path.exists("saved"):
        os.makedirs("saved")
    files = [f for f in os.listdir("saved") if f.endswith(".pkl")]
    return files

# Function to handle file upload
def upload_file():
    global content, collection

    send_button.config(state=tk.DISABLED)

    loading_window = Toplevel(window)
    loading_window.title("Uploading")
    loading_window.geometry("250x120")
    loading_window.configure(bg="#2C3E50")
    
    loading_label = Label(loading_window, text="Uploading your file...", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white")
    loading_label.pack(pady=30)
    
    file_types = [("PDF Files", "*.pdf")]
    file_path = filedialog.askopenfilename(filetypes=file_types)
    
    if file_path:
        file_name = os.path.basename(file_path)
        destination_dir = "uploads"
        
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        
        destination_path = os.path.join(destination_dir, file_name)
        
        try:
            shutil.copy(file_path, destination_path)
            loading_window.destroy()
            collection_name = file_name.split(".")[0]
            content = doc_loader(destination_path)
            collection = vector_creator(content, save_name=collection_name)
            add_message("Hi, how can I help you today?", sender="Bot")
            send_button.config(state=tk.NORMAL)

            
            refresh_dropdown()
        except Exception as e:
            loading_window.destroy()
            messagebox.showerror("File Upload", f"Failed to upload file: {str(e)}")
    else:
        loading_window.destroy()
        messagebox.showinfo("File Upload", "No file selected.")

# Function to refresh the dropdown options
def refresh_dropdown():
    files = get_saved_embeddings()
    dropdown_menu['menu'].delete(0, 'end')  
    if files:
        dropdown_var.set(files[0])  
        for file in files:
            dropdown_menu['menu'].add_command(label=file, command=lambda f=file: dropdown_var.set(f))
    else:
        dropdown_var.set("No saved embeddings")
        dropdown_menu['menu'].add_command(label="No saved embeddings", command=lambda: None)


# Function to load selected embedding
def load_embedding():
    global collection
    if collection:
        collection_name = "docs"  # The name of your collection
        client = chromadb.Client()
        client.delete_collection(name=collection_name)
        collection = None
    
    selected_file = dropdown_var.get()
    if selected_file and selected_file != "No saved embeddings":
        try:
            # Load the selected embedding
            collection = load_saved_embedding(selected_file)
            if collection:
                add_message("Embedding loaded successfully. You can now ask questions.", sender="Bot")
            else:
                add_message("Failed to load embedding. Collection is empty.", sender="Bot")
        except Exception as e:
            messagebox.showerror("Load Embedding", f"Failed to load embedding: {str(e)}")
    else:
        messagebox.showinfo("Load Embedding", "Please select a valid embedding to load.")

# Function to style buttons with hover effect
def style_button(button, hover_color="#34495E", original_color="#2C3E50"):
    def on_enter(event):
        button['bg'] = hover_color

    def on_leave(event):
        button['bg'] = original_color

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# GUI Setup
window = tk.Tk()
window.title("Ollama Chatbot")
window.geometry("800x700")
window.configure(bg="#ECF0F1")

# Title Section
title_label = tk.Label(window, text="Ollama Chatbot", font=("Helvetica", 16, "bold"), bg="#ECF0F1", fg="#2C3E50")
title_label.pack(pady=10)

# Dropdown and Buttons Section (in a single row)
dropdown_frame = tk.Frame(window, bg="#ECF0F1")
dropdown_frame.pack(pady=10, fill=tk.X)

dropdown_label = tk.Label(dropdown_frame, text="Select or Load Embedding:", font=("Helvetica", 12), bg="#ECF0F1", fg="#34495E")
dropdown_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

dropdown_var = StringVar()
files = get_saved_embeddings()
if files:
    dropdown_var.set(files[0])  
else:
    dropdown_var.set("No saved embeddings")  

dropdown_menu = OptionMenu(dropdown_frame, dropdown_var, *files if files else ["No saved embeddings"])
dropdown_menu.config(font=("Helvetica", 12), bg="#2C3E50", fg="white", relief="flat", highlightthickness=0)
dropdown_menu.grid(row=0, column=1, padx=10, pady=10)

upload_button = tk.Button(dropdown_frame, text="Upload File", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white", bd=0, relief="flat", cursor="hand2", 
                          command=upload_file, padx=15, pady=8)
upload_button.grid(row=0, column=3, padx=10, pady=10)
style_button(upload_button)

load_button = tk.Button(dropdown_frame, text="Load Embedding", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white", bd=0, relief="flat", cursor="hand2", 
                         command=load_embedding, padx=15, pady=8)
load_button.grid(row=0, column=2, padx=10, pady=10)
style_button(load_button)

# Chat Area
chat_frame = tk.Frame(window, bg="#ECF0F1")
chat_frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

# Create a canvas for scrollable chat
chat_canvas = tk.Canvas(chat_frame, bg="#ECF0F1", highlightthickness=0)
chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_scrollbar = Scrollbar(chat_frame, orient=tk.VERTICAL, command=chat_canvas.yview)
chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

chat_canvas.configure(yscrollcommand=chat_scrollbar.set)

# Create a container for chat messages inside the canvas
chat_container = tk.Frame(chat_canvas, bg="#ECF0F1")
chat_canvas_window = chat_canvas.create_window((0, 0), window=chat_container, anchor="nw")

# Ensure the chat container resizes dynamically
def configure_chat_container(event):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
    chat_canvas.itemconfig(chat_canvas_window, width=chat_canvas.winfo_width())

chat_container.bind("<Configure>", configure_chat_container)

def add_message(message, sender="You"):
    message_frame = tk.Frame(chat_container, bg="#ECF0F1", pady=5)

    if sender == "You":
        message_label = tk.Label(
            message_frame,
            text=message,
            bg="#0078FF",
            fg="white",
            font=("Helvetica", 11),
            padx=10,
            pady=5,
            wraplength=600,
            justify="left",
        )
        message_label.pack(side="right", anchor="e", padx=10, pady=5)
    else:
        message_label = tk.Label(
            message_frame,
            text=message,
            bg="#E5E5EA",
            fg="#000000",
            font=("Helvetica", 11),
            padx=10,
            pady=5,
            wraplength=600,
            justify="left",
        )
        message_label.pack(side="left", anchor="w", padx=10, pady=5)

    message_frame.pack(fill="x", padx=10, pady=5)
    chat_canvas.update_idletasks()
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
    chat_canvas.yview_moveto(1)

entry_frame = tk.Frame(window, bg="#ECF0F1")
entry_frame.pack(pady=10, fill=tk.X)

entry_box = tk.Entry(entry_frame, width=40, font=("Helvetica", 12), bg="#FFFFFF", fg="#2C3E50", bd=1, relief="solid", highlightthickness=2, 
                     highlightbackground="#BDC3C7", highlightcolor="#34495E")
entry_box.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

def bot_response(user_input):
    if collection:
        return chat(collection, user_input)
    else:
        return "No embedding loaded. Please upload a file or select a saved embedding."

def send_message(event=None):
    user_message = entry_box.get()
    if user_message:
        add_message(user_message, sender="You")
        entry_box.delete(0, tk.END)
        bot_reply = bot_response(user_message)
        add_message(bot_reply, sender="Bot")

window.bind('<Return>', send_message)

send_button = tk.Button(entry_frame, text="Send", font=("Helvetica", 12, "bold"), bg="#2C3E50", fg="white", bd=0, relief="flat", padx=20, pady=8, cursor="hand2", 
                        command=send_message)
send_button.pack(side=tk.LEFT, padx=10)
style_button(send_button)

send_button.config(state=tk.DISABLED)

window.mainloop()
