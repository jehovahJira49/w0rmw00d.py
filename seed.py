import errno
import pygame
import random
import string
import time
from pygame.locals import *

# Global variables
command_history = []
drop_speed = 6  # Permanent speed set to 3 (6 = 3 * 2, see speed command logic)
string_types_cache = None


# Add new string generation functions
def get_random_string():
    global string_types_cache
    if string_types_cache is None:
        string_types_cache = {
            "default": string.ascii_letters,
            "numbers": string.digits,
            "hex": string.hexdigits,
            "binary": "01",
            "japanese": "アイウエオカキクケコ",
            "math": "∞∑∏πΣΔψΩ",
        }
    return string_types_cache


# Command index remains unchanged
COMMANDS = {
    "help": {
        "usage": "help [command]",
        "desc": "Show all commands or detailed help for specific command",
        "example": "help mode",
    },
    "mode": {
        "usage": "mode <type>",
        "desc": "Change character set type",
        "options": ["default", "numbers", "hex", "binary", "japanese", "math"],
        "example": "mode binary",
    },
    "custom": {
        "usage": "custom <chars>",
        "desc": "Set custom character set",
        "example": "custom ABC123",
    },
    "speed": {
        "usage": "speed <1-20>",  # Changed from 1-10 to 1-20
        "desc": "Set drop speed of characters (1=slow, 20=fast)",
        "example": "speed 15",
    },
    "clear": {"usage": "clear", "desc": "Clear terminal history", "example": "clear"},
}


def get_command_help(cmd=None):
    if cmd and cmd in COMMANDS:
        c = COMMANDS[cmd]
        return f"""
Command: {cmd}
Usage: {c['usage']}
Description: {c['desc']}
Example: {c['example']}
{f"Options: {', '.join(c['options'])}" if 'options' in c else ''}
"""
    return "\n".join([f"{cmd}: {info['desc']}" for cmd, info in COMMANDS.items()])


def process_command(cmd, available_chars, current_mode):
    global command_history, drop_speed

    cmd = cmd.lower().split()
    if not cmd:
        return available_chars, current_mode, "/?"

    if cmd[0] == "help":
        if len(cmd) > 1:
            return available_chars, current_mode, get_command_help(cmd[1])
        return available_chars, current_mode, get_command_help()

    if cmd[0] == "clear":
        command_history = []
        return available_chars, current_mode, "Terminal cleared"

    if cmd[0] == "mode":
        if len(cmd) < 2:
            return available_chars, current_mode, "Please specify a mode"
        modes = get_random_string()
        if cmd[1] in modes:
            return modes[cmd[1]], cmd[1], f"Changed to {cmd[1]} mode"
        return available_chars, current_mode, "Invalid mode"

    if cmd[0] == "custom":
        if len(cmd) < 2 or not cmd[1]:
            return available_chars, current_mode, "Please provide characters"
        return cmd[1], "custom", f"Set custom characters: {cmd[1]}"

    if cmd[0] == "speed":
        if len(cmd) < 2:
            return available_chars, current_mode, "Please specify speed (1-20)"
        try:
            speed = int(cmd[1])
            if 1 <= speed <= 20:  # Changed from 10 to 20
                global drop_speed
                drop_speed = speed * 2  # Multiply by 2 for faster effect
                return available_chars, current_mode, f"Speed set to {speed}"
        except ValueError:
            pass
        return available_chars, current_mode, "Invalid speed value"

    return available_chars, current_mode, "Unknown command"


def matrix_effect_pygame():
    import os
    import ctypes

    # Detect monitor setup on Windows and place window on leftmost monitor
    try:
        from ctypes import wintypes

        # Use Windows API to get monitor positions
        user32 = ctypes.windll.user32

        # Get primary monitor dimensions
        primary_width = user32.GetSystemMetrics(0)
        primary_height = user32.GetSystemMetrics(1)

        # If monitors are arranged left-to-right, leftmost will have negative x
        # Place window at far left with safe margin
        leftmost_x = -primary_width - 100
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{leftmost_x},50"
    except Exception:
        # Fallback: place far left if detection fails
        os.environ["SDL_VIDEO_WINDOW_POS"] = "-2560,50"

    pygame.init()
    # Get left monitor dimensions for fullscreen
    try:
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        primary_width = user32.GetSystemMetrics(0)
        primary_height = user32.GetSystemMetrics(1)
        screen_width, screen_height = primary_width, primary_height
    except Exception:
        # Fallback to standard resolution
        screen_width, screen_height = 1920, 1080

    # Use borderless windowed mode instead of exclusive fullscreen to avoid minimizing when focus changes
    flags = pygame.NOFRAME
    screen = pygame.display.set_mode((screen_width, screen_height), flags)
    pygame.display.set_caption("w̶̧̢͍͚͓͔͎͌͊̓͋́̈̆̌̈́͐̐̈́͜͝͝0̴̡̨̢̨͎̭̙̳̗̰͓͎̰̙̠̀̑̈́̈́̍̔r̶̢͇̰͓͚͋́̈́̑͆̈́́͆̽̍m̶̧̨̡̦͍͈̪̦̩͕͔̃̈̀ͅẇ̸̢̢̖̬̥̠͕͙͉̩͗̾̀̐͛͠0̵̡̡̡̬̪̤̭̥̬͚̪̪͔̤͂͆̄̉̔͐̿͜0̷̠̰͉̠̦͇̙̱͉̣̈̈́̈͑͋̈́d̶̜́̀͆͒̊́͠")

    # Prepare window handle for optional topmost toggling. Do NOT force topmost by default.
    try:
        wm_info = pygame.display.get_wm_info()
        hwnd = wm_info.get("window") or wm_info.get("hwnd")
    except Exception:
        hwnd = None

    topmost_enabled = False

    def set_topmost(enable: bool):
        nonlocal topmost_enabled
        if not hwnd:
            return
        try:
            import ctypes

            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            flags = SWP_NOMOVE | SWP_NOSIZE
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST if enable else HWND_NOTOPMOST, 0, 0, 0, 0, flags
            )
            topmost_enabled = enable
        except Exception:
            pass

    try:
        background_img = pygame.image.load("background.png")
        background_img = pygame.transform.scale(
            background_img, (screen_width, screen_height)
        )
    except Exception:
        background_img = None

    font_size = 20
    font = pygame.font.SysFont("terminal", font_size)
    columns = int(screen_width / font_size)
    drops = [0 for _ in range(columns)]

    terminal_height = 150
    matrix_height = screen_height - terminal_height
    terminal_font = pygame.font.SysFont("terminal", 16)
    current_input = ""
    cursor_visible = True
    cursor_timer = 0
    # cursor_pos is the insertion point within current_input (0..len)
    cursor_pos = 0
    string_change_timer = 0

    string_types = get_random_string()
    available_chars = string_types["default"]
    current_mode = "default"

    history_index = -1
    command_backup = [errno.ENOENT]

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            if event.type == KEYDOWN:
                # Ctrl+T toggles always-on-top so you can click other apps like VS Code without the window disappearing
                try:
                    mods = pygame.key.get_mods()
                    if event.key == K_t and mods & KMOD_CTRL:
                        set_topmost(not topmost_enabled)
                        continue
                except Exception:
                    pass
                if event.key == K_RETURN and current_input:
                    command_history.append(f"> {current_input}")
                    command_backup = command_history.copy()
                    chars, mode, response = process_command(
                        current_input, available_chars, current_mode
                    )
                    available_chars = chars
                    current_mode = mode
                    command_history.append(response)
                    current_input = ""
                    cursor_pos = 0
                    history_index = -1
                elif event.key == K_BACKSPACE:
                    if cursor_pos > 0:
                        # delete character before cursor
                        current_input = (
                            current_input[: cursor_pos - 1] + current_input[cursor_pos:]
                        )
                        cursor_pos -= 1
                elif event.key == K_UP:
                    if command_backup and history_index < len(command_backup) - 1:
                        history_index += 1
                        current_input = command_backup[-(history_index + 1)].lstrip(
                            "> "
                        )
                        cursor_pos = len(current_input)
                elif event.key == K_DOWN:
                    if history_index > -1:
                        history_index -= 1
                        current_input = (
                            command_backup[-(history_index + 1)].lstrip("> ")
                            if history_index >= 0
                            else ""
                        )
                        cursor_pos = len(current_input)
                elif event.key == K_LEFT:
                    # move cursor left (Ctrl+Left -> word)
                    mods = pygame.key.get_mods()
                    if mods & KMOD_CTRL:
                        # jump left by word
                        if cursor_pos > 0:
                            # find previous whitespace
                            idx = cursor_pos - 1
                            while idx > 0 and current_input[idx].isspace():
                                idx -= 1
                            while idx > 0 and not current_input[idx - 1].isspace():
                                idx -= 1
                            cursor_pos = idx
                    else:
                        if cursor_pos > 0:
                            cursor_pos -= 1
                elif event.key == K_RIGHT:
                    mods = pygame.key.get_mods()
                    if mods & KMOD_CTRL:
                        # jump right by word
                        n = len(current_input)
                        idx = cursor_pos
                        while idx < n and not current_input[idx].isspace():
                            idx += 1
                        while idx < n and current_input[idx].isspace():
                            idx += 1
                        cursor_pos = idx
                    else:
                        if cursor_pos < len(current_input):
                            cursor_pos += 1
                elif event.key == K_HOME:
                    cursor_pos = 0
                elif event.key == K_END:
                    cursor_pos = len(current_input)
                elif event.key == K_DELETE:
                    if cursor_pos < len(current_input):
                        current_input = (
                            current_input[:cursor_pos] + current_input[cursor_pos + 1 :]
                        )
                elif event.unicode and event.unicode.isprintable():
                    # insert at cursor position
                    current_input = (
                        current_input[:cursor_pos]
                        + event.unicode
                        + current_input[cursor_pos:]
                    )
                    cursor_pos += 1
                elif event.type == MOUSEBUTTONDOWN:
                    # handled below in mouse block
                    pass

            if event.type == MOUSEBUTTONDOWN:
                # If user clicks in the input area, set cursor position there
                mx, my = event.pos
                input_top = screen_height - 30
                if my >= input_top:
                    # relative x inside input text (input starts at x=10)
                    rel_x = max(0, mx - 10)
                    # find the nearest character index by measuring substring widths
                    idx = 0
                    for i in range(0, len(current_input) + 1):
                        w = terminal_font.size(current_input[:i])[0]
                        if w >= rel_x:
                            idx = i
                            break
                        idx = i
                    cursor_pos = idx
        string_change_timer = (string_change_timer + 1) % 100
        if string_change_timer == 0 and current_mode != "custom":
            string_types = get_random_string()
            if current_mode in string_types:
                available_chars = string_types[current_mode]

        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill((0, 0, 0))

        for i in range(len(drops)):
            y_pos = drops[i] * font_size
            if y_pos < matrix_height:
                char = random.choice(available_chars)
                text = font.render(char, True, (0, 255, 0))
                screen.blit(text, (i * font_size, y_pos))

            if drops[i] * font_size > matrix_height or random.random() > 0.95:
                drops[i] = 0
            drops[i] += drop_speed / 10.0

        pygame.draw.line(
            screen, (0, 255, 0), (0, matrix_height), (screen_width, matrix_height), 2
        )

        history_y = matrix_height + 10
        for cmd in command_history[-4:]:
            text = terminal_font.render(cmd, True, (0, 255, 0))
            screen.blit(text, (10, history_y))
            history_y += 20

        # Use cursor_visible toggled by cursor_timer so the variable is accessed and controls blinking
        cursor_timer += 1
        if cursor_timer >= 30:
            cursor_visible = not cursor_visible
            cursor_timer = 0

        # Render input left of cursor and right of cursor separately so we can place a blinking caret
        pre_text = terminal_font.render(
            f"> {current_input[:cursor_pos]}", True, (0, 255, 0)
        )
        screen.blit(pre_text, (10, screen_height - 30))

        # caret position (x) is after the pre_text width
        caret_x = 10 + pre_text.get_width()
        caret_y = screen_height - 30

        # width of the mark we'll use for the caret so we can position post-text consistently
        mark_w = terminal_font.size("!")[0]
        if cursor_visible:
            # draw '!' mark as caret
            mark_text = terminal_font.render("!", True, (0, 255, 0))
            screen.blit(mark_text, (caret_x, screen_height - 30))

        # render remainder of text after cursor, positioned after the mark width
        post_text = terminal_font.render(current_input[cursor_pos:], True, (0, 255, 0))
        screen.blit(post_text, (caret_x + mark_w + 2, screen_height - 30))

        # --- Use the time module here to render a live clock in the input area (right-aligned) ---
        try:
            current_time_str = time.strftime("%H:%M:%S")
            clock_text = terminal_font.render(current_time_str, True, (0, 255, 0))
            clock_x = screen_width - clock_text.get_width() - 10
            clock_y = screen_height - 30
            # Make sure clock does not overlap the typed input area; draw after input so it overlays correctly
            screen.blit(clock_text, (clock_x, clock_y))
        except Exception:
            # If time rendering fails for any reason, ignore and continue
            pass

        pygame.display.flip()
        # maintain a modest frame rate; time module already used here for sleeping
        time.sleep(0.05)


def main():
    matrix_effect_pygame()


if __name__ == "__main__":
    # This ensures that matrix_effect_pygame() is called only when the script is executed directly
    main()

# Recommended for debugging (inspect files in dist/). Use --debug=all to include verbose debug bootloader output.
pyinstaller --name w0rmw00d --onedir --console --debug=all --add-data "background.png;." seed.py
