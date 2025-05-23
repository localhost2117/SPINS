# SPINS - Spinning Pi-based Interactive Nonsensical System

**SPINS** is a playful, Raspberry Pi–powered interactive installation that transforms everyday interaction into a joyful, absurd experience. Inspired by the viral spinning cat meme, SPINS uses physical inputs (a button and light sensors) to trigger spinning cat animations accompanied by upbeat music. The project offers multiple modes of interaction, including:

- **Single-Cat Mode:** A button press triggers a spinning cat animation with music.
- **Cat Teasing Mode:** Players use a laser pointer on light sensors to make individual cat avatars spin.
- **Game Mode:** A random cat spins, and players must hit the corresponding sensor to record their reaction times over seven rounds. A stylish scoreboard displays the results with persistent score tracking.

The system is engineered using Python with Tkinter for the GUI, lgpio for GPIO control, and pygame for audio playback. Object-oriented design principles keep the code modular and scalable.

## Features

- **Interactive Animations:** Spinning cat animations triggered by physical inputs.
- **Multiple Modes:** Single-Cat, Cat Teasing, and Game modes.
- **Audio Integration:** Upbeat background music with warning sounds for incorrect interactions.
- **Score Tracking:** Persistent scoreboard to track reaction times.

## File Overview

### `SPINS/`
Contains all source code, including version history and the final release (`V1.0`).

- **V0.1** – Basic implementation: button triggers cat spin  
- **V0.5** – Added "Teasing Mode": laser pointer controls cat spin  
- **V0.7** – Introduced "Game Mode": interactive reaction-based gameplay  
- **V0.9** – Added warning sounds for incorrect hits; enhanced scoreboard  
- **V1.0_build_alpha** – Fixed replay logic; refined game flow and layout  
- **V1.0** – Final version: redesigned scoreboard with per-round stats, UI improvements, gameplay shortened to 7 rounds


## Hardware Requirements

- Raspberry Pi (compatible with lgpio)
- Push Button (connected to GPIO 18)
- Light Sensor Modules with digital output (connected to GPIO21, GPIO20, and GPIO2)
- HDMI monitor or display
- Audio output (speakers or headphones)
- Additional components: cables, resistors, breadboard, etc.


## Software Requirements

- Python 3.x
- Tkinter (typically pre-installed on Raspberry Pi OS)
- lgpio
- pygame


## Installation

1. **Clone the repository:**

2. **Install dependencies (Debian-based systems):**

   sudo apt update
   sudo apt install python3-tk python3-lgpio python3-pygame
   pip3 install pygame


## Usage

Run the project with main.py in any of the versions

**Interaction Overview:**

- **Single-Cat Mode:** Press the physical button to trigger a spinning cat animation with music.
- **Cat Teasing Mode:** Toggle "Teasing Mode" to use a laser pointer on the sensors for interactive cat spins.
- **Game Mode:** Click "Play With Cats" to start the game. A random cat spins, and your reaction time is measured over seven rounds. A scoreboard is displayed at the end, and you can reset the game using hardware inputs or the on-screen "Play Again" button.
- **Persistent Scoreboard:** Use the "Scoreboard" button to view saved game scores.

## Future Work

- **Add skin system**  
- **More sensors**  
- **More game modes**  
- **3D-printed enclosure**  
- **Banana gun laser pen**

## License

This project is licensed under the [MIT License](LICENSE).

---

Go wild, just don’t blame us if your cat starts spinning in real life.
