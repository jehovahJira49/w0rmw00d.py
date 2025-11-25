  # !make - convenience wrapper to generate player modules and playtest logs
# Run this by calling: python make_players.py
# (The following was a shell command; keep as comment or run externally)
# python make_players.py
import pygame
import random
import string
import time
import os
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
MATRIX_HEIGHT = 500

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_ROUND_COMPLETE = 3

# Global variables
drop_speed = 2
current_mode = "default"
# 3D depth settings
enable_3d = False  # Toggled by taking red pill
MIN_DEPTH = 0  # Front of screen
MAX_DEPTH = 100  # Back of screen
DEPTH_SCALE_FACTOR = 0.5  # Scale reduction at max depth


def get_random_string():
    string_types = {
        "default": string.ascii_letters,
        "numbers": string.digits,
        "hex": string.hexdigits,
        "binary": "01",
        "japanese": "アイウエオカキクケコ",
        "math": "∞∑∏πΣΔψΩ",
    }
    return string_types


def load_player_frames():
    """Load player frames.

    Preferred behaviour:
    - If a spritesheet named 'sprite sheet.png' exists and contains 4 frames laid out horizontally,
      slice it into 4 frames and return that list.
    - Otherwise, attempt to load individual numbered frame files (1st frame.png ... 25th frame.png) as fallback.
    - If nothing found, return 4 placeholder frames.
    
    Excludes punching/attack frames from movement animations.
    """
    sheet_name = "sprite sheet.png"
    # target height for player frames (reduce "too long" sprites)
    target_h = 48
    
    # Frames to exclude from movement animation (punching/attack frames)
    # Add frame numbers here that should not be part of movement animation
    # Frames 4, 5, 9, 10, 15, 16, 17 are punching/attack animations
    # Frames 13 and 25 are jump frames (left and right respectively)
    EXCLUDE_FROM_MOVEMENT = [4, 5, 9, 10, 13, 15, 16, 17, 25]
    
    # Jump frames - separate from movement
    JUMP_FRAME_LEFT = 13
    JUMP_FRAME_RIGHT = 25

    # We'll return frames grouped by direction: down, left, up, right
    # and an explicit idle pair (1st + 2nd frame) when available.
    # Prefer horizontal movement frames first so right/left animations are primary
    dirs = ["right", "left", "down", "up"]
    frames_by_dir = {d: [] for d in dirs}
    # idle_frames: global fallback (1st/2nd)
    idle_frames = []
    # idle_by_dir: per-direction idle pairs (idle_down.png, idle_left.png, ...)
    idle_by_dir = {d: [] for d in dirs}

    # 1) Try to load explicit idle frames (1st and 2nd). These will be used when the player
    # is standing idle.
    def _load_numbered(n):
        suffix = "th"
        if n == 1:
            suffix = "st"
        elif n == 2:
            suffix = "nd"
        elif n == 3:
            suffix = "rd"
        fname = os.path.join(os.path.dirname(__file__), f"{n}{suffix} frame.png")
        if os.path.exists(fname):
            try:
                img = pygame.image.load(fname).convert_alpha()
                fw, fh = img.get_size()
                if fh != target_h:
                    scale = target_h / fh
                    new_w = max(1, int(fw * scale))
                    img = pygame.transform.smoothscale(img, (new_w, target_h))
                return img
            except Exception:
                return None
        return None

    # load idle first (1st and 2nd)
    for n in (1, 2):
        img = _load_numbered(n)
        if img:
            idle_frames.append(img)

    # build list of available numbered frames (1..25)
    # Exclude punching/attack frames from movement animations
    frame_files = []
    for i in range(1, 26):
        # Skip frames that are designated for punching/attacks
        if i in EXCLUDE_FROM_MOVEMENT:
            continue
            
        suffix = "th"
        if i == 1:
            suffix = "st"
        elif i == 2:
            suffix = "nd"
        elif i == 3:
            suffix = "rd"
        img = _load_numbered(i)
        if img:
            frame_files.append(img)

    # If we found numbered frames, split them into 4 directional groups sequentially
    if frame_files:
        total = len(frame_files)
        chunk = math.ceil(total / 4)
        for idx, d in enumerate(dirs):
            start = idx * chunk
            end = start + chunk
            frames_by_dir[d] = frame_files[start:end]
        # Ensure each direction has at least 2 frames by duplicating or flipping where necessary
        for d in dirs:
            if len(frames_by_dir[d]) == 0:
                # fallback: duplicate first available frame from any dir
                for other in dirs:
                    if frames_by_dir[other]:
                        frames_by_dir[d] = [
                            frames_by_dir[other][0].copy(),
                            pygame.transform.flip(frames_by_dir[other][0], True, False),
                        ]
                        break
            elif len(frames_by_dir[d]) == 1:
                f0 = frames_by_dir[d][0]
                f1 = pygame.transform.flip(f0, True, False)
                frames_by_dir[d] = [f0, f1]
        # If we don't have an explicit idle pair, try to set it from the 'down' group
        if len(idle_frames) < 2:
            down = frames_by_dir.get("down", [])
            if len(down) >= 2:
                idle_frames = down[:2]
            elif len(down) == 1:
                idle_frames = [down[0], pygame.transform.flip(down[0], True, False)]

        # build per-direction idle pairs (try explicit files idle_<dir>.png first)
        for d in dirs:
            idle_path = os.path.join(os.path.dirname(__file__), f"idle_{d}.png")
            if os.path.exists(idle_path):
                try:
                    img = pygame.image.load(idle_path).convert_alpha()
                    fw, fh = img.get_size()
                    if fh != target_h:
                        scale = target_h / fh
                        new_w = max(1, int(fw * scale))
                        img = pygame.transform.smoothscale(img, (new_w, target_h))
                    idle_by_dir[d] = [img, pygame.transform.flip(img, True, False)]
                    continue
                except Exception:
                    pass

            # fallback to using first two frames of the direction if available
            if len(frames_by_dir[d]) >= 2:
                idle_by_dir[d] = frames_by_dir[d][:2]
            elif len(frames_by_dir[d]) == 1:
                f0 = frames_by_dir[d][0]
                idle_by_dir[d] = [f0, pygame.transform.flip(f0, True, False)]
            else:
                # will fill later with placeholders
                idle_by_dir[d] = []

        # final sanity: ensure idle_frames has two entries
        if len(idle_frames) == 1:
            idle_frames.append(pygame.transform.flip(idle_frames[0], True, False))
        elif len(idle_frames) == 0:
            # create placeholders
            img = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(img, GREEN, (0, 0, target_h, target_h), 2)
            idle_frames = [img, pygame.transform.flip(img, True, False)]

        # fill any empty idle_by_dir with global idle or placeholders
        for d in dirs:
            if not idle_by_dir[d]:
                if len(frames_by_dir[d]) >= 2:
                    idle_by_dir[d] = frames_by_dir[d][:2]
                else:
                    idle_by_dir[d] = idle_frames[:2]

        # Load jump frames separately (frame 13 for left jump, frame 25 for right jump)
        jump_frame_left = _load_numbered(JUMP_FRAME_LEFT)
        jump_frame_right = _load_numbered(JUMP_FRAME_RIGHT)
        
        # Load punch frames by direction
        # Frames 4-5: LEFT punch (character facing left)
        # Frames 9-10: FLY frames (both arms extended - for future fly mechanic in 2D/3D)
        # Frames 15-17: RIGHT punch (character facing right)
        PUNCH_FRAMES_LEFT = [4, 5]
        PUNCH_FRAMES_FLY = [9, 10]  # Both arms extended - saved for fly mechanic
        PUNCH_FRAMES_RIGHT = [15, 16, 17]
        
        punch_frames_by_dir = {"left": [], "fly": [], "right": []}
        
        # Load left punch frames
        for pf in PUNCH_FRAMES_LEFT:
            frame = _load_numbered(pf)
            if frame:
                punch_frames_by_dir["left"].append(frame)
        
        # Load fly frames (both arms extended)
        for pf in PUNCH_FRAMES_FLY:
            frame = _load_numbered(pf)
            if frame:
                punch_frames_by_dir["fly"].append(frame)
        
        # Load right punch frames
        for pf in PUNCH_FRAMES_RIGHT:
            frame = _load_numbered(pf)
            if frame:
                punch_frames_by_dir["right"].append(frame)
        
        # Create placeholders if frames don't exist
        if not punch_frames_by_dir["left"]:
            for _ in range(len(PUNCH_FRAMES_LEFT)):
                punch_frame = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
                pygame.draw.rect(punch_frame, RED, (0, 0, target_h, target_h), 2)
                punch_frames_by_dir["left"].append(punch_frame)
        
        if not punch_frames_by_dir["fly"]:
            for _ in range(len(PUNCH_FRAMES_FLY)):
                punch_frame = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
                pygame.draw.rect(punch_frame, RED, (0, 0, target_h, target_h), 2)
                punch_frames_by_dir["fly"].append(punch_frame)
        
        if not punch_frames_by_dir["right"]:
            for _ in range(len(PUNCH_FRAMES_RIGHT)):
                punch_frame = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
                pygame.draw.rect(punch_frame, RED, (0, 0, target_h, target_h), 2)
                punch_frames_by_dir["right"].append(punch_frame)
        
        # If jump frames don't exist, create placeholders
        if not jump_frame_left:
            jump_frame_left = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(jump_frame_left, GREEN, (0, 0, target_h, target_h), 2)
        if not jump_frame_right:
            jump_frame_right = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(jump_frame_right, GREEN, (0, 0, target_h, target_h), 2)

        return frames_by_dir, idle_by_dir, idle_frames, jump_frame_left, jump_frame_right, punch_frames_by_dir

    # If no numbered frames, try spritesheet (sprite sheet.png -> 4 horizontal frames)
    try:
        path = os.path.join(os.path.dirname(__file__), sheet_name)
        if os.path.exists(path):
            spritesheet = pygame.image.load(path).convert_alpha()
            sw, sh = spritesheet.get_size()
            frame_count = 4
            frame_w = sw // frame_count
            frame_h = sh
            if frame_w > 0:
                for i in range(frame_count):
                    rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
                    frame = spritesheet.subsurface(rect).copy()
                    fw, fh = frame.get_size()
                    if fh != target_h:
                        scale = target_h / fh
                        new_w = max(1, int(fw * scale))
                        frame = pygame.transform.smoothscale(frame, (new_w, target_h))
                    frames_by_dir[dirs[i % 4]].append(frame)
    except Exception:
        pass

    # Final fallback: generate placeholder frames for each direction
    for d in dirs:
        if not frames_by_dir[d]:
            img = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(img, GREEN, (0, 0, target_h, target_h), 2)
            pygame.draw.polygon(
                img,
                GREEN,
                [
                    (target_h // 2, 8),
                    (target_h - 9, target_h - 8),
                    (target_h // 2, target_h - 12),
                    (9, target_h - 8),
                ],
            )
            frames_by_dir[d] = [img, pygame.transform.flip(img, True, False)]

    # If we reach here (no numbered frames nor spritesheet) ensure we still have an idle pair.
    if len(idle_frames) < 2:
        # derive from any directional set
        for d in dirs:
            if len(frames_by_dir[d]) >= 2:
                idle_frames = frames_by_dir[d][:2]
                break
        if len(idle_frames) == 1:
            idle_frames.append(pygame.transform.flip(idle_frames[0], True, False))
        elif len(idle_frames) == 0:
            img = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(img, GREEN, (0, 0, target_h, target_h), 2)
            idle_frames = [img, pygame.transform.flip(img, True, False)]

    # build idle_by_dir for fallback case
    for d in dirs:
        idle_by_dir[d] = (
            frames_by_dir[d][:2] if len(frames_by_dir[d]) >= 2 else idle_frames[:2]
        )

    # Load jump frames separately (frame 13 for left jump, frame 25 for right jump)
    jump_frame_left = _load_numbered(JUMP_FRAME_LEFT)
    jump_frame_right = _load_numbered(JUMP_FRAME_RIGHT)
    
    # Load punch frames by direction
    # Frames 4-5: LEFT punch (character facing left)
    # Frames 9-10: FLY frames (both arms extended - for future fly mechanic in 2D/3D)
    # Frames 15-17: RIGHT punch (character facing right)
    PUNCH_FRAMES_LEFT = [4, 5]
    PUNCH_FRAMES_FLY = [9, 10]  # Both arms extended - saved for fly mechanic
    PUNCH_FRAMES_RIGHT = [15, 16, 17]
    
    punch_frames_by_dir = {"left": [], "fly": [], "right": []}
    
    # Load left punch frames
    for pf in PUNCH_FRAMES_LEFT:
        frame = _load_numbered(pf)
        if frame:
            punch_frames_by_dir["left"].append(frame)
    
    # Load fly frames (both arms extended)
    for pf in PUNCH_FRAMES_FLY:
        frame = _load_numbered(pf)
        if frame:
            punch_frames_by_dir["fly"].append(frame)
    
    # Load right punch frames
    for pf in PUNCH_FRAMES_RIGHT:
        frame = _load_numbered(pf)
        if frame:
            punch_frames_by_dir["right"].append(frame)
    
    # Create placeholders if frames don't exist
    if not punch_frames_by_dir["left"]:
        for _ in range(len(PUNCH_FRAMES_LEFT)):
            punch_frame = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(punch_frame, RED, (0, 0, target_h, target_h), 2)
            punch_frames_by_dir["left"].append(punch_frame)
    
    if not punch_frames_by_dir["fly"]:
        for _ in range(len(PUNCH_FRAMES_FLY)):
            punch_frame = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(punch_frame, RED, (0, 0, target_h, target_h), 2)
            punch_frames_by_dir["fly"].append(punch_frame)
    
    if not punch_frames_by_dir["right"]:
        for _ in range(len(PUNCH_FRAMES_RIGHT)):
            punch_frame = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
            pygame.draw.rect(punch_frame, RED, (0, 0, target_h, target_h), 2)
            punch_frames_by_dir["right"].append(punch_frame)
    
    # If jump frames don't exist, create placeholders
    if not jump_frame_left:
        jump_frame_left = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
        pygame.draw.rect(jump_frame_left, GREEN, (0, 0, target_h, target_h), 2)
    if not jump_frame_right:
        jump_frame_right = pygame.Surface((target_h, target_h), pygame.SRCALPHA)
        pygame.draw.rect(jump_frame_right, GREEN, (0, 0, target_h, target_h), 2)

    return frames_by_dir, idle_by_dir, idle_frames, jump_frame_left, jump_frame_right, punch_frames_by_dir


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # load frames and setup animation (directional frames)
        # load_player_frames now returns (frames_by_dir, idle_by_dir, idle_frames, jump_left, jump_right, punch_frames_by_dir)
        self.dir_frames, self.idle_by_dir, self.idle_frames, self.jump_frame_left, self.jump_frame_right, self.punch_frames = load_player_frames()
        # default set will be idle frames if available
        self.frames = (
            self.idle_frames if self.idle_frames else self.dir_frames.get("down", [])
        )
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 8  # frames per second-ish (higher => faster animate)
        self.idle_animation_speed = 3  # Slower speed for idle breathing effect
        self.idle_timer = 0  # Separate timer for idle animation
        self.idle_state = "breathing"  # Track idle animation state

        # ensure there is at least one frame
        if not self.frames:
            # fallback single blank
            self.frames = [pygame.Surface((48, 48), pygame.SRCALPHA)]
        self.image = self.frames[self.frame_index]
        # store a 3D position (x, y, z). We'll only use x/y for now but keep z for future use.
        self.pos = pygame.math.Vector3(x, y, 0)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.speed = 6
        self.health = 100

        # side-view physics
        self.side_view = True  # start in side view (left/right + jump)
        self.vy = 0
        self.gravity = 1
        self.jump_strength = -16
        self.on_ground = False
        # horizontal velocity for impulse (used by wall-jump)
        self.vx = 0

        # animation state
        self.active_set = None
        self.any_dir_pressed = False

        self.facing = "down"

        # advanced movement
        self.max_jumps = 2
        self.jumps_left = self.max_jumps
        self.on_wall = False
        self.wall_dir = None
        self.prev_up_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        
        # Track if we're currently jumping to show jump frame
        self.is_jumping = False
        
        # 3D depth controls (z-axis movement)
        self.depth_speed = 3  # Speed of z-axis movement
        self.base_scale = 1.0  # Original scale at z=0
        self.original_frames = None  # Store original unscaled frames
        
        # Attack/Punch mechanics
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_duration = 15  # frames for attack animation
        self.attack_cooldown = 0
        self.attack_cooldown_duration = 20  # frames before can attack again
        self.attack_range = 80  # pixels for attack hitbox
        self.attack_parry_window = 3  # frames window for perfect parry timing

    # --- helper animation methods ---
    def set_facing(self, direction: str):
        """Set facing direction immediately (used while keys are pressed)."""
        self.facing = direction

    def set_active_direction_frames(self, direction: str):
        """Select movement frames for a given direction and make them active.

        This ensures the player shows the moving frames for the direction even when
        movement is blocked (for example at a wall).
        For right direction, it flips the left direction frames horizontally.
        """
        # Use left frames for both left and right, but flip for right
        lookup_direction = "left" if direction == "right" else direction
        dir_set = self.dir_frames.get(lookup_direction, [])
        
        if len(dir_set) == 0:
            # placeholder pair
            img0 = pygame.Surface((48, 48), pygame.SRCALPHA)
            img1 = pygame.Surface((48, 48), pygame.SRCALPHA)
            self.active_set = [img0, img1]
        elif len(dir_set) == 1:
            f0 = dir_set[0]
            if direction == "right":
                f0 = pygame.transform.flip(f0, True, False)
            self.active_set = [f0, pygame.transform.flip(f0, True, False)]
        else:
            # Use ALL frames from the direction set for proper animation
            if direction == "right":
                # Flip all left frames horizontally for right movement
                self.active_set = [pygame.transform.flip(frame, True, False) for frame in dir_set]
            else:
                self.active_set = dir_set
        
        # reset animation index/timer when changing sets only if direction actually changed
        if not hasattr(self, 'last_direction') or self.last_direction != direction:
            self.frame_index = 0
            self.animation_timer = 0
            self.last_direction = direction

    def set_idle_for_facing(self):
        """Set the idle animation for the current facing direction."""
        facing_idle = getattr(self, "idle_by_dir", {}).get(self.facing, None)
        if facing_idle and len(facing_idle) >= 2:
            self.active_set = facing_idle[:2]
        else:
            facing_set = self.dir_frames.get(self.facing, [])
            if len(facing_set) >= 2:
                self.active_set = facing_set[:2]
            else:
                # fallback to global idle_frames or a placeholder
                if getattr(self, "idle_frames", None) and len(self.idle_frames) >= 2:
                    self.active_set = self.idle_frames[:2]
                else:
                    img = pygame.Surface((48, 48), pygame.SRCALPHA)
                    self.active_set = [img, pygame.transform.flip(img, True, False)]
        self.frame_index = 0
        self.animation_timer = 0

    def sync_rect(self):
        """Sync the sprite rect to the current image and self.pos (center).

        We store position in self.pos (Vector3). The sprite rect is positioned using
        the x/y components; z is reserved for future use.
        """
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def get_depth_scale(self):
        """Calculate scale factor based on z-depth position.
        
        Returns a scale between 1.0 (front, z=0) and DEPTH_SCALE_FACTOR (back, z=MAX_DEPTH)
        """
        if not enable_3d:
            return 1.0
        # Clamp z between MIN_DEPTH and MAX_DEPTH
        z = max(MIN_DEPTH, min(MAX_DEPTH, self.pos.z))
        # Linear interpolation: scale goes from 1.0 to DEPTH_SCALE_FACTOR
        normalized = z / MAX_DEPTH
        return 1.0 - (normalized * (1.0 - DEPTH_SCALE_FACTOR))
    
    def apply_depth_scale(self, frame):
        """Scale a frame based on current depth position."""
        if not enable_3d:
            return frame
        scale = self.get_depth_scale()
        if scale == 1.0:
            return frame
        w, h = frame.get_size()
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return pygame.transform.smoothscale(frame, (new_w, new_h))

    def handle_input(self, keys):
        """Handle movement input and select the active frame set.

        Behavior:
        - There are two frame-sets: idle_set (frames 0/1) and move_set (frames 2/3).
        - While in a set, the player cycles between the two frames.
        - If the 's' key is pressed, the second frame of the active set is held permanently
          until 's' is released.
        """
        moved = False

        # Evaluate which direction keys are pressed regardless of movement success
        left_pressed = bool(keys[pygame.K_a])
        right_pressed = bool(keys[pygame.K_d])
        
        # In 3D mode, W/S control depth (forward/back perspective)
        # In 2D mode, W is jump and S is unused
        if enable_3d:
            up_pressed = False  # W used for depth in 3D mode
            forward_pressed = bool(keys[pygame.K_w])
            backward_pressed = bool(keys[pygame.K_s])
        else:
            up_pressed = bool(keys[pygame.K_w]) or bool(keys[pygame.K_SPACE])
            forward_pressed = False
            backward_pressed = False
        
        down_pressed = False

        # 3D depth movement (W = move forward/closer, S = move back/away) - first/third person perspective
        if enable_3d:
            if forward_pressed:  # Move forward (decrease z, closer to screen)
                self.pos.z = max(MIN_DEPTH, self.pos.z - self.depth_speed)
                moved = True
            if backward_pressed:  # Move backward (increase z, away from screen)
                self.pos.z = min(MAX_DEPTH, self.pos.z + self.depth_speed)
                moved = True
            # Space bar still allows jumping in 3D mode
            if keys[pygame.K_SPACE]:
                up_pressed = True

        # store pressed state for use in update (wall slide etc.)
        self.left_pressed = left_pressed
        self.right_pressed = right_pressed
        self.up_pressed = up_pressed

        # Movement (WASD controls)
        can_fly = current_mode == "math"
        if self.side_view:
            # side-view: left/right movement
            half_w = self.rect.width / 2
            if left_pressed and (self.pos.x - half_w) > 0:
                self.pos.x -= self.speed
                moved = True
            if right_pressed and (self.pos.x + half_w) < SCREEN_WIDTH:
                self.pos.x += self.speed
                moved = True

            # Jump / fly handling
            if can_fly:
                # flying mode: holding up gives upward thrust
                if up_pressed:
                    self.vy = -6
                    self.on_ground = False
                    moved = True
            else:
                # normal jump/double-jump/wall-jump logic (edge-triggered)
                if up_pressed and not self.prev_up_pressed:
                    if self.on_ground:
                        self.vy = self.jump_strength
                        self.on_ground = False
                        moved = True
                    elif self.on_wall:
                        # wall jump: give a vertical impulse plus horizontal impulse away from wall
                        # slightly reduce vertical power for wall-jump to feel more natural
                        self.vy = int(self.jump_strength * 0.9)
                        if self.wall_dir == "left":
                            # jump to the right with horizontal velocity
                            self.vx = 10
                        elif self.wall_dir == "right":
                            # jump to the left
                            self.vx = -10
                        self.on_wall = False
                        moved = True
                    elif self.jumps_left > 0:
                        self.vy = self.jump_strength
                        self.jumps_left -= 1
                        moved = True
        else:
            # top-down fallback (WASD)
            half_w = self.rect.width / 2
            half_h = self.rect.height / 2
            if left_pressed and (self.pos.x - half_w) > 0:
                self.pos.x -= self.speed
                moved = True
            if right_pressed and (self.pos.x + half_w) < SCREEN_WIDTH:
                self.pos.x += self.speed
                moved = True
            if up_pressed and (self.pos.y - half_h) > 0:
                self.pos.y -= self.speed
                moved = True
            if down_pressed and (self.pos.y + half_h) < MATRIX_HEIGHT:
                self.pos.y += self.speed
                moved = True

        # Choose direction based on input
        # prefer left/right for side-view; use 'up' when jumping
        if self.side_view:
            # prefer left/right for side-view; use 'up' when jumping
            if left_pressed:
                direction = "left"
            elif right_pressed:
                direction = "right"
            elif not self.on_ground or up_pressed:
                direction = "up"
            else:
                direction = "down"
        else:
            # top-down: map W to up, S to down, A to left, D to right
            if left_pressed:
                direction = "left"
            elif right_pressed:
                direction = "right"
            elif up_pressed:
                direction = "up"
            elif down_pressed:
                direction = "down"
            else:
                direction = "down"

        # select frames for this direction and ensure at least two
        dir_set = self.dir_frames.get(direction, [])
        if len(dir_set) == 0:
            dir_set = [
                pygame.Surface((48, 48), pygame.SRCALPHA),
                pygame.Surface((48, 48), pygame.SRCALPHA),
            ]
        elif len(dir_set) == 1:
            f0 = dir_set[0]
            dir_set = [f0, pygame.transform.flip(f0, True, False)]

        # Determine new_set: prefer idle when standing still and on ground
        # only consider left/right/up as direction inputs; exclude 's' (down) from movement detection
        any_dir_pressed = left_pressed or right_pressed or up_pressed

        # If any directional key is pressed, update facing and show movement frames
        if any_dir_pressed:
            self.set_facing(direction)
            self.set_active_direction_frames(direction)
        else:
            # when on ground and no direction pressed, prefer the global idle
            # animation (player facing forward) rather than re-using the
            # last-movement frames which can make the sprite appear "stuck"
            # facing right after a short tap.
            if self.on_ground:
                if getattr(self, "idle_frames", None) and len(self.idle_frames) >= 2:
                    # use the global idle pair (usually 1st/2nd frames)
                    self.active_set = self.idle_frames[:2]
                    self.frame_index = 0
                    self.animation_timer = 0
                    self.image = self.active_set[self.frame_index]
                    self.sync_rect()
                else:
                    # fallback to per-facing idle
                    self.set_idle_for_facing()

        # store pressed state for update-time animation control
        self.any_dir_pressed = any_dir_pressed

        # remember upward press for edge-triggered jumps next frame
        self.prev_up_pressed = up_pressed

        return moved
    
    def handle_mouse_attack(self, mouse_buttons):
        """Handle mouse button attack input"""
        # Left mouse button (index 0)
        if mouse_buttons[0] and not self.is_attacking and self.attack_cooldown == 0:
            self.start_attack()
    
    def start_attack(self):
        """Initiate attack animation and hitbox"""
        self.is_attacking = True
        self.attack_timer = 0
        self.frame_index = 0
    
    def get_attack_hitbox(self):
        """Return the attack hitbox rect based on facing direction"""
        if not self.is_attacking:
            return None
        
        # Create hitbox in front of player based on facing direction
        hitbox_width = self.attack_range
        hitbox_height = self.rect.height
        
        if self.facing == "right" or (not hasattr(self, 'last_direction') and self.right_pressed):
            # Attack to the right
            hitbox = pygame.Rect(self.rect.right, self.rect.top, hitbox_width, hitbox_height)
        elif self.facing == "left" or self.left_pressed:
            # Attack to the left
            hitbox = pygame.Rect(self.rect.left - hitbox_width, self.rect.top, hitbox_width, hitbox_height)
        elif self.facing == "up":
            # Attack upward
            hitbox = pygame.Rect(self.rect.left, self.rect.top - hitbox_width, hitbox_height, hitbox_width)
        else:  # down or default
            # Attack downward
            hitbox = pygame.Rect(self.rect.left, self.rect.bottom, hitbox_height, hitbox_width)
        
        return hitbox

    def update(self):
        # ensure active_set exists; prefer idle frames when available
        if not hasattr(self, "active_set") or not self.active_set:
            if getattr(self, "idle_frames", None):
                self.active_set = self.idle_frames[:2]
            else:
                self.active_set = (
                    self.frames[:2] if len(self.frames) >= 2 else self.frames
                )

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Handle attack animation
        if self.is_attacking:
            self.attack_timer += 1
            
            # Determine which punch frames to use based on facing direction
            # Only use left or right punch frames (fly frames saved for future fly mechanic)
            if self.facing == "left" or self.left_pressed:
                punch_list = self.punch_frames["left"]
            elif self.facing == "right" or self.right_pressed:
                punch_list = self.punch_frames["right"]
            else:
                # Default to right if no clear direction
                punch_list = self.punch_frames["right"]
            
            # Cycle through the appropriate directional punch frames
            frame_idx = (self.attack_timer // 2) % len(punch_list)
            base_frame = punch_list[frame_idx]
            
            self.image = self.apply_depth_scale(base_frame)
            self.sync_rect()
            
            # End attack after duration
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.attack_timer = 0
                self.attack_cooldown = self.attack_cooldown_duration
            return  # Skip normal animation when attacking

        # side-view physics: apply gravity and ground collision (use self.pos for coordinates)
        if self.side_view:
            # apply horizontal velocity (from impulses like wall-jump) to pos.x
            if abs(self.vx) > 0.5:
                self.pos.x += self.vx
                # decay horizontal impulse each frame
                self.vx *= 0.85
            else:
                self.vx = 0
            # clamp horizontal bounds using half-width
            half_w = self.rect.width / 2
            if self.pos.x - half_w < 0:
                self.pos.x = half_w
                self.vx = 0
            elif self.pos.x + half_w > SCREEN_WIDTH:
                self.pos.x = SCREEN_WIDTH - half_w
                self.vx = 0

            # wall slide detection: if holding into a wall while airborne, slow descent
            self.on_wall = False
            self.wall_dir = None
            if not self.on_ground:
                if self.left_pressed and (self.pos.x - half_w) <= 0:
                    self.on_wall = True
                    self.wall_dir = "left"
                    # slow fall (slightly slower clamp for a natural feel)
                    self.vy = min(self.vy, 3)
                elif self.right_pressed and (self.pos.x + half_w) >= SCREEN_WIDTH:
                    self.on_wall = True
                    self.wall_dir = "right"
                    self.vy = min(self.vy, 3)

            # apply gravity unless flying mode (handled via handle_input thrust)
            if not (current_mode == "math" and self.up_pressed):
                self.vy += self.gravity

            # apply vertical velocity to pos.y
            self.pos.y += int(self.vy)

            # ensure player doesn't fall below ground (pos is center y)
            half_h = self.rect.height / 2
            if self.pos.y + half_h >= MATRIX_HEIGHT:
                # snap to ground
                self.pos.y = MATRIX_HEIGHT - half_h
                self.vy = 0
                self.on_ground = True
                # reset jumps
                self.jumps_left = self.max_jumps
                self.is_jumping = False
            else:
                self.on_ground = False
                # Player is in the air, show jump frame
                if not self.on_wall:
                    self.is_jumping = True

        # Note: 's' key functionality removed — no lock or drop-on-S behavior here.

        # If jumping (in the air), display the appropriate jump frame
        if self.is_jumping and self.side_view:
            # Determine which jump frame to use based on last movement direction
            if self.facing == "right" or self.right_pressed:
                base_frame = self.jump_frame_right
            else:
                # Default to left jump frame for left or any other direction
                base_frame = self.jump_frame_left
            # Apply depth scaling if 3D is enabled
            self.image = self.apply_depth_scale(base_frame)
            self.sync_rect()
            return  # Skip normal animation when jumping

        # otherwise advance animation. Movement frames animate while direction keys are pressed.
        if getattr(self, "any_dir_pressed", False):
            speed_threshold = max(1, 60 // self.animation_speed)
        else:
            # idle animates slower
            speed_threshold = max(1, 60 // self.idle_animation_speed)

        self.animation_timer += 1
        if self.animation_timer >= speed_threshold:
            self.animation_timer = 0
            # advance within active set (wrap around)
            self.frame_index = (self.frame_index + 1) % len(self.active_set)
            base_frame = self.active_set[self.frame_index]
            # Apply depth scaling if 3D is enabled
            self.image = self.apply_depth_scale(base_frame)
            # keep rect centered on logical pos
            self.sync_rect()

        # always ensure rect matches logical position
        self.sync_rect()


class MatrixCharacter(pygame.sprite.Sprite):
    """Falling matrix characters that the player must collect"""

    def __init__(self, x, y, char, point_value=1):
        super().__init__()
        font = pygame.font.SysFont("Consolas", 20)
        self.image = font.render(char, True, GREEN)
        # store 3D position (use x/y for now)
        self.pos = pygame.math.Vector3(x, y, 0)
        self.rect = self.image.get_rect(topleft=(int(self.pos.x), int(self.pos.y)))
        self.char = char
        self.point_value = point_value
        self.speed = drop_speed

    def update(self):
        self.pos.y += self.speed
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        if self.pos.y > MATRIX_HEIGHT:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    """Red matrix characters that damage the player"""

    def __init__(self, x, y):
        super().__init__()
        font = pygame.font.SysFont("Consolas", 24, bold=True)
        self.image = font.render("X", True, RED)
        self.pos = pygame.math.Vector3(x, y, 0)
        self.rect = self.image.get_rect(topleft=(int(self.pos.x), int(self.pos.y)))
        self.speed = drop_speed + 1
        
        # Knockback physics
        self.knocked_back = False
        self.knockback_vx = 0  # Horizontal knockback velocity
        self.knockback_vy = 0  # Vertical knockback velocity
        self.knockback_decay = 0.95  # Velocity decay per frame
        self.was_hit_by_player = False  # Track if player destroyed this enemy

    def update(self):
        if self.knocked_back:
            # Apply knockback velocity
            self.pos.x += self.knockback_vx
            self.pos.y += self.knockback_vy
            
            # Decay knockback over time
            self.knockback_vx *= self.knockback_decay
            self.knockback_vy *= self.knockback_decay
            
            # Check if enemy flew off screen edges
            if (self.pos.x < -50 or self.pos.x > SCREEN_WIDTH + 50 or
                self.pos.y < -50 or self.pos.y > SCREEN_HEIGHT + 50):
                self.kill()  # Destroy when off screen
        else:
            # Normal falling behavior
            self.pos.y += self.speed
            if self.pos.y > MATRIX_HEIGHT:
                self.kill()
        
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
    
    def apply_knockback(self, direction_x, direction_y, force=20):
        """Apply knockback force in a direction"""
        self.knocked_back = True
        self.was_hit_by_player = True  # Mark that player destroyed this enemy
        self.knockback_vx = direction_x * force
        self.knockback_vy = direction_y * force


class Pill(pygame.sprite.Sprite):
    """Pills that unlock 3D mode (red) or keep 2D mode (blue)"""
    
    def __init__(self, x, y, pill_type):
        super().__init__()
        self.pill_type = pill_type  # "red" or "blue"
        self.pos = pygame.math.Vector3(x, y, 0)
        
        # Create pill visual (capsule shape)
        width = 30
        height = 15
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw capsule
        color = RED if pill_type == "red" else (0, 100, 255)  # Blue
        # Draw circles on ends
        pygame.draw.circle(self.image, color, (height // 2, height // 2), height // 2)
        pygame.draw.circle(self.image, color, (width - height // 2, height // 2), height // 2)
        # Draw rectangle in middle
        pygame.draw.rect(self.image, color, (height // 2, 0, width - height, height))
        
        # Add highlight
        highlight_color = (255, 100, 100) if pill_type == "red" else (100, 150, 255)
        pygame.draw.circle(self.image, highlight_color, (height // 2 + 3, height // 3), 3)
        
        self.rect = self.image.get_rect(topleft=(int(self.pos.x), int(self.pos.y)))
        self.speed = drop_speed - 0.5  # Slower than regular characters
    
    def update(self):
        self.pos.y += self.speed
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        if self.pos.y > MATRIX_HEIGHT:
            self.kill()


class InGameConsole:
    """A small in-game master terminal for quick file viewing/editing and commands.

    Toggle with the backquote key (`). Commands (type at prompt and press Enter):
    - help                  : show commands
    - open <path>           : open a file into the buffer
    - show [start end]      : show buffer lines (defaults to first 20)
    - edit <line> <text...> : replace a line in the buffer (1-based index)
    - save                  : save buffer back to opened file
    - close                 : close buffer
    - exit                  : close console
    """

    def __init__(self, game):
        self.game = game
        self.active = False
        self.log = ["In-game console ready. Type 'help' for commands."]
        self.input = ""
        self.font = pygame.font.SysFont("Consolas", 16)
        self.buffer = []
        self.file_path = None

    def toggle(self):
        self.active = not self.active
        if self.active:
            pygame.key.set_repeat(300, 50)
        else:
            pygame.key.set_repeat()

    def append_log(self, text):
        for line in str(text).splitlines():
            self.log.append(line)
        # keep log bounded
        if len(self.log) > 200:
            self.log = self.log[-200:]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # toggle console
            if event.key == pygame.K_BACKQUOTE:
                self.toggle()
                return True

            if not self.active:
                return False

            if event.key == pygame.K_RETURN:
                cmd = self.input.strip()
                self.input = ""
                if cmd:
                    self.append_log(f"> {cmd}")
                    self.execute(cmd)
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
                return True
            else:
                ch = getattr(event, "unicode", "")
                if ch:
                    self.input += ch
                    return True
        return False

    def execute(self, cmd):
        parts = cmd.split()
        if not parts:
            return
        op = parts[0].lower()
        if op == "help":
            self.append_log(
                "Commands: help, open <path>, show [s e], edit <line> <text>, save, close, exit"
            )
        elif op == "open" and len(parts) >= 2:
            path = " ".join(parts[1:])
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.buffer = f.read().splitlines()
                self.file_path = path
                self.append_log(f"Opened '{path}' ({len(self.buffer)} lines)")
            except Exception as e:
                self.append_log(f"Error opening '{path}': {e}")
        elif op == "show":
            start = 1
            end = min(20, len(self.buffer))
            if len(parts) >= 3:
                try:
                    start = int(parts[1])
                    end = int(parts[2])
                except Exception:
                    pass
            for i in range(max(1, start), min(end, len(self.buffer)) + 1):
                self.append_log(f"{i:4d}: {self.buffer[i-1]}")
        elif op == "edit" and len(parts) >= 3:
            try:
                idx = int(parts[1]) - 1
                if 0 <= idx < len(self.buffer):
                    new_text = " ".join(parts[2:])
                    self.buffer[idx] = new_text
                    self.append_log(f"Line {idx+1} updated")
                else:
                    self.append_log("Line index out of range")
            except Exception as e:
                self.append_log(f"Edit error: {e}")
        elif op == "save":
            if not self.file_path:
                self.append_log("No file open to save")
            else:
                try:
                    with open(self.file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(self.buffer))
                    self.append_log(f"Saved '{self.file_path}'")
                except Exception as e:
                    self.append_log(f"Save error: {e}")
        elif op == "close":
            self.buffer = []
            self.file_path = None
            self.append_log("Buffer closed")
        elif op == "exit":
            self.toggle()
        else:
            self.append_log(f"Unknown command: {op}")

    def draw(self, surf):
        if not self.active:
            return
        w, h = surf.get_size()
        # draw semi-transparent background
        overlay_h = int(h * 0.4)
        rect = pygame.Surface((w, overlay_h), pygame.SRCALPHA)
        rect.fill((10, 10, 10, 200))
        surf.blit(rect, (0, h - overlay_h))

        # draw log
        padding = 8
        y = h - overlay_h + padding
        max_lines = (overlay_h - 60) // 18
        for line in self.log[-max_lines:]:
            txt = self.font.render(line, True, WHITE)
            surf.blit(txt, (padding, y))
            y += 18

        # draw input prompt
        prompt = "> " + self.input
        txt = self.font.render(prompt, True, GREEN)
        surf.blit(txt, (padding, h - 28))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("32-bit Processor")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        self.font_large = pygame.font.SysFont("Consolas", 48)
        self.font_medium = pygame.font.SysFont("Consolas", 24)
        self.font_small = pygame.font.SysFont("Consolas", 16)

        # Game sprites
        self.player = None
        self.characters = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.pills = pygame.sprite.Group()  # Red/Blue pills
        self.all_sprites = pygame.sprite.Group()

        # Game variables
        self.score = 0
        self.keys_collected = 0  # Track number of keys/characters collected
        self.health = 100
        self.spawn_timer = 0
        self.game_time = 0
        self.current_round = 1  # Track current round
        self.pill_offered = False  # Track if pills have been offered
        self.pill_spawn_time = 300  # Time before pills spawn (5 seconds at 60fps)
        # Chat / input state
        self.chat_active = False
        self.chat_text = ""
        # map number keys to modes
        self.mode_keys = {
            pygame.K_0: "default",
            pygame.K_1: "numbers",
            pygame.K_2: "hex",
            pygame.K_3: "binary",
            pygame.K_4: "japanese",
            pygame.K_5: "math",
        }
        # in-game console
        self.console = InGameConsole(self)

    def show_menu(self):
        """Display the main menu"""
        menu_running = True
        while menu_running and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    menu_running = False
                if event.type == pygame.KEYDOWN:
                    # Any key starts the game
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        menu_running = False
                    else:
                        self.start_game()
                        menu_running = False

            self.screen.fill(BLACK)
            title = self.font_large.render("WORMWOOD", True, GREEN)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(title, title_rect)

            prompt = self.font_medium.render("Press any key", True, WHITE)
            prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(prompt, prompt_rect)

            pygame.display.flip()
            self.clock.tick(60)

    def start_game(self):
        """Initialize and start the game"""
        self.state = STATE_PLAYING
        self.player = Player(SCREEN_WIDTH // 2, MATRIX_HEIGHT - 100)
        # snap player to ground (use pos.y as center y)
        half_h = self.player.rect.height / 2
        self.player.pos.y = MATRIX_HEIGHT - half_h
        self.player.sync_rect()
        self.all_sprites.add(self.player)
        self.score = 0
        self.keys_collected = 0  # Reset keys collected
        self.health = 100
        self.spawn_timer = 0
        self.game_time = 0
        self.current_round = 1  # Reset to round 1
        self.pill_offered = False
        self.characters.empty()
        self.enemies.empty()
        self.pills.empty()
    
    def start_next_round(self):
        """Start the next round with increased difficulty"""
        global drop_speed
        self.current_round += 1
        self.state = STATE_PLAYING
        # Keep score from previous round
        self.health = 100  # Regenerate health to 100
        self.spawn_timer = 0
        drop_speed += 1  # Increase speed each round
        self.characters.empty()
        self.enemies.empty()
        self.pills.empty()
        print(f"Starting Round {self.current_round} - Speed: {drop_speed}")

    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            # allow toggling the console with backquote at any time
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                self.console.toggle()
                # let the console handle the toggle and skip other handling
                if self.console.active:
                    continue

            # If console is active, give it priority to handle events
            if self.console.active:
                handled = self.console.handle_event(event)
                if handled:
                    continue
            # Always allow quitting
            if event.type == pygame.QUIT:
                self.running = False

            # If chat is active, capture text input and editing keys
            if self.chat_active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # send chat (for now, just print to console) and close chat
                        print("CHAT:", self.chat_text)
                        self.chat_text = ""
                        self.chat_active = False
                        try:
                            pygame.key.stop_text_input()
                        except Exception:
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        self.chat_text = self.chat_text[:-1]
                    else:
                        # use event.unicode to get the typed character
                        ch = getattr(event, "unicode", "")
                        if ch:
                            self.chat_text += ch
                continue

            # Not chatting: handle global keys
            if event.type == pygame.KEYDOWN:
                # toggle chat with RETURN
                if event.key == pygame.K_RETURN:
                    self.chat_active = True
                    self.chat_text = ""
                    try:
                        pygame.key.start_text_input()
                    except Exception:
                        pass
                    continue

                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                    self.characters.empty()
                    self.enemies.empty()
                    self.all_sprites.empty()
                    continue

                # number keys switch modes (1..5, 0 for default)
                if event.key in self.mode_keys:
                    global current_mode
                    current_mode = self.mode_keys[event.key]
                    print(f"mode -> {current_mode}")
                    continue

    def update(self):
        """Update game logic"""
        if self.state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        
        self.player.handle_input(keys)
        self.player.handle_mouse_attack(mouse_buttons)

        # Check for enemies that were destroyed (before update removes them)
        enemies_before_update = list(self.enemies)
        
        # Update all sprites
        self.all_sprites.update()
        
        # Award 10 points for each enemy destroyed by player
        enemies_after_update = list(self.enemies)
        for enemy in enemies_before_update:
            if enemy not in enemies_after_update and enemy.was_hit_by_player:
                self.score += 10
                print(f"Enemy destroyed! +10 points (Total: {self.score})")
        
        # Check if player completed a round (200 points)
        if self.score >= 200:
            self.state = STATE_ROUND_COMPLETE
            return

        # Spawn pills only when player reaches 999 points (only once per round)
        # After round 3, pills are required to continue
        if not self.pill_offered and self.score >= 999:
            if self.current_round >= 3:
                # Round 3+: Pills are mandatory to continue playing
                self.spawn_pills()
                self.pill_offered = True
                print("CRITICAL: Choose a pill to continue!")
            else:
                # Before round 3: Pills are optional bonus
                self.spawn_pills()
                self.pill_offered = True

        # Spawn new characters
        self.spawn_timer += 1
        if self.spawn_timer > 20:
            self.spawn_characters()
            self.spawn_timer = 0

        # Check collisions with collectable characters
        for char_sprite in self.characters:
            if pygame.sprite.spritecollide(
                self.player, pygame.sprite.Group(char_sprite), True
            ):
                self.score += char_sprite.point_value
                self.keys_collected += 1  # Increment keys collected counter

        # Check collisions with enemies - PRECISE TIMING REQUIRED
        # Player must be attacking within the parry window when enemy touches them
        for enemy in list(self.enemies):
            if pygame.sprite.spritecollide(
                self.player, pygame.sprite.Group(enemy), False  # Don't auto-remove
            ):
                # Enemy is touching player - check if player is attacking at this exact moment
                if self.player.is_attacking and self.player.attack_timer <= self.player.attack_parry_window:
                    # Perfect timing! Calculate knockback direction from player to enemy
                    dx = enemy.pos.x - self.player.pos.x
                    dy = enemy.pos.y - self.player.pos.y
                    # Normalize direction
                    distance = max(1, (dx**2 + dy**2)**0.5)
                    knock_dir_x = dx / distance
                    knock_dir_y = dy / distance
                    
                    # Apply knockback force (increased for faster flight)
                    enemy.apply_knockback(knock_dir_x, knock_dir_y, force=40)
                    print("PERFECT PARRY! Enemy knocked away!")
                else:
                    # Missed the timing window - take damage and still knock enemy back
                    dx = enemy.pos.x - self.player.pos.x
                    dy = enemy.pos.y - self.player.pos.y
                    distance = max(1, (dx**2 + dy**2)**0.5)
                    knock_dir_x = dx / distance
                    knock_dir_y = dy / distance
                    
                    enemy.apply_knockback(knock_dir_x, knock_dir_y, force=30)
                    self.health -= 10
                    if self.health <= 0:
                        self.state = STATE_GAME_OVER
                    print("Missed parry! -10 health")
        
        # Attack hitbox for destroying enemies at range
        if self.player.is_attacking:
            attack_hitbox = self.player.get_attack_hitbox()
            if attack_hitbox:
                for enemy in list(self.enemies):
                    # Only count if enemy is NOT touching player (range attack, not parry)
                    if attack_hitbox.colliderect(enemy.rect) and not self.player.rect.colliderect(enemy.rect):
                        # Calculate knockback direction based on player's facing direction
                        if self.player.facing == "right" or self.player.right_pressed:
                            knock_dir_x, knock_dir_y = 1, 0
                        elif self.player.facing == "left" or self.player.left_pressed:
                            knock_dir_x, knock_dir_y = -1, 0
                        elif self.player.facing == "up":
                            knock_dir_x, knock_dir_y = 0, -1
                        else:  # down
                            knock_dir_x, knock_dir_y = 0, 1
                        
                        enemy.apply_knockback(knock_dir_x, knock_dir_y, force=35)

        # Check collisions with pills
        for pill in self.pills:
            if pygame.sprite.spritecollide(
                self.player, pygame.sprite.Group(pill), True
            ):
                global enable_3d
                if pill.pill_type == "red":
                    enable_3d = True
                    print("RED PILL CHOSEN: 3D mode activated! Use W (forward) and S (backward) to move in depth.")
                elif pill.pill_type == "blue":
                    enable_3d = False
                    self.player.pos.z = 0  # Reset depth
                    print("BLUE PILL CHOSEN: Staying in 2D mode. The choice is made.")
                # Remove all remaining pills once one is taken
                self.pills.empty()

        # Increase difficulty
        self.game_time += 1
        if self.game_time % 300 == 0:  # Every 5 seconds
            global drop_speed
            drop_speed = min(drop_speed + 0.5, 10)

        # End game if health is depleted
        if self.health <= 0:
            self.state = STATE_GAME_OVER

    def spawn_characters(self):
        """Spawn falling matrix characters"""
        modes = get_random_string()
        chars = modes[current_mode]

        # Spawn collectables (green)
        for _ in range(random.randint(1, 3)):
            x = random.randint(0, SCREEN_WIDTH - 20)
            y = random.randint(-50, -10)
            char = random.choice(chars)
            sprite = MatrixCharacter(x, y, char, point_value=1)
            self.characters.add(sprite)
            self.all_sprites.add(sprite)

        # Spawn enemies (red)
        if random.random() > 0.7:
            x = random.randint(0, SCREEN_WIDTH - 30)
            y = random.randint(-50, -10)
            enemy = Enemy(x, y)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

    def spawn_pills(self):
        """Spawn red and blue pills for the player to choose"""
        # Spawn red pill (left side)
        red_x = SCREEN_WIDTH // 3
        red_y = -50
        red_pill = Pill(red_x, red_y, "red")
        self.pills.add(red_pill)
        self.all_sprites.add(red_pill)
        
        # Spawn blue pill (right side)
        blue_x = (SCREEN_WIDTH * 2) // 3
        blue_y = -50
        blue_pill = Pill(blue_x, blue_y, "blue")
        self.pills.add(blue_pill)
        self.all_sprites.add(blue_pill)
        
        print("999 POINTS REACHED! CHOICE: Red pill (3D mode) or Blue pill (stay 2D)?")


    def draw(self):
        """Draw everything on screen"""
        # Processor-style background: dark grid and subtle lines
        self.screen.fill((10, 10, 12))
        # draw a faint grid in the matrix area
        grid_color = (20, 40, 20)
        cell = 20
        for gx in range(0, SCREEN_WIDTH, cell):
            pygame.draw.line(self.screen, grid_color, (gx, 0), (gx, MATRIX_HEIGHT), 1)
        for gy in range(0, MATRIX_HEIGHT, cell):
            pygame.draw.line(self.screen, grid_color, (0, gy), (SCREEN_WIDTH, gy), 1)

        # processor label
        label = self.font_small.render("32-bit Processor", True, DARK_GREEN)
        self.screen.blit(label, (10, 10))

        if self.state == STATE_PLAYING:
            # Draw ground line
            pygame.draw.line(
                self.screen,
                DARK_GREEN,
                (0, MATRIX_HEIGHT),
                (SCREEN_WIDTH, MATRIX_HEIGHT),
                2,
            )

            # Draw sprites
            self.all_sprites.draw(self.screen)

            # Draw HUD with improved layout
            # Score on the left
            score_text = self.font_medium.render(f"Score: {self.score}", True, GREEN)
            self.screen.blit(score_text, (10, MATRIX_HEIGHT + 20))
            
            # Keys collected below score
            keys_text = self.font_small.render(f"Keys Collected: {self.keys_collected}", True, GREEN)
            self.screen.blit(keys_text, (10, MATRIX_HEIGHT + 55))

            # Health on the right
            health_text = self.font_medium.render(
                f"Health: {self.health}%", True, RED if self.health < 30 else GREEN
            )
            self.screen.blit(health_text, (SCREEN_WIDTH - 250, MATRIX_HEIGHT + 20))

            # Speed in the center
            speed_text = self.font_small.render(f"Speed: {drop_speed:.1f}", True, GREEN)
            self.screen.blit(speed_text, (SCREEN_WIDTH // 2 - 50, MATRIX_HEIGHT + 20))
            
            # 3D mode indicator and depth
            if enable_3d:
                mode_text = self.font_small.render("3D MODE (W=Forward S=Back)", True, RED)
                self.screen.blit(mode_text, (SCREEN_WIDTH // 2 - 120, MATRIX_HEIGHT + 55))
                
                if self.player:
                    depth_text = self.font_small.render(f"Depth: {int(self.player.pos.z)}", True, GREEN)
                    self.screen.blit(depth_text, (SCREEN_WIDTH // 2 - 50, MATRIX_HEIGHT + 80))


            # Draw chat box if active
            if getattr(self, "chat_active", False):
                box_h = 28
                box_w = 600
                box_x = 20
                box_y = MATRIX_HEIGHT + 60
                pygame.draw.rect(
                    self.screen, (5, 5, 5), (box_x - 2, box_y - 2, box_w + 4, box_h + 4)
                )
                pygame.draw.rect(
                    self.screen, (30, 30, 30), (box_x, box_y, box_w, box_h)
                )
                chat_surf = self.font_small.render(self.chat_text, True, GREEN)
                self.screen.blit(chat_surf, (box_x + 6, box_y + 6))

            # draw in-game console overlay if active
            try:
                if getattr(self, "console", None) and self.console.active:
                    self.console.draw(self.screen)
            except Exception:
                # protect draw from crashing the game
                pass

        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        
        elif self.state == STATE_ROUND_COMPLETE:
            self.draw_round_complete()

        pygame.display.flip()

    def draw_round_complete(self):
        """Draw round complete screen"""
        title = self.font_large.render(f"ROUND {self.current_round} COMPLETE!", True, GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)

        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(score_text, score_rect)
        
        # Calculate rounds until end or pill choice
        rounds_until_end = 3 - self.current_round
        
        if rounds_until_end > 0:
            # Show warning message
            warning = self.font_small.render(f"THE END IS NEAR", True, RED)
            warning_rect = warning.get_rect(center=(SCREEN_WIDTH // 2, 320))
            self.screen.blit(warning, warning_rect)
            
            rounds_text = self.font_small.render(f"{rounds_until_end} rounds until you must reach 999 points", True, WHITE)
            rounds_rect = rounds_text.get_rect(center=(SCREEN_WIDTH // 2, 360))
            self.screen.blit(rounds_text, rounds_rect)
            
            pill_text = self.font_small.render("Choose the Red or Blue pill to continue", True, GREEN)
            pill_rect = pill_text.get_rect(center=(SCREEN_WIDTH // 2, 390))
            self.screen.blit(pill_text, pill_rect)
        else:
            # Round 3 completed - must get pills
            final_warning = self.font_small.render("FINAL CHANCE: Reach 999 points for the pills!", True, RED)
            final_rect = final_warning.get_rect(center=(SCREEN_WIDTH // 2, 340))
            self.screen.blit(final_warning, final_rect)

        continue_text = self.font_small.render("Press SPACE to continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 470))
        self.screen.blit(continue_text, continue_rect)

        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.current_round >= 3:
                        # After round 3, game ends if they didn't get 999
                        self.state = STATE_GAME_OVER
                    else:
                        # Start next round
                        self.start_next_round()

    def draw_game_over(self):
        """Draw game over screen"""
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        final_score = self.font_medium.render(f"Final Score: {self.score}", True, GREEN)
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(final_score, score_rect)

        restart = self.font_small.render("Press SPACE to return to Menu", True, WHITE)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(restart, restart_rect)

        # Handle menu input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.state = STATE_MENU
                    self.characters.empty()
                    self.enemies.empty()
                    self.all_sprites.empty()

    def run(self):
        """Main game loop"""
        while self.running:
            if self.state == STATE_MENU:
                self.show_menu()
            elif self.state == STATE_PLAYING:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(60)
            elif self.state == STATE_GAME_OVER:
                self.draw()
                self.clock.tick(60)
            elif self.state == STATE_ROUND_COMPLETE:
                self.draw()
                self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
