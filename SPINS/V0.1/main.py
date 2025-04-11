#!/usr/bin/env python3

import tkinter as tk
import lgpio
import pygame

BUTTON_PIN = 18
STILL_IMAGE_PATH = "oiia.png"
ANIMATED_GIF_PATH = "oiia_spin.gif"
AUDIO_FILE_PATH = "oiia-short.mp3"
GREEN = "#40FF00"

class AnimatedGifApp:
    def __init__(self, master):
        self.master = master
        self.master.title("GIF vs PNG Example (using lgpio)")

        # --- NEW: Set the overall window background color ---
        self.master.configure(bg=GREEN)

        # --- NEW: Fix the window size to 800x600, and prevent resizing ---
        self.master.geometry("800x600")
        self.master.resizable(False, False)

        # --- Setup lgpio ---
        self.chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self.chip, BUTTON_PIN)
        
        # Setup pygame audio
        pygame.init()
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(AUDIO_FILE_PATH)

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

        self.show_gif = False

        # A label to display whichever image is active
        self.image_label = tk.Label(self.master, image=self.still_image, bg=GREEN)
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Start polling the button
        self.poll_button()
        # Start the animation loop
        self.update_animation()

    def poll_button(self):
        """
        Check the button state with lgpio:
          - If button_state == 0, consider it pressed
          - Otherwise, it's not pressed
        """
        button_state = lgpio.gpio_read(self.chip, BUTTON_PIN)
        if button_state == 0:
            # Button is pressed
            if not self.show_gif:
                self.show_gif = True
                self.sound.play(loops=-1)
        else:
            # Button is not pressed
            self.show_gif = False
            self.sound.stop()

        self.master.after(100, self.poll_button)

    def update_animation(self):
        """
        If show_gif is True, cycle frames of the animated GIF.
        Otherwise, display the static PNG.
        """
        if self.show_gif:
            self.current_frame = (self.current_frame + 1) % self.total_frames
            self.image_label.config(image=self.gif_frames[self.current_frame])
        else:
            self.image_label.config(image=self.still_image)

        self.master.after(100, self.update_animation)

    def cleanup(self):
        """
        Close the GPIO chip and quit pygame on exit.
        """
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
