import tkinter as tk
import subprocess
import time
import json
import socket
from PIL import Image, ImageTk

# Simple Tkinter interface
root = tk.Tk()
class DoomLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("EdgeAerospace Terminal")

        # 1. Loads Background image
        self.bg_image = Image.open("assets/background_nickname.png")
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        # 2. Creates a canvas with the background image dimensions
        self.canvas = tk.Canvas(root, width=self.bg_image.width, height=self.bg_image.height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # 3. Adds image to tk window background 
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # 4. Adds nickname textbox
        self.entry_name = tk.Entry(root, font=("Courier", 18), bg="#1a1a1a", fg="#ff4500", 
                                    insertbackground="white", borderwidth=0,highlightthickness=0)
        self.canvas.create_window(820, 490, window=self.entry_name, width=600,height=60) 
        self.entry_name.focus_set()

        # 5. Adds start button
        self.start_btn = tk.Button(root, text="START", font=("Courier", 14, "bold"), 
                                    bg="#8b0000", fg="white", activebackground="#ff0000",
                                    command=self.championship_start, padx=20,highlightthickness=0)
        self.canvas.create_window(535, 620, window=self.start_btn,width=370,height=80)

        # Maps ENTER to same action as Start Button pressing
        self.root.bind('<Return>', lambda event: self.championship_start())
    
    def championship_start(self):
        player_name = self.entry_name.get()
        root.destroy() # Closes UI

        # Opens the game
        processo = subprocess.Popen(["./build/dsda-doom"])
        
        # Waits for 1 minute or 60 seconds
        try:
            processo.wait(timeout=60) 
        except subprocess.TimeoutExpired:
            processo.terminate() # Closes the game right after timeout

        # Reads doom stats file 
        try:
            with open("dsda_stats.json", "r") as f:
                stats = json.load(f)
            
            stats["player_name"] = player_name # Inserts the name on the json
            print(stats)
            
            # Sends UDP packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = json.dumps(stats).encode('utf-8')
            sock.sendto(message, ("192.168.3.45", 5005))
            print("Data successfully sent!")
        except Exception as e:
            print(f"Error when processing data: {e}")
app = DoomLauncher(root)
root.mainloop()