from pathlib import Path
from typing import ClassVar

import pygame
from pygame.mixer import Sound
import random
from .AssetManager import music, sfx


class MusicManager:
    music_volume: float = 0.70 # This is the default volume for music, 0.00-1.00
    sfx_volume: float = 0.70 # This is the default volume for sound effects, 0.00-1.00
    _sfx_cache: ClassVar[dict[str, Sound]] = {} # This stores loaded sound effects so they do not need to be loaded from disk each time

    def __init__(self) -> None:
        if not pygame.mixer.get_init(): # This checks whether the pygame mixer has already been initialised before using it
            _ = pygame.mixer.init()

        self.playlist: list[Path] = [path for path in music.values() if path.is_file()] # This stores all music files that exist so missing assets are ignored
        self.shuffle_music() # Randomly shuffles the music, after the playlist is initialised
        self.current_track: int = 0 # This stores the index of the music track that is currently selected
        self._is_playing: bool = False # This tracks whether the music manager is currently playing music

        pygame.mixer.music.set_volume(self.music_volume) # This applies the default music volume to the pygame music channel

        if self.playlist: # This starts the first track automatically when at least one music file is available
            self.play()
    
    def shuffle_music(self) -> None:
        # Shuffles the playlist in random order, so each time the game starts a different music is played
        random.shuffle(x=self.playlist)

    def play(self) -> None:
        if not self.playlist: # This prevents an error when play is called without any valid music files
            return

        pygame.mixer.music.load(filename=str(self.playlist[self.current_track])) # This loads the currently selected music track
        print(f"{pygame.mixer.music.__name__} has been loaded! And now will be playing in the background")
        pygame.mixer.music.play() # This starts the loaded music track
        pygame.mixer.music.set_volume(self.music_volume) # This ensures the loaded track uses the current music volume
        self._is_playing = True # This records that music is now playing

    # Undocumented
    def stop(self) -> None:
        pygame.mixer.music.stop() # This stops the music immediately
        self._is_playing = False # This records that music is no longer playing

    # Undocumented
    def pause(self) -> None:
        pygame.mixer.music.pause() # This pauses the current music track without resetting its position

    # undocumented
    def unpause(self) -> None:
        pygame.mixer.music.unpause() # This continues the current music track from its paused position

    def update(self) -> None:
        if not self._is_playing or not self.playlist: # This avoids checking for the next track when music is stopped or no tracks exist
            return

        if pygame.mixer.music.get_busy(): # This keeps the current track playing until it has finished
            return

        self.current_track = (self.current_track + 1) % len(self.playlist) # This moves to the next track and loops back to the first track at the end
        self.play() # This starts the newly selected track

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.00, min(1.00, volume)) # This restricts the music volume to pygame's valid range
        pygame.mixer.music.set_volume(self.music_volume) # This applies the new music volume immediately

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.00, min(1.00, volume)) # This restricts the sound-effect volume to pygame's valid range
        for sound in self._sfx_cache.values(): # This updates every sound effect that has already been loaded
            sound.set_volume(self.sfx_volume) # This applies the new sound-effect volume to the cached sound

            print(f"Volume for sfx {sound.__hash__} is {sound.get_volume()}")

    def play_sfx(self, sfx_key: str) -> None:
        sound: Sound | None = self._sfx_cache.get(sfx_key) # This checks whether the requested sound effect has already been loaded
        print("sound found " if sound else "sound not found")

        if sound is None: # This loads the sound effect only when it is not already cached
            sfx_path: Path | None = sfx.get(sfx_key) # This gets the file path associated with the requested sound-effect key
            if sfx_path is None or not sfx_path.is_file(): # This ignores unknown keys and sound-effect files that do not exist
                return

            sound = pygame.mixer.Sound(file=str(sfx_path)) # This loads the sound effect from its file path
            self._sfx_cache[sfx_key] = sound # This caches the loaded sound effect for later use

        sound.set_volume(self.sfx_volume) # This ensures the sound effect uses the current sound-effect volume

        print(f"SFX PLAYING WITH THE VOLUME {sound.get_volume()}")
        _ = sound.play() # This plays the requested sound effect
