import tkinter as tk
import subprocess
import time
import json
import socket
from PIL import Image, ImageTk

import subprocess

from dotenv import dotenv_values, set_key

config_file = "DOOM_CONFIG_FILE"

config = dotenv_values(config_file)

GAMEPLAY_TIME = int(config["GAMEPLAY_TIME"])
# IWAD = config["IWAD"]
last_id_played = int(config["LAST_ID_PLAYED"])
board_prefix_identifier=config["BOARD_PREFIX_IDENTIFIER"]
scoreboard_server_ip=config["SCORE_BOARD_IP"]

if board_prefix_identifier == "":
    cmd = "ifconfig eth0 | grep -oE '([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}' | grep -o '..$'"

    try:
        last_two = subprocess.check_output(cmd, shell=True).decode().strip()
        print(f"The last two characters are: {last_two}")
    except subprocess.CalledProcessError:
        print("Could not retrieve MAC address. Check interface name.")

# print(last_id)

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

        # 1. HIDE the window instead of destroying it
        self.root.withdraw()

        # Opens the game
        processo = subprocess.Popen(["./build/dsda-doom","-complevel", "2",
                                                         "-skill", "4",
                                                         "-warp", "01"])
        
        # Waits for GAMEPLAY_TIME
        try:
            processo.wait(timeout=GAMEPLAY_TIME) 
        except subprocess.TimeoutExpired:
            processo.terminate() # Closes the game right after timeout

        # Reads doom stats file 
        try:
            with open("dsda_stats.json", "r") as f:
                stats = json.load(f)
            
            stats["player_name"] = player_name # Inserts the name on the json
            set_key(config_file, "LAST_ID_PLAYED", str(last_id_played+1))
            stats["player_identifier"] = board_prefix_identifier+str(last_id_played)
            print(stats)
            
            # Sends UDP packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = json.dumps(stats).encode('utf-8')
            sock.sendto(message, (scoreboard_server_ip, 5005))
            print("Data successfully sent!")
            # BRING THE WINDOW BACK
            self.root.deiconify()
            self.show_ending_screen(stats)
        except Exception as e:
            print(f"Error when processing data: {e}")

    def show_ending_screen(self,stats):
        # 1. Clear previous bindings and canvas
        self.canvas.delete("all")
        self.root.unbind('<Return>')
        self.root = root
        self.root.title("EdgeAerospace Terminal")

        # 2. Load and set the new background
        # Ensure you keep a reference to the image so it isn't garbage collected
        self.end_bg_image = Image.open("assets/ending-screen.png")
        self.end_bg_photo = ImageTk.PhotoImage(self.end_bg_image)
        self.canvas.create_image(0, 0, image=self.end_bg_photo, anchor="nw")

        # 3. Add Ending Screen Objects (Labels, Stats, or Buttons)
        # Example: Final Score or "Game Over" text
        self.canvas.create_text(600, 540, text=stats["player_identifier"], 
                                 font=("Courier", 40, "bold"), fill="#8b0000")

        # Example: A 'Restart' or 'Exit' button
        self.exit_btn = tk.Button(self.root, text="EXIT", font=("Courier", 20, "bold"), 
                                    bg="#8b0000", fg="white", activebackground="#ff0000",
                                    command=self.root.quit, padx=20,highlightthickness=0)
        self.canvas.create_window(740, 810, window=self.exit_btn, width=300, height=60)
        self.root.bind('<Return>', lambda event: self.root.quit())
app = DoomLauncher(root)
root.mainloop()