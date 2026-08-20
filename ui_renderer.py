import pygame


class UIRenderer:
    """Draws and manages the code-editor frontend shell."""

    SCREEN_WIDTH = 1100
    SCREEN_HEIGHT = 650
    LEFT_PANEL_WIDTH = 600

    CODE_BACKGROUND = (27, 32, 46)
    OUTPUT_BACKGROUND = (31, 31, 35)
    TOP_BAR = (35, 35, 40)
    BORDER = (70, 73, 82)
    MUTED_TEXT = (155, 158, 168)
    STANDARD_TEXT = (255, 255, 255)
    BLUE = (27, 101, 220)
    BLUE_HOVER = (45, 121, 240)
    CARET = (230, 230, 235)

    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont(None, 18)
        self.ui_font = pygame.font.SysFont(None, 17)
        self.code_font = pygame.font.SysFont("consolas", 16)
        self.code = ""
        self.undo_stack = []
        self.cursor_line = 0
        self.cursor_column = 0
        self.editor_focused = False
        self.selection_anchor = None
        self.dragging_selection = False
        # Keep the button completely inside the 50px top bar.
        self.run_button = pygame.Rect(425, 9, 75, 32)
        self.editor_rect = pygame.Rect(0, 50, self.LEFT_PANEL_WIDTH, 600)

    def draw(self):
        self._draw_panels()
        self._draw_top_bars()
        self._draw_code_editor()
        self._draw_output_panel()

    def _draw_panels(self):
        self.screen.fill(self.OUTPUT_BACKGROUND)
        pygame.draw.rect(
            self.screen, self.CODE_BACKGROUND,
            pygame.Rect(0, 0, self.LEFT_PANEL_WIDTH, self.SCREEN_HEIGHT)
        )
        pygame.draw.line(
            self.screen, self.BORDER,
            (self.LEFT_PANEL_WIDTH, 0),
            (self.LEFT_PANEL_WIDTH, self.SCREEN_HEIGHT),
        )

    def _draw_top_bars(self):
        pygame.draw.rect(
            self.screen, self.TOP_BAR,
            pygame.Rect(0, 0, self.SCREEN_WIDTH, 50)
        )
        pygame.draw.line(
            self.screen, self.BORDER, (0, 49), (self.SCREEN_WIDTH, 49)
        )
        self._draw_text("main.py", self.ui_font, self.STANDARD_TEXT, (4, 30))
        self._draw_text("Output", self.ui_font, self.STANDARD_TEXT, (615, 18))
        self._draw_output_controls()

        button_color = self.BLUE_HOVER if self.run_button.collidepoint(
            pygame.mouse.get_pos()
        ) else self.BLUE
        pygame.draw.rect(self.screen, button_color, self.run_button, border_radius=2)
        self._draw_text("Run", self.ui_font, self.STANDARD_TEXT, (442, 18))
        pygame.draw.polygon(
            self.screen, self.STANDARD_TEXT,
            [(480, 18), (480, 32), (489, 25)]
        )

    def _draw_code_editor(self):
        lines = self.code.split("\n")
        line_height = 22

        self.screen.set_clip(self.editor_rect)
        for line_number, code_line in enumerate(lines):
            y = 58 + line_number * line_height
            self._draw_text(str(line_number + 1), self.code_font,
                            self.MUTED_TEXT, (1, y))
            self._draw_selection_for_line(line_number, code_line, y)
            self._draw_text(code_line, self.code_font, self.STANDARD_TEXT, (17, y))

        if self.editor_focused:
            before_cursor = lines[self.cursor_line][:self.cursor_column]
            cursor_x = 17 + self.code_font.size(before_cursor)[0]
            cursor_y = 58 + self.cursor_line * line_height
            pygame.draw.rect(
                self.screen, self.CARET,
                pygame.Rect(cursor_x, cursor_y, 1, self.code_font.get_height())
            )
        self.screen.set_clip(None)

    def _draw_output_panel(self):
        # Reserved for the future JSON-driven animation renderer.
        pass

    def _draw_output_controls(self):
        """Draw the menu control inside the output panel."""
        menu_x = 1065
        for offset in (-6, 0, 6):
            pygame.draw.circle(self.screen, self.STANDARD_TEXT,
                               (menu_x, 24 + offset), 2)

    def _draw_selection_for_line(self, line_number, code_line, y):
        selection = self._selection_range()
        if selection is None:
            return
        start, end = selection
        line_start = self._line_start_index(line_number)
        line_end = line_start + len(code_line)
        highlight_start = max(start, line_start)
        highlight_end = min(end, line_end)
        if highlight_start >= highlight_end:
            return

        start_column = highlight_start - line_start
        end_column = highlight_end - line_start
        x = 17 + self.code_font.size(code_line[:start_column])[0]
        width = self.code_font.size(
            code_line[start_column:end_column]
        )[0]
        pygame.draw.rect(
            self.screen, (70, 125, 190),
            pygame.Rect(x, y, max(2, width), self.code_font.get_height())
        )

    def _selection_range(self):
        if self.selection_anchor is None:
            return None
        current = self._cursor_index()
        return tuple(sorted((self.selection_anchor, current)))

    def _line_start_index(self, line_number):
        lines = self.code.split("\n")
        return sum(len(line) + 1 for line in lines[:line_number])

    def _draw_text(self, text, font, color, position):
        self.screen.blit(font.render(text, True, color), position)

    def handle_text_input(self, text):
        if not self.editor_focused:
            return
        self._save_undo_state()
        self._delete_selection()
        index = self._cursor_index()
        self.code = (
            self.code[:index] + text + self.code[index:]
        )
        cursor_index = index + len(text)
        self.code, cursor_index = self._wrap_code_to_editor_width(
            self.code, cursor_index
        )
        self._set_cursor_from_index(cursor_index)

    def handle_key_down(self, event):
        if not self.editor_focused:
            return

        if event.key == pygame.K_BACKSPACE:
            index = self._cursor_index()
            if index > 0:
                self._save_undo_state()
                if self._delete_selection():
                    return
                modifiers = event.mod | pygame.key.get_mods()
                if modifiers & pygame.KMOD_CTRL:
                    new_index = self._previous_word_index(index)
                else:
                    new_index = index - 1
                self.code = self.code[:new_index] + self.code[index:]
                self._set_cursor_from_index(new_index)
        elif event.key == pygame.K_DELETE:
            index = self._cursor_index()
            if index < len(self.code):
                self._save_undo_state()
                if self._delete_selection():
                    return
                self.code = self.code[:index] + self.code[index + 1:]
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.handle_text_input("\n")
        elif event.key == pygame.K_LEFT:
            self._set_cursor_from_index(max(0, self._cursor_index() - 1))
        elif event.key == pygame.K_RIGHT:
            self._set_cursor_from_index(
                min(len(self.code), self._cursor_index() + 1)
            )
        elif event.key == pygame.K_UP:
            self._move_cursor_vertical(-1)
        elif event.key == pygame.K_DOWN:
            self._move_cursor_vertical(1)
        elif event.key == pygame.K_HOME:
            self.cursor_column = 0
        elif event.key == pygame.K_END:
            self.cursor_column = len(self.code.split("\n")[self.cursor_line])
        elif event.key == pygame.K_TAB:
            self.handle_text_input("    ")

    def set_editor_focus(self, focused):
        self.editor_focused = focused
        pygame.key.start_text_input() if focused else pygame.key.stop_text_input()
        if not focused:
            self.dragging_selection = False

    def handle_mouse_down(self, position, button):
        if not self.editor_rect.collidepoint(position):
            return
        self.set_editor_focus(True)
        cursor_index = self._cursor_index_from_position(position)
        self._set_cursor_from_index(cursor_index)
        self.selection_anchor = cursor_index
        self.dragging_selection = button in (1, 3)

    def handle_mouse_motion(self, position, buttons):
        left_or_right_button_down = buttons[0] or buttons[2]
        if self.dragging_selection and left_or_right_button_down:
            self._set_cursor_from_index(
                self._cursor_index_from_position(position)
            )

    def handle_mouse_up(self):
        self.dragging_selection = False
        if self.selection_anchor == self._cursor_index():
            self.selection_anchor = None

    def _cursor_index_from_position(self, position):
        lines = self.code.split("\n")
        line = max(0, min(len(lines) - 1, (position[1] - 58) // 22))
        relative_x = max(0, position[0] - 17)
        column = 0
        for index in range(len(lines[line]) + 1):
            if self.code_font.size(lines[line][:index])[0] >= relative_x:
                column = index
                break
            column = index
        return self._line_start_index(line) + column

    def _cursor_index(self):
        lines = self.code.split("\n")
        return sum(len(line) + 1 for line in lines[:self.cursor_line]) + self.cursor_column

    def _set_cursor_from_index(self, index):
        before = self.code[:index]
        self.cursor_line = before.count("\n")
        self.cursor_column = len(before.rsplit("\n", 1)[-1])

    def _move_cursor_vertical(self, direction):
        lines = self.code.split("\n")
        target_line = max(0, min(len(lines) - 1, self.cursor_line + direction))
        self.cursor_line = target_line
        self.cursor_column = min(self.cursor_column, len(lines[target_line]))

    def _previous_word_index(self, index):
        """Return the position reached by Ctrl+Backspace."""
        while index > 0 and self.code[index - 1].isspace():
            index -= 1
        while index > 0 and not self.code[index - 1].isspace():
            index -= 1
        return index

    def _save_undo_state(self):
        if not self.undo_stack or self.undo_stack[-1] != self.code:
            self.undo_stack.append(self.code)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.code = self.undo_stack.pop()
            self.cursor_line = 0
            self.cursor_column = 0
            self.selection_anchor = None

    def _delete_selection(self):
        selection = self._selection_range()
        if selection is None or selection[0] == selection[1]:
            return False
        start, end = selection
        self.code = self.code[:start] + self.code[end:]
        self._set_cursor_from_index(start)
        self.selection_anchor = None
        return True

    def _wrap_code_to_editor_width(self, code, cursor_index):
        """Hard-wrap text so it never crosses into the output panel."""
        available_width = self.LEFT_PANEL_WIDTH - 25
        wrapped = []
        new_cursor_index = cursor_index
        output_index = 0

        for line in code.split("\n"):
            current_line = ""
            for character in line:
                if (
                    current_line
                    and self.code_font.size(current_line + character)[0]
                    > available_width
                ):
                    wrapped.append(current_line)
                    current_line = ""
                    if output_index < cursor_index:
                        new_cursor_index += 1
                    output_index += 1
                current_line += character
                output_index += 1
            wrapped.append(current_line)
            output_index += 1

        result = "\n".join(wrapped)
        return result, min(new_cursor_index, len(result))

    def copy_code(self):
        """Copy the complete editor contents to the system clipboard."""
        selection = self._selection_range()
        if selection and selection[0] != selection[1]:
            text_to_copy = self.code[selection[0]:selection[1]]
        else:
            text_to_copy = self.code
        if not text_to_copy:
            return

        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text_to_copy)
        root.update()
        root.destroy()