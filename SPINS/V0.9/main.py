#!/usr/bin/env python3

import tkinter as tk
import lgpio
import pygame
import random
import time

# Pin definitions
BUTTON_PIN = 18
SENSOR_PINS = [21, 20, 2]

# File paths and colors
STILL_IMAGE_PATH = "oiia.png"
ANIMATED_GIF_PATH = "oiia_spin.gif"
AUDIO_FILE_PATH = "oiia-short.mp3"
WARNING_AUDIO_FILE_PATH = "warning.mp3"  # Warning sound for wrong hit
GREEN = "#40FF00"

class AnimatedGifApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Cat Game Example (using lgpio)")
        self.master.configure(bg=GREEN)
        self.master.geometry("1280x720")
        self.master.resizable(False, False)

        # --- Setup lgpio ---
        self.chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self.chip, BUTTON_PIN)
        for pin in SENSOR_PINS:
            lgpio.gpio_claim_input(self.chip, pin)

        # --- Setup pygame audio ---
        pygame.init()
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(AUDIO_FILE_PATH)
        self.warning_sound = pygame.mixer.Sound(WARNING_AUDIO_FILE_PATH)
        self.sound_playing = False  # tracks if audio is playing

        # --- Load images ---
        self.still_image = tk.PhotoImage(file=STILL_IMAGE_PATH)
        self.gif_frames = []
        frame_index = 0
        while True:
            try:
                frame = tk.PhotoImage(
                    file=ANIMATED_GIF_PATH,
                    format=f"gif -index {frame_index}"
                )
                self.gif_frames.append(frame)
                frame_index += 1
            except tk.TclError:
                break
        self.total_frames = len(self.gif_frames)
        self.current_frame = 0

        # ----- Modes and Variables -----
        self.show_gif = False         # Single-cat mode flag
        self.teasing_mode = False     # Teasing mode flag
        self.game_mode = False        # Game mode flag
        self.game_over = False        # Flag to freeze sensor polling when game is over

        # For Game Mode:
        self.current_game_cat = None
        self.round_start_time = 0.0
        self.hits_count = 0
        self.total_time = 0.0
        self.round_times = []  # List of each round's time

        # --- Display Setup ---
        # Single-cat display (center)
        self.image_label = tk.Label(self.master, image=self.still_image, bg=GREEN)
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        # Teasing / Game mode display: 3 cat labels
        self.cat_labels = []
        for _ in range(3):
            lbl = tk.Label(self.master, image=self.still_image, bg=GREEN)
            self.cat_labels.append(lbl)
        self.cat_positions = [
            (0.20, 0.5),
            (0.50, 0.5),
            (0.80, 0.5)
        ]
        self.cat_spinning = [False, False, False]
        self.cat_indices  = [0, 0, 0]

        # --- Mode Toggle Buttons ---
        # Teasing Mode toggle button (top-right)
        self.tease_button = tk.Button(
            self.master,
            text="Teasing Mode",
            command=self.toggle_teasing_mode
        )
        self.tease_button.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # Game Mode button (top-left)
        self.game_button = tk.Button(
            self.master,
            text="Game Mode",
            command=self.toggle_game_mode
        )
        self.game_button.place(relx=0.0, rely=0.0, anchor="nw", x=10, y=10)

        # Scoreboard and Warning labels (hidden by default)
        self.score_label = tk.Label(self.master, text="", font=("Arial", 24), bg=GREEN)
        self.warning_label = None
        self.play_again_button = None

        # Start polling inputs and animation updates
        self.poll_inputs()
        self.update_animation()
        
    # ------------------- Mode Toggle Methods -------------------
    def toggle_teasing_mode(self):
        if self.game_mode:
            return  # Do nothing if game mode is active
        self.teasing_mode = not self.teasing_mode
        if self.teasing_mode:
            self.tease_button.config(text="Back")
            self.image_label.place_forget()
            for i, lbl in enumerate(self.cat_labels):
                rx, ry = self.cat_positions[i]
                lbl.place(relx=rx, rely=ry, anchor="center")
        else:
            self.tease_button.config(text="Teasing Mode")
            for lbl in self.cat_labels:
                lbl.place_forget()
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")

    def toggle_game_mode(self):
        if self.teasing_mode:
            self.toggle_teasing_mode()
        self.game_mode = not self.game_mode
        if self.game_mode:
            self.game_button.config(text="Stop Game")
            self.image_label.place_forget()
            self.score_label.place_forget()
            if self.warning_label:
                self.warning_label.destroy()
                self.warning_label = None
            if self.play_again_button:
                self.play_again_button.destroy()
                self.play_again_button = None
            for i, lbl in enumerate(self.cat_labels):
                rx, ry = self.cat_positions[i]
                lbl.place(relx=rx, rely=ry, anchor="center")
            self.hits_count = 0
            self.total_time = 0.0
            self.round_times = []
            self.game_over = False
            self.round_start_time = time.time()
            self.start_new_round()
            self.tease_button.config(state="disabled")
        else:
            # Hide any scoreboard, warning, or play again button when stopping game mode.
            self.score_label.place_forget()
            if self.warning_label:
                self.warning_label.destroy()
                self.warning_label = None
            if self.play_again_button:
                self.play_again_button.destroy()
                self.play_again_button = None

            self.game_button.config(text="Game Mode")
            for lbl in self.cat_labels:
                lbl.place_forget()
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")
            self.tease_button.config(state="normal")
    
    def reset_game(self):
        if self.warning_label:
            self.warning_label.destroy()
            self.warning_label = None
        if self.play_again_button:
            self.play_again_button.destroy()
            self.play_again_button = None
        self.game_over = False
        self.hits_count = 0
        self.total_time = 0.0
        self.round_times = []
        self.round_start_time = time.time()
        for i in range(3):
            self.cat_spinning[i] = False
        self.start_new_round()
        self.tease_button.config(state="disabled")
        self.game_button.config(text="Stop Game")
        self.score_label.place_forget()
    
    def start_new_round(self):
        for i in range(3):
            self.cat_spinning[i] = False
        self.current_game_cat = random.choice([0, 1, 2])
        self.cat_spinning[self.current_game_cat] = True
        self.cat_indices[self.current_game_cat] = 0  # reset frame for that cat
        self.round_start_time = time.time()
    
    def handle_cat_hit(self, cat_index):
        """ Called when the correct cat is hit. Add a 1-second delay before next round. """
        self.cat_spinning[cat_index] = False
        elapsed = time.time() - self.round_start_time
        self.round_times.append(elapsed)
        self.total_time += elapsed
        self.hits_count += 1
        if self.hits_count < 10:
            self.master.after(1000, self.start_new_round)
        else:
            self.show_scoreboard()
    
    def handle_wrong_hit(self, wrong_cat_index):
        """ Called when a wrong cat is hit. Show warning, play warning sound, and show Play Again button. """
        self.cat_spinning = [False, False, False]
        if self.sound_playing:
            self.sound.stop()
            self.sound_playing = False
        self.warning_sound.play()
        self.warning_label = tk.Label(
            self.master, 
            text="Wrong Cat Hit! Game Over!", 
            font=("Arial", 24), 
            bg=GREEN
        )
        self.warning_label.place(relx=0.5, rely=0.4, anchor="center")
        self.play_again_button = tk.Button(
            self.master,
            text="Play Again",
            command=self.reset_game
        )
        self.play_again_button.place(relx=0.5, rely=0.5, anchor="center")
        # Set game over flag so sensor polling is halted in game mode.
        self.game_over = True
        # Do not revert to single-cat mode; scoreboard remains until Play Again is pressed.
    
    def show_scoreboard(self):
        for lbl in self.cat_labels:
            lbl.place_forget()
        rounds_text = "\n".join([f"Round {i+1}: {t:.2f} sec" for i, t in enumerate(self.round_times)])
        score_text = f"Game Over!\n{rounds_text}\nTotal time: {self.total_time:.2f} sec"
        self.score_label.config(text=score_text)
        self.score_label.place(relx=0.5, rely=0.5, anchor="center")
        # Set game_over flag so that game mode remains and sensors are ignored.
        self.game_over = True
        # Show Play Again button for the user to restart.
        self.play_again_button = tk.Button(
            self.master,
            text="Play Again",
            command=self.reset_game
        )
        self.play_again_button.place(relx=0.5, rely=0.7, anchor="center")
    
    # ------------------- Polling & Animation -------------------
    def poll_inputs(self):
        if self.game_mode and not self.game_over:
            # First, check the correct sensor.
            correct_pin = SENSOR_PINS[self.current_game_cat]
            correct_state = lgpio.gpio_read(self.chip, correct_pin)
            if correct_state == 0 and self.cat_spinning[self.current_game_cat]:
                self.handle_cat_hit(self.current_game_cat)
            else:
                # Then check the other sensors for a wrong hit.
                for i, pin in enumerate(SENSOR_PINS):
                    if i == self.current_game_cat:
                        continue
                    sensor_state = lgpio.gpio_read(self.chip, pin)
                    if sensor_state == 0:
                        self.handle_wrong_hit(i)
                        break
            self.update_teasing_audio(any(self.cat_spinning))
        else:
            if not self.teasing_mode:
                button_state = lgpio.gpio_read(self.chip, BUTTON_PIN)
                if button_state == 0:
                    if not self.show_gif:
                        self.show_gif = True
                else:
                    if self.show_gif:
                        self.show_gif = False
                self.update_single_cat_audio()
            else:
                any_spinning = False
                for i, pin in enumerate(SENSOR_PINS):
                    sensor_state = lgpio.gpio_read(self.chip, pin)
                    self.cat_spinning[i] = (sensor_state == 0)
                    if self.cat_spinning[i]:
                        any_spinning = True
                self.update_teasing_audio(any_spinning)
        self.master.after(50, self.poll_inputs)
    
    def update_single_cat_audio(self):
        if self.show_gif and not self.sound_playing:
            self.sound_playing = True
            self.sound.play(loops=-1)
        elif not self.show_gif and self.sound_playing:
            self.sound_playing = False
            self.sound.stop()
    
    def update_teasing_audio(self, any_spinning):
        if any_spinning and not self.sound_playing:
            self.sound_playing = True
            self.sound.play(loops=-1)
        elif not any_spinning and self.sound_playing:
            self.sound_playing = False
            self.sound.stop()
    
    def update_animation(self):
        if self.game_mode:
            for i, lbl in enumerate(self.cat_labels):
                if self.cat_spinning[i]:
                    self.cat_indices[i] = (self.cat_indices[i] + 1) % self.total_frames
                    lbl.config(image=self.gif_frames[self.cat_indices[i]])
                else:
                    lbl.config(image=self.still_image)
        else:
            if not self.teasing_mode:
                if self.show_gif:
                    self.current_frame = (self.current_frame + 1) % self.total_frames
                    self.image_label.config(image=self.gif_frames[self.current_frame])
                else:
                    self.image_label.config(image=self.still_image)
            else:
                for i, lbl in enumerate(self.cat_labels):
                    if self.cat_spinning[i]:
                        self.cat_indices[i] = (self.cat_indices[i] + 1) % self.total_frames
                        lbl.config(image=self.gif_frames[self.cat_indices[i]])
                    else:
                        lbl.config(image=self.still_image)
        self.master.after(50, self.update_animation)
    
    def cleanup(self):
        lgpio.gpiochip_close(self.chip)
        pygame.quit()

def main():
    root = tk.Tk()
    app = AnimatedGifApp(root)
    def on_closing():
        app.cleanup()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
