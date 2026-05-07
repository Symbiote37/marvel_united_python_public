import os
from src.utils.helpers import Col

class AudioSystem:
    _initialized = False

    @staticmethod
    def initialize():
        """Bootstraps the SDL2 audio bindings in headless mode."""
        try:
            # 🚨 Hide the standard Pygame welcome message from cluttering the terminal
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
            import pygame
            pygame.mixer.init()
            AudioSystem._initialized = True
        except ImportError:
            print(Col.wrap(" [!] AudioSystem offline: 'pygame' module not found.", Col.YLW))
        except Exception as e:
            print(Col.wrap(f" [!] AudioSystem failed to boot: {e}", Col.RED))

    @staticmethod
    def play_menu_theme(file_path):
        """Plays the track asynchronously on an infinite loop."""
        if not AudioSystem._initialized: return
        if not os.path.exists(file_path):
            print(Col.wrap(f" [!] Audio track missing: {file_path}", Col.DARK_GRAY))
            return

        import pygame
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(loops=-1) # -1 forces infinite looping
        except Exception as e:
            print(Col.wrap(f" [!] AudioSystem Menu BGM Error: {e}", Col.RED))

    @staticmethod
    def stop_music():
        """Fades out the current track over 1.5 seconds."""
        if not AudioSystem._initialized: return
        import pygame
        pygame.mixer.music.fadeout(1500)

    @staticmethod
    def transition_track(file_path, fade_ms=1500):
        """Gracefully fades out the current track and brings in the new one."""
        if not AudioSystem._initialized: return
        import pygame
        import time
        import os
        from src.utils.helpers import Col

        if not os.path.exists(file_path):
            print(Col.wrap(f" [!] Audio track missing: {file_path}", Col.DARK_GRAY))
            return

        try:
            # If music is actively playing, fade it to zero
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(fade_ms)
                time.sleep(fade_ms / 1000.0) # Pause the game state to allow the fade

            # Load and ignite the new track
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(loops=-1)
        except Exception as e:
            print(Col.wrap(f" [!] AudioSystem Transition Error: {e}", Col.RED))
