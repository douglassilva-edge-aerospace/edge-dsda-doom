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
def ordinal(n):
    if n is None:
        return "N/A"
    if 10 <= (n % 100) <= 20:
        suffix = "TH"
    else:
        suffix = {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"


import re
def sanitize_player_name(name: str, max_len: int = 16) -> str:
    if not isinstance(name, str):
        return "PLAYER"

    # Trim whitespace
    name = name.strip()

    # Remove disallowed characters
    name = re.sub(r"[^A-Za-z0-9 _-]", "", name)

    # Collapse repeated spaces
    name = re.sub(r"\s+", " ", name)

    # Enforce length
    name = name[:max_len].strip()

    # Fallback if empty
    if not name:
        return "PLAYER"

    return name

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
                                    command=self.show_instructions, padx=20,highlightthickness=0)
        self.canvas.create_window(535, 620, window=self.start_btn,width=370,height=80)

        # Maps ENTER to same action as Start Button pressing
        self.root.bind('<Return>', lambda event: self.show_instructions())
    
    def show_instructions(self):
        self.canvas.delete("all")
        self.root.unbind('<Return>')
        self.root = root
        self.root.title("EdgeAerospace Terminal")

        # 1. Loads Background image
        self.instruction_image = Image.open("assets/instructions-screen.png")
        self.instruction_photo = ImageTk.PhotoImage(self.instruction_image)

        # 3. Adds image to tk window background 
        # 2. Update the Canvas size to match the NEW image exactly
        self.canvas.config(width=self.instruction_photo.width(), height=self.instruction_photo.height())
        self.canvas.create_image(0, 0, image=self.instruction_photo, anchor="nw")

# 2. Progress Bar Settings
        BAR_WIDTH = 1150
        BAR_HEIGHT = 15
        BAR_X = 570 - (BAR_WIDTH // 2) # Centering based on your button logic
        BAR_Y = 995
        HOLD_TIME_MS = 5000  # 5 seconds
        INTERVAL_MS = 75     # Update every 50ms
        
        # Draw Bar Border
        self.canvas.create_rectangle(BAR_X, BAR_Y, BAR_X + BAR_WIDTH, BAR_Y + BAR_HEIGHT, 
                                     outline="#5c5e5c", width=2)
        
        # Create the filling part (starts at 0 width)
        progress_fill = self.canvas.create_rectangle(BAR_X, BAR_Y, BAR_X, BAR_Y + BAR_HEIGHT, 
                                                     fill="#17ba05", outline="")

        # 3. Progress Update Function
        self.elapsed = 0
        def update_progress():
            self.elapsed += INTERVAL_MS
            current_width = (self.elapsed / HOLD_TIME_MS) * BAR_WIDTH
            
            # Update the coordinates of the fill rectangle
            self.canvas.coords(progress_fill, BAR_X, BAR_Y, BAR_X + current_width, BAR_Y + BAR_HEIGHT)
            
            if self.elapsed < HOLD_TIME_MS:
                # Schedule the next update
                self.root.after(INTERVAL_MS, update_progress)
            else:
                # 4. Once finished, show the START button
                self.championship_start()

        update_progress()


    def championship_start(self):
        player_name = self.entry_name.get()

        # 1. HIDE the window instead of destroying it
        self.root.withdraw()

        # Opens the game
        process = subprocess.Popen(["./build/dsda-doom","-width","1600","-height","900","-complevel", "2",
                                                         "-skill", "2",
                                                         "-warp", "3 6"])
        
        # Waits for GAMEPLAY_TIME
        try:
            process.wait(timeout=GAMEPLAY_TIME) 
        except subprocess.TimeoutExpired:
            process.terminate() # Closes the game right after timeout

        # Reads doom stats file 
        try:
            with open("dsda_stats.json", "r") as f:
                stats = json.load(f)
            
            stats["player_name"] = sanitize_player_name(player_name, max_len=16).upper()
            aux_monsters = stats["monsters"]
            stats["monsters"] = {"killed":aux_monsters[0],"total":aux_monsters[1]}
            aux_secrets = stats["secrets"]
            stats["secrets"] = {"found":aux_secrets[0],"total":aux_secrets[1]}
            aux_items = stats["items"]
            stats["items"] = {"picked_up":aux_items[0],"total":aux_items[1]}
            set_key(config_file, "LAST_ID_PLAYED", str(last_id_played+1))
            stats["player_identifier"] = board_prefix_identifier+str(last_id_played)
            print(stats)
            
            # Sends packet
            import requests
            url = f"http://{scoreboard_server_ip}:5005/api/ingest"
            response = requests.post(url, json=stats, timeout=2)
            response.raise_for_status()  # Checks if the server returned an error

            resp_json = response.json()
            print("Server response:", resp_json)

            # Add returned fields into stats so ending screen can use them
            stats["rank_position"] = resp_json.get("position")
            stats["updated"] = resp_json.get("updated")

            print("Data successfully sent!")
        except Exception as e:
            print(f"Error when processing data: {e}")
        
        # BRING THE WINDOW BACK
        self.root.deiconify()
        self.show_ending_screen(stats)

    def show_ending_screen(self,stats):
        # 1. Clear previous bindings and canvas
        self.canvas.delete("all")
        self.root.unbind('<Return>')
        self.root = root
        self.root.title("EdgeAerospace Terminal")

        # 2. Load and set the new background
        # Ensure you keep a reference to the image so it isn't garbage collected
        self.end_bg_image = Image.open("assets/ending-screen-3.png")
        self.end_bg_photo = ImageTk.PhotoImage(self.end_bg_image)
        
        # Canvas stuff
        self.canvas.config(width=self.end_bg_photo.width(), height=self.end_bg_photo.height())
        self.canvas.create_image(0, 0, image=self.end_bg_photo, anchor="nw")


        # 3. Add Ending Screen Objects (Labels, Stats, or Buttons)
        # Example: Final Score or "Game Over" text
        self.canvas.create_text(600, 530, text=f"Player: {stats['player_identifier']}", 
                                 font=("Courier", 40, "bold"), fill="#8b0000")
        
            # Rank position
        rank_text = ordinal(stats.get("rank_position"))
        self.canvas.create_text(
            600, 580,
            text="  Rank: "+rank_text+" Place",
            font=("Courier", 40, "bold"),
            fill="#8b0000"
        )

        # Example: A 'Restart' or 'Exit' button
        self.exit_btn = tk.Button(self.root, text="EXIT", font=("Courier", 20, "bold"), 
                                    bg="#8b0000", fg="white", activebackground="#ff0000",
                                    command=self.root.quit, padx=20,highlightthickness=0)
        self.canvas.create_window(740, 810, window=self.exit_btn, width=300, height=60)
        self.root.bind('<Return>', lambda event: self.root.quit())
app = DoomLauncher(root)
root.mainloop()