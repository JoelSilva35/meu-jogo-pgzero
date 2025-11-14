# ==========================
# IMPORTS
# ==========================
import pgzrun
import random
import math
from pygame import Rect

# ==========================
# CONFIGURAÇÕES GLOBAIS
# ==========================
WIDTH = 800
HEIGHT = 600
TITLE = "COP PARÁ"
SUB_TITLE = "O Desafio da Amazônia"
GRAVITY = 0.5
PLAYER_SPEED = 4
JUMP_VELOCITY = -13
ENEMY_SPEED = 2
MAX_FALL_SPEED = 10
PLATFORM_COLOR = (100, 50, 0)  # marrom

# Variáveis globais
game_state = "MENU"  # MENU, PLAYING, GAME_OVER
music_on = True

# ==========================
# FUNÇÕES AUXILIARES
# ==========================
def play_sound(sound_name):
    if music_on:
        try:
            getattr(sounds, sound_name).play()
        except AttributeError:
            print(f"Sound file '{sound_name}' not found.")

def toggle_music():
    global music_on
    music_on = not music_on
    if music_on:
        music.play("music")
    else:
        music.stop()

# ==========================
# CLASSES DO JOGO
# ==========================
class Character:
    def __init__(self, name, x, y, idle_frames, move_frames, jump_frames=None):
        self.idle_frames = idle_frames
        self.move_frames = move_frames
        self.jump_frames = jump_frames or [idle_frames[0]]
        self.actor = Actor(idle_frames[0])
        self.actor.pos = (x, y)
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False
        self.animation_frame = 0
        self.animation_timer = 0
        self.direction = 1
        self.current_animation = "idle"
        self.flip_x = False

    def apply_gravity(self):
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED

    def update_position(self, platforms):
        # Movimento horizontal
        self.actor.x += self.velocity_x
        self.handle_collisions_x(platforms)

        # Movimento vertical
        self.apply_gravity()
        self.actor.y += self.velocity_y
        self.on_ground = False
        self.handle_collisions_y(platforms)

    def handle_collisions_x(self, platforms):
        for p in platforms:
            if self.actor.colliderect(p.rect): 
                if self.velocity_x > 0:
                    self.actor.right = p.rect.left
                elif self.velocity_x < 0:
                    self.actor.left = p.rect.right
                self.velocity_x = 0

    def handle_collisions_y(self, platforms):
        for p in platforms:
            if self.actor.colliderect(p.rect): 
                if self.velocity_y > 0:
                    self.actor.bottom = p.rect.top
                    self.on_ground = True
                elif self.velocity_y < 0:
                    self.actor.top = p.rect.bottom
                self.velocity_y = 0

    def update_animation(self, speed):
        frames = self.idle_frames
        # Determina animação
        if not self.on_ground:
            new_animation = "jump"
        elif abs(speed) > 0.5:
            new_animation = "move"
        else:
            new_animation = "idle"

        # Reinicia se mudou de animação
        if new_animation != self.current_animation:
            self.current_animation = new_animation
            self.animation_frame = 0
            self.animation_timer = 0

        # Escolhe frames
        if self.current_animation == "jump":
            frames = self.jump_frames
        elif self.current_animation == "move":
            frames = self.move_frames
        else:
            frames = self.idle_frames

        # Velocidade da animação
        if self.current_animation == "idle":
             frame_speed = 30
        else:
            frame_speed = 8

        # Atualiza frame
        self.animation_timer += 1
        if self.animation_timer >= frame_speed:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            self.actor.image = frames[self.animation_frame]

        # Inverte sprite
        self.actor.flip_x = self.direction == -1

# ==========================
# HERO
# ==========================
class Hero(Character):
    def __init__(self, x, y):
        super().__init__("Hero", x, y,
                         idle_frames=['hero_idle_1', 'hero_idle_2'],
                         move_frames=['hero_run_1', 'hero_run_2', 'hero_run_3'],
                         jump_frames=['hero_jump_1', 'hero_jump_2', 'hero_jump_3'])

    def handle_input(self):
        self.velocity_x = 0
        if keyboard.left:
            self.velocity_x = -PLAYER_SPEED
            self.direction = -1
        if keyboard.right:
            self.velocity_x = PLAYER_SPEED
            self.direction = 1
        if keyboard.up and self.on_ground:
            self.velocity_y = JUMP_VELOCITY
            self.on_ground = False
            self.state = "jump"
            self.animation_frame = 0
            sounds.jump.play()

    def update(self, platforms):
        self.handle_input()
        self.update_animation(self.velocity_x)
        self.update_position(platforms)
        
# ==========================
# ENEMY
# ==========================
class Enemy(Character):
    def __init__(self, x, y, move_range):
        super().__init__("Enemy", x, y,
                         idle_frames=['enemy_1', 'enemy_2'],
                         move_frames=['enemy_run1', 'enemy_run2'])
        self.start_x = x
        self.end_x = x + move_range
        self.velocity_x = ENEMY_SPEED
        self.direction = 1

    def update(self, platforms):
        # Movimento horizontal
        if self.actor.x >= self.end_x:
            self.direction = -1
            self.velocity_x = -ENEMY_SPEED
        elif self.actor.x <= self.start_x:
            self.direction = 1
            self.velocity_x = ENEMY_SPEED

        self.actor.x += self.velocity_x

        # Gravidade e colisão vertical
        self.apply_gravity()
        self.actor.y += self.velocity_y
        self.on_ground = False
        self.handle_collisions_y(platforms)

        # Atualiza animação
        self.update_animation(self.velocity_x)

# ==========================
# PLATFORM
# ==========================
class Platform:
    def __init__(self, x, y, width, height):
        self.rect = Rect(x, y, width, height)

    def draw(self):
        screen.draw.filled_rect(self.rect, PLATFORM_COLOR)
        screen.draw.rect(self.rect, (255, 255, 255))

# ==========================
# BUTTON
# ==========================
class Button:
    def __init__(self, rect, text, action):
        self.rect = rect
        self.text = text
        self.action = action

    def draw(self):
        screen.draw.filled_rect(self.rect, (50, 150, 200))
        screen.draw.rect(self.rect, (255, 255, 255))
        screen.draw.text(self.text, center=self.rect.center, color=(255, 255, 255), fontsize=30)

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False

# ==========================
# OBJETOS DO JOGO
# ==========================
hero = None
enemies = []
platforms = []
menu_buttons = []

def init_game_objects():
    global hero, enemies, platforms
    hero = Hero(50, HEIGHT - 60)
    platforms = [
        Platform(0, HEIGHT - 30, WIDTH, 30),
        Platform(300, HEIGHT - 150, 150, 20),
        Platform(550, HEIGHT - 250, 150, 20),
        Platform(580, HEIGHT - 120, 150, 20)
    ]
    enemies = [
        Enemy(270, HEIGHT - 170  - 20, 150),
        Enemy(600, HEIGHT - 140 - 20, 150)
    ]

def init_menu_buttons():
    global menu_buttons
    if music_on:
        music.play("music")
    start_button_rect = Rect(WIDTH // 5 - 100, HEIGHT // 2 - 50, 200, 50)
    music_button_rect = Rect(WIDTH // 5 - 100, HEIGHT // 2 + 20, 200, 50)
    exit_button_rect = Rect(WIDTH // 5 - 100, HEIGHT // 2 + 90, 200, 50)
    menu_buttons = [
        Button(start_button_rect, "Iniciar", start_game),
        Button(music_button_rect, "Música on/off", toggle_music),
        Button(exit_button_rect, "Sair", exit_game)
    ]

def start_game():
    global game_state
    game_state = "PLAYING"
    init_game_objects()
    if music_on:
        music.play("music")

def exit_game():
    exit()

# ==========================
# PGZERO FUNCTIONS
# ==========================
def draw():
    screen.clear()
    if game_state == "MENU":
        screen.blit("bg_menu", (0, 0))
        screen.draw.text(TITLE, center=(WIDTH // 2, HEIGHT // 8), fontsize=60, color=(255, 255, 0), owidth=1.2, ocolor=(210, 105, 30))
        screen.draw.text(SUB_TITLE, center=(WIDTH // 2, HEIGHT // 5.3), fontsize=40, color=(255, 255, 150), owidth=3, ocolor=(101, 67, 33))
        for button in menu_buttons:
            button.draw()
        screen.draw.text(f"Música: {'LIGADA' if music_on else 'DESLIGADA'}", (10, 10), color=(255, 255, 255))
    elif game_state == "PLAYING":
        screen.blit("bg_game", (0, 0))
        for p in platforms:
            p.draw()
        hero.actor.draw()
        for e in enemies:
            e.actor.draw()
        screen.draw.text("SCORE: 0", (WIDTH - 150, 10), color=(255, 255, 255), fontsize=30)
    elif game_state == "GAME_OVER":
        screen.blit("bg_gameover", (0, 0))
        screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2), fontsize=80, color=(255, 0, 0), owidth=2, ocolor=(0, 0, 0))
        screen.draw.text("Pressione R para recomeçar ou Esc para o menu", center=(WIDTH // 2, HEIGHT // 2 + 70), fontsize=30, color=(255, 255, 255), owidth=1, ocolor=(0, 0, 0))

def update():
    global game_state
    if game_state == "PLAYING":
        hero.update(platforms)
        for e in enemies:
            e.update(platforms)

        # Colisão hero x enemies
        for e in enemies:
            if hero.actor.colliderect(e.actor):
                sounds.hit.play()
                game_state = "GAME_OVER"
                music.stop()
                break

        # Queda hero
        if hero.actor.y > HEIGHT + 50:
            sounds.hit.play()
            game_state = "GAME_OVER"
            music.stop()

    elif game_state == "GAME_OVER":
        if keyboard.r:
            start_game()
        if keyboard.escape:
            game_state = "MENU"
            if music_on:
                music.play("music")

def on_mouse_down(pos):
    if game_state == "MENU":
        for button in menu_buttons:
            if button.is_clicked(pos):
                break

# ==========================
# INICIALIZAÇÃO FINAL
# ==========================
init_menu_buttons()
pgzrun.go()