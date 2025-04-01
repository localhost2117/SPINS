#!/usr/bin/env python3

import tkinter as tk
import lgpio
import pygame

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
        # Track if sound is currently playing (to avoid re-calling play() constantly)
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

        # Single-cat mode variables
        self.show_gif = False

        # Single cat label in the middle
        self.image_label = tk.Label(self.master, image=self.still_image, bg=GREEN)
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Teasing mode variables
        self.teasing_mode = False
        # Each cat label
        self.cat_labels = []
        for _ in range(3):
            lbl = tk.Label(self.master, image=self.still_image, bg=GREEN)
            self.cat_labels.append(lbl)
        
        self.cat_positions = [
            (0.20, 0.5),
            (0.50, 0.5),
            (0.80, 0.5)
        ]

        # Independent spin states & frame indices for each cat
        self.cat_spinning = [False, False, False]
        self.cat_indices  = [0, 0, 0]

        # --- Teasing Mode toggle button (top-right corner) ---
        self.tease_button = tk.Button(
            self.master,
            text="Teasing Mode",
            command=self.toggle_teasing_mode
        )
        self.tease_button.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # Start polling GPIO & updating animation
        self.poll_inputs()
        self.update_animation()
        
    def toggle_teasing_mode(self):
        """ Toggle between single-cat mode and three-cat teasing mode. """
        self.teasing_mode = not self.teasing_mode

        if self.teasing_mode:
            # Switch button text to "Back"
            self.tease_button.config(text="Back")

            # Hide the single image label
            self.image_label.place_forget()

            # Show the 3 cat labels
            for i, lbl in enumerate(self.cat_labels):
                rx, ry = self.cat_positions[i]
                lbl.place(relx=rx, rely=ry, anchor="center")
        else:
            # Switch button text back to "Teasing Mode"
            self.tease_button.config(text="Teasing Mode")

            # Hide the 3 cats
            for lbl in self.cat_labels:
                lbl.place_forget()

            # Restore the single cat label
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")

    def poll_inputs(self):
        """
        Reads the main button (BUTTON_PIN) and the sensor pins.
        In single-cat mode:
          - The button toggles show_gif -> audio.
        In teasing mode:
          - Each sensor can spin its cat. If ANY cat is spinning, we play audio.
        """
        if not self.teasing_mode:
            # --- Single-cat mode audio logic ---
            button_state = lgpio.gpio_read(self.chip, BUTTON_PIN)
            if button_state == 0:  # pressed
                if not self.show_gif:
                    self.show_gif = True
            else:
                if self.show_gif:
                    self.show_gif = False

            # Start/stop audio if show_gif changed
            self.update_single_cat_audio()

        else:
            # --- Teasing mode: poll each sensor ---
            any_spinning = False
            for i, pin in enumerate(SENSOR_PINS):
                sensor_state = lgpio.gpio_read(self.chip, pin)
                # If sensor is 0 => cat i spins, else static
                # Flip if your hardware logic is reversed
                self.cat_spinning[i] = (sensor_state == 0)

                if self.cat_spinning[i]:
                    any_spinning = True

            # Audio in teasing mode: If ANY cat is spinning => play, else stop
            self.update_teasing_audio(any_spinning)

        # Poll again in 50ms
        self.master.after(50, self.poll_inputs)

    def update_single_cat_audio(self):
        """ If show_gif is True => loop audio, else stop audio. """
        if self.show_gif and not self.sound_playing:
            self.sound_playing = True
            self.sound.play(loops=-1)
        elif not self.show_gif and self.sound_playing:
            self.sound_playing = False
            self.sound.stop()

    def update_teasing_audio(self, any_spinning):
        """ In teasing mode, if any cat is spinning => loop audio; else stop. """
        if any_spinning and not self.sound_playing:
            self.sound_playing = True
            self.sound.play(loops=-1)
        elif not any_spinning and self.sound_playing:
            self.sound_playing = False
            self.sound.stop()

    def update_animation(self):
        """
        Called repeatedly. 
        If not teasing_mode, update the single image (spin or static).
        If teasing_mode, each cat spins or is static based on self.cat_spinning[].
        """
        if not self.teasing_mode:
            # Single-cat animation
            if self.show_gif:
                self.current_frame = (self.current_frame + 1) % self.total_frames
                self.image_label.config(image=self.gif_frames[self.current_frame])
            else:
                self.image_label.config(image=self.still_image)
        else:
            # Teasing-mode: per-cat animation
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
