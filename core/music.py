import pygame
import threading
import time
import os


class OneShotMusicManager:
    """Plays exactly one music file, once, for your Pac-Man school project."""

    def __init__(self, music_file, volume=0.3):
        # init mixer
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()

        if not os.path.exists(music_file):
            raise FileNotFoundError(f"Music file not found: {music_file}")

        # load sound
        self.sound = pygame.mixer.Sound(music_file)
        self.sound.set_volume(volume)
        self.channel = pygame.mixer.Channel(0)

        # state
        self.is_playing = False

    def start(self):
        """Play the track once."""
        if self.is_playing:
            return
        self.channel.play(self.sound)
        self.is_playing = True
        # Optionally, detect when it ends:
        threading.Thread(target=self._watch_end, daemon=True).start()

    def _watch_end(self):
        """Monitor playback and reset state on finish."""
        # busy-wait until the sound is done
        while self.channel.get_busy():
            time.sleep(0.1)
        self.is_playing = False
        print("🎵 Music finished.")

    def stop(self):
        """Stop playback immediately."""
        self.channel.stop()
        self.is_playing = False

    def set_volume(self, vol):
        """Set volume (0.0 to 1.0)."""
        self.sound.set_volume(max(0, min(1, vol)))

    def stop_temporarily(self):
        if self.is_playing:
            self.channel.pause()
            self.is_playing = False

    def resume(self):
        if not self.is_playing:
            self.channel.unpause()
            self.is_playing = True
