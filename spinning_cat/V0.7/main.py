#!/usr/bin/env python3

import tkinter as tk
import lgpio
import pygame
import time
import random

BUTTON_PIN = 18
SENSOR_PINS = [21, 20, 2]

STILL_IMAGE_PATH = "oiia.png"
ANIMATED_GIF_PATH = "oiia_spin.gif"
AUDIO_FILE_PATH = "oiia-short.mp3"
GREEN = "#40FF00"

class AnimatedGifApp:
    def __init__(self, master):
        self.master = master
        self.master.title("GIF vs PNG Example (using lgpio)")

        # Window background & size
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
        self.sound_playing = False

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

        # ------------------
        # SINGLE-CAT MODE
        # ------------------
        self.show_gif = False
        self.image_label = tk.Label(self.master, image=self.still_image, bg=GREEN)
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        # ------------------
        # TEASING MODE
        # ------------------
        self.teasing_mode = False
        self.cat_labels = []
        for _ in range(3):
            lbl = tk.Label(self.master, image=self.still_image, bg=GREEN)
            self.cat_labels.append(lbl)
        # Positions for 3 cats
        self.cat_positions = [
            (0.20, 0.5),
            (0.50, 0.5),
            (0.80, 0.5)
        ]
        self.cat_spinning = [False, False, False]
        self.cat_indices  = [0, 0, 0]

        # Teasing Mode button (top-right corner)
        self.tease_button = tk.Button(
            self.master,
            text="Teasing Mode",
            command=self.toggle_teasing_mode
        )
        self.tease_button.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # ------------------
        # GAME MODE
        # ------------------
        self.game_mode = False
        self.game_button = tk.Button(
            self.master,
            text="Game Mode",
            command=self.toggle_game_mode
        )
        # Place it at the top-left corner
        self.game_button.place(relx=0.0, rely=0.0, anchor="nw", x=10, y=10)

        # Game state
        self.round_count = 0
        self.total_time = 0.0
        self.game_active_cat = None  # Which cat is currently spinning
        self.game_start_time = 0.0   # When we started spinning the current cat

        # Start polling and animating
        self.poll_inputs()
        self.update_animation()

    # ==============================
    #        MODE TOGGLES
    # ==============================

    def toggle_teasing_mode(self):
        """ Toggle between single-cat mode and three-cat teasing mode 
            (ignored if we're in game mode).
        """
        # If game_mode is active, ignore teasing toggles
        if self.game_mode:
            return

        self.teasing_mode = not self.teasing_mode
        if self.teasing_mode:
            self.tease_button.config(text="Back")
            # Hide single image
            self.image_label.place_forget()
            # Show 3 cats
            for i, lbl in enumerate(self.cat_labels):
                rx, ry = self.cat_positions[i]
                lbl.place(relx=rx, rely=ry, anchor="center")
        else:
            self.tease_button.config(text="Teasing Mode")
            # Hide 3 cats
            for lbl in self.cat_labels:
                lbl.place_forget()
            # Show single cat again
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")

    def toggle_game_mode(self):
        """ Toggle Game Mode on/off. """
        if self.game_mode:
            # End/exit Game Mode
            self.game_mode = False
            self.game_button.config(text="Game Mode")
            self.end_game_mode()
        else:
            # Start Game Mode
            self.game_mode = True
            self.game_button.config(text="Exit Game")
            self.start_game_mode()

    # ==============================
    #          GAME MODE
    # ==============================

    def start_game_mode(self):
        """ Start or reset the game state, show the 3 cats, start round 1. """
        # If we were in teasing mode, turn it off
        self.teasing_mode = False
        self.tease_button.config(text="Teasing Mode")

        # Hide single cat label
        self.image_label.place_forget()
        # Hide tease cats in case they are placed
        for lbl in self.cat_labels:
            lbl.place_forget()

        # Show the 3 cats
        for i, lbl in enumerate(self.cat_labels):
            rx, ry = self.cat_positions[i]
            lbl.place(relx=rx, rely=ry, anchor="center")

        # Reset game stats
        self.round_count = 0
        self.total_time = 0.0
        self.game_active_cat = None
        self.game_start_time = 0.0

        # Start first round
        self.next_game_round()

    def end_game_mode(self):
        """ Clean up game mode: hide cats, show single cat, or do what you prefer. """
        # Hide 3 cats
        for lbl in self.cat_labels:
            lbl.place_forget()

        # Show single cat again
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        # Optionally show scoreboard
        msg = f"Game Over!\nYou completed 10 rounds.\nTotal time: {self.total_time:.2f} seconds."
        tk.messagebox.showinfo("Scoreboard", msg)

    def next_game_round(self):
        """ Move to the next round, pick a random cat to spin. """
        self.round_count += 1
        if self.round_count > 10:
            # All done
            self.finish_game()
            return

        # Choose a cat randomly
        self.game_active_cat = random.choice([0, 1, 2])

        # Spin only that cat
        for i in range(3):
            self.cat_spinning[i] = (i == self.game_active_cat)
            self.cat_indices[i] = 0  # reset frame index

        # Start timing
        self.game_start_time = time.time()

    def finish_game(self):
        """ Called after round_count > 10. Ends the game mode. """
        self.round_count = 10
        self.toggle_game_mode()  # This calls end_game_mode()

    def cat_hit(self, cat_index):
        """ Called when user hits the correct cat with laser. We record time and go to next round. """
        # Only count the hit if it's the currently active cat
        if cat_index != self.game_active_cat:
            return  # They hit the wrong cat, ignore

        # Calculate time taken
        now = time.time()
        round_time = now - self.game_start_time
        self.total_time += round_time

        # Stop spinning that cat
        self.cat_spinning[self.game_active_cat] = False
        self.game_active_cat = None
        self.game_start_time = 0.0

        # Wait a brief moment, then next round
        self.master.after(500, self.next_game_round)

    # ==============================
    #         POLLING LOGIC
    # ==============================

    def poll_inputs(self):
        """ Read hardware inputs for single-cat mode, teasing mode, and game mode. """
        if self.game_mode:
            # Game logic: check if the active cat is spinning & sensor is triggered
            # If the correct cat is triggered, call cat_hit()
            for i, pin in enumerate(SENSOR_PINS):
                sensor_state = lgpio.gpio_read(self.chip, pin)
                # If cat i is spinning and sensor is triggered (0?), it's a hit
                if self.cat_spinning[i] and (sensor_state == 0):
                    self.cat_hit(i)
            # Audio in game mode: if any cat is spinning => audio
            any_spinning = any(self.cat_spinning)
            self.update_teasing_audio(any_spinning)

        elif self.teasing_mode:
            # Teasing mode: each sensor => spin that cat if sensor=0
            any_spinning = False
            for i, pin in enumerate(SENSOR_PINS):
                sensor_state = lgpio.gpio_read(self.chip, pin)
                self.cat_spinning[i] = (sensor_state == 0)
                if self.cat_spinning[i]:
                    any_spinning = True
            # Audio in teasing mode
            self.update_teasing_audio(any_spinning)

        else:
            # Single-cat mode
            button_state = lgpio.gpio_read(self.chip, BUTTON_PIN)
            if button_state == 0:  # pressed
                if not self.show_gif:
                    self.show_gif = True
            else:
                if self.show_gif:
                    self.show_gif = False
            self.update_single_cat_audio()

        # Poll again in 50ms
        self.master.after(50, self.poll_inputs)

    # ==============================
    #        AUDIO HANDLERS
    # ==============================

    def update_single_cat_audio(self):
        """ If show_gif is True => loop audio, else stop audio. """
        if self.show_gif and not self.sound_playing:
            self.sound_playing = True
            self.sound.play(loops=-1)
        elif not self.show_gif and self.sound_playing:
            self.sound_playing = False
            self.sound.stop()

    def update_teasing_audio(self, any_spinning):
        """ If any cat is spinning => loop audio; else stop. (Used by Teasing & Game Mode) """
        if any_spinning and not self.sound_playing:
            self.sound_playing = True
            self.sound.play(loops=-1)
        elif not any_spinning and self.sound_playing:
            self.sound_playing = False
            self.sound.stop()

    # ==============================
    #       ANIMATION LOOP
    # ==============================

    def update_animation(self):
        """ 
        If single-cat mode => spin or still that one cat. 
        If teasing mode => each cat depends on cat_spinning[i].
        If game mode => only the chosen cat spins, the rest is still.
        """
        if self.game_mode:
            # Animate the cat(s) that are spinning, same as teasing
            for i, lbl in enumerate(self.cat_labels):
                if self.cat_spinning[i]:
                    self.cat_indices[i] = (self.cat_indices[i] + 1) % self.total_frames
                    lbl.config(image=self.gif_frames[self.cat_indices[i]])
                else:
                    lbl.config(image=self.still_image)

        elif self.teasing_mode:
            # Teasing-mode: each cat can spin or be static
            for i, lbl in enumerate(self.cat_labels):
                if self.cat_spinning[i]:
                    self.cat_indices[i] = (self.cat_indices[i] + 1) % self.total_frames
                    lbl.config(image=self.gif_frames[self.cat_indices[i]])
                else:
                    lbl.config(image=self.still_image)

        else:
            # Single-cat mode
            if self.show_gif:
                self.current_frame = (self.current_frame + 1) % self.total_frames
                self.image_label.config(image=self.gif_frames[self.current_frame])
            else:
                self.image_label.config(image=self.still_image)

        self.master.after(50, self.update_animation)

    # ==============================
    #       CLEANUP ON EXIT
    # ==============================

    def cleanup(self):
        lgpio.gpiochip_close(self.chip)
        pygame.quit()

def main():
    root = tk.Tk()

    # For the scoreboard popup
    import tkinter.messagebox

    app = AnimatedGifApp(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
