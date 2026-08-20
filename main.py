import pygame

from ui_renderer import UIRenderer


class CodeVisualizerApp:
    """Owns the Pygame lifecycle and application event loop."""

    SCREEN_WIDTH = 1100
    SCREEN_HEIGHT = 650
    WINDOW_TITLE = "Semester 3 IT Engineering Code Visualizer"

    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(400, 35)
        self.screen = pygame.display.set_mode(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(self.WINDOW_TITLE)
        self.ui_renderer = UIRenderer(self.screen)
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.ui_renderer.run_button.collidepoint(event.pos):
                    self.ui_renderer.set_editor_focus(False)
                else:
                    self.ui_renderer.handle_mouse_down(event.pos, event.button)
            elif event.type == pygame.MOUSEMOTION:
                self.ui_renderer.handle_mouse_motion(
                    event.pos, event.buttons
                )
            elif event.type == pygame.MOUSEBUTTONUP:
                self.ui_renderer.handle_mouse_up()
            elif event.type == pygame.TEXTINPUT:
                self.ui_renderer.handle_text_input(event.text)
            elif event.type == pygame.KEYDOWN:
                if event.mod & pygame.KMOD_CTRL:
                    if event.key == pygame.K_v:
                        # Consume Ctrl+V here so it is never treated as text.
                        try:
                            self._paste_from_clipboard()
                        except Exception:
                            pass
                    elif event.key == pygame.K_c:
                        # Copy the selection, or all code if nothing is selected.
                        try:
                            self.ui_renderer.copy_code()
                        except Exception:
                            pass
                    elif event.key == pygame.K_z:
                        try:
                            self.ui_renderer.undo()
                        except Exception:
                            pass
                    elif event.key == pygame.K_x:
                        try:
                            self.ui_renderer.copy_code()
                            self.ui_renderer._save_undo_state()
                            if not self.ui_renderer._delete_selection():
                                self.ui_renderer.code = ""
                                self.ui_renderer.cursor_line = 0
                                self.ui_renderer.cursor_column = 0
                        except Exception:
                            pass
                    else:
                        self.ui_renderer.handle_key_down(event)
                else:
                    self.ui_renderer.handle_key_down(event)

    def _paste_from_clipboard(self):
        if not self.ui_renderer.editor_focused:
            return

        # Use the native Windows clipboard through Tkinter. This is more
        # reliable than pygame.scrap when Pygame is running on Windows.
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        root.update()
        try:
            clipboard_text = root.clipboard_get()
        finally:
            root.destroy()

        if clipboard_text:
            self.ui_renderer.handle_text_input(clipboard_text)

    def run(self):
        while self.running:
            self.handle_events()
            self.ui_renderer.draw()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    app = CodeVisualizerApp()
    app.run()