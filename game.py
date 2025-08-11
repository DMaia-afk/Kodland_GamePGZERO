import pgzrun
from pgzero.rect import Rect
import random
import math

# ==============================================================================
#                      CONFIGURAÇÕES E VARIÁVEIS GLOBAIS
# ==============================================================================

# Dimensões da tela do jogo
WIDTH = 1270
HEIGHT = 720

# Velocidades e constantes de animação e física
STAND_ANIMATION_SPEED = 0.4
WALK_ANIMATION_SPEED = 0.14
ENEMY_WALK_ANIMATION_SPEED = 0.2
FLYMAN_FLY_SPEED = 0.1
CLOUD_SPEED = 3
ENEMY_FOLLOW_SPEED = 3
FLYMAN_FOLLOW_SPEED = 3
FLEEING_SPEED = 8
GRAVITY = 1
JUMP_STRENGTH = -18
ATTACK_ANIMATION_SPEED = 0.05
COIN_ANIMATION_SPEED = 0.3
CARROT_ANIMATION_SPEED = 0.2

# Variáveis de estado do jogo
# Estados: 'MAIN_MENU', 'HOW_TO_PLAY', 'PLAYING', 'BOSS_PRELUDE', 'BOSS_FIGHT', 'GAMEOVER', 'WIN'
game_state = 'MAIN_MENU'
game_timer = 0.0
second_spawner_threshold = 30
boss_fight_threshold = 120
BOSS_PRELUDE_DURATION = 6.0
prelude_timer = 0.0
powerup_duration = 4
powerup_carrots_required = 8
boss_invincibility_duration = 4.0

# Variáveis de controle de áudio e menu
menu_music_playing = False
walk_sound_timer = 0.0
WALK_SOUND_COOLDOWN = 0.3
is_muted = False

mute_button = None
menu_selection = 0

# Listas para gerenciar entidades do jogo
platforms = []
coins = []
carrots = []
enemies = []
spawners = []
flames = []
player = None
boss = None

# ==============================================================================
#                              CLASSES DO JOGO
# ==============================================================================

class Platform:
    """Uma classe para representar as plataformas no jogo."""
    def __init__(self, image, x, y):
        self.actor = Actor(image)
        self.actor.midtop = (x, y)
    def draw(self):
        self.actor.draw()

class PhysicsEntity:
    """
    Classe base para entidades que interagem com a física, como gravidade e
    colisão com plataformas.
    """
    def __init__(self, actor):
        self.actor = actor
        self.vy = 0
        self.on_ground = False
    def apply_physics(self, old_y):
        self.actor.y += self.vy
        if not self.on_ground:
            self.vy += GRAVITY
        self.on_ground = False
        for platform in platforms:
            if self.actor.colliderect(platform.actor):
                if self.vy > 0 and old_y + self.actor.height / 2 <= platform.actor.y + platform.actor.height / 2:
                    self.actor.bottom = platform.actor.top
                    self.vy = 0
                    self.on_ground = True
                    break

class Player(PhysicsEntity):
    """Uma classe para representar o jogador (o coelho)."""
    def __init__(self, x, y):
        super().__init__(Actor('bunny1_ready'))
        self.actor.midbottom = (x, y)
        self.walk_right_frames = ['bunny1_walk_right1', 'bunny1_walk_right2']
        self.walk_left_frames = ['bunny1_walk_left1', 'bunny1_walk_left2']
        self.stand_frames = ['bunny1_ready', 'bunny1_stand']
        self.jump_frames = ['bunny1_ready', 'bunny1_jump']
        self.attack_right_frames = [f'net_right{i}' for i in range(1, 10)]
        self.attack_left_frames = [f'net_left{i}' for i in range(1, 10)]
        self.attack_image_right = 'bunny1_walk_right1'
        self.attack_image_left = 'bunny1_walk_left1'
        self.original_image = self.actor.image
        self.frame_index = 0
        self.facing_left = False
        self.jumping = False
        self.frame_timer = 0.0
        self.lives = 3
        self.score = 0
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_frame_index = 0
        self.net = Actor(self.attack_right_frames[0])
        self.net.visible = False
        self.attack_cooldown = 1.5
        self.cooldown_timer = 0.0
        self.collected_carrots = 0
        self.is_invincible = False
        self.powerup_timer = 0.0
    def move(self, dt):
        global walk_sound_timer
        move_speed = 5
        old_y = self.actor.y
        self.cooldown_timer -= dt
        is_moving_horizontally = False
        if not self.is_attacking:
            if keyboard.right:
                self.actor.x += move_speed
                self.facing_left = False
                is_moving_horizontally = True
            if keyboard.left:
                self.actor.x -= move_speed
                self.facing_left = True
                is_moving_horizontally = True
        if is_moving_horizontally and self.on_ground:
            walk_sound_timer += dt
            if walk_sound_timer >= WALK_SOUND_COOLDOWN:
                try:
                    if not is_muted:
                        sounds.grass_walk.play()
                except Exception:
                    print("Erro ao tentar tocar 'grass_walk.wav'")
                walk_sound_timer = 0.3
        else:
            walk_sound_timer = 0.0
        self.animate(dt, is_moving_horizontally)
        if self.actor.x > WIDTH:
            self.actor.x = 0
        if self.actor.x < 0:
            self.actor.x = WIDTH
        if keyboard.up and self.on_ground and not self.is_attacking:
            self.vy = JUMP_STRENGTH
            self.jumping = True
            self.on_ground = False
            self.actor.image = self.jump_frames[1]
            try:
                if not is_muted:
                    sounds.jump.play()
            except Exception:
                print("Erro ao tentar tocar 'jump.wav'")
        if keyboard.space and not self.is_attacking and self.cooldown_timer <= 0:
            self.attack()
        if self.is_attacking:
            self.update_attack(dt)
        self.update_powerup(dt)
        self.apply_physics(old_y)
        if self.actor.y > HEIGHT:
            self.actor.y = 0
            self.vy = 0
            self.jumping = False
            self.on_ground = False
    def take_damage(self):
        global game_state, enemies, flames
        if self.is_invincible:
            return
        try:
            if not is_muted:
                sounds.bunny_hurt.play()
        except Exception:
            print("Erro ao tentar tocar 'bunny_hurt.wav'")
        self.lives -= 1
        if self.lives <= 0:
            game_state = 'GAMEOVER'
        else:
            self.actor.midbottom = (150, 0)
            self.vy = 0
            self.jumping = False
            self.on_ground = False
            enemies.clear()
            flames.clear()
    def activate_powerup(self):
        self.is_invincible = True
        self.powerup_timer = 0
        self.collected_carrots = 0
        try:
            if not is_muted:
                sounds.powerup_sound.play()
        except Exception:
            print("Erro ao tentar tocar 'powerup_sound.wav'")
    def update_powerup(self, dt):
        if self.is_invincible:
            self.powerup_timer += dt
            if self.powerup_timer >= powerup_duration:
                self.is_invincible = False
                self.powerup_timer = 0
    def attack(self):
        self.is_attacking = True
        self.attack_timer = 0.0
        self.attack_frame_index = 0
        self.net.visible = True
        self.cooldown_timer = self.attack_cooldown
        if self.facing_left:
            self.actor.image = self.attack_image_left
        else:
            self.actor.image = self.attack_image_right
        try:
            if not is_muted:
                sounds.net_attack.play()
        except Exception:
            print("Erro ao tentar tocar 'net_attack.wav'")
    def update_attack(self, dt):
        self.attack_timer += dt
        total_frames = len(self.attack_right_frames)
        attack_total_duration = ATTACK_ANIMATION_SPEED * total_frames
        progress = min(1.0, self.attack_timer / attack_total_duration)
        frame = int(progress * (total_frames - 1))
        self.attack_frame_index = frame
        start_angle = 0 if self.facing_left else math.pi
        end_angle = math.pi if self.facing_left else 0
        current_angle = start_angle + (end_angle - start_angle) * progress
        center_x = self.actor.x
        center_y = self.actor.y
        radius = self.actor.height * 0.55
        net_x = center_x + radius * math.cos(current_angle)
        net_y = center_y - radius * math.sin(current_angle)
        if self.facing_left:
            self.net.image = self.attack_left_frames[self.attack_frame_index]
        else:
            self.net.image = self.attack_right_frames[self.attack_frame_index]
        self.net.center = (net_x, net_y)
        if self.attack_timer >= attack_total_duration:
            self.is_attacking = False
            self.net.visible = False
            self.actor.image = 'bunny1_ready'
    def animate(self, dt, is_moving_horizontally):
        if self.is_attacking:
            return
        self.frame_timer += dt
        if self.jumping and not self.on_ground:
            return
        if is_moving_horizontally and self.on_ground:
            if self.frame_timer >= WALK_ANIMATION_SPEED:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.walk_right_frames)
                self.actor.image = (self.walk_left_frames if self.facing_left else self.walk_right_frames)[self.frame_index]
        elif self.on_ground:
            if self.frame_timer >= STAND_ANIMATION_SPEED:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.stand_frames)
                self.actor.image = self.stand_frames[self.frame_index]
    def draw(self):
        if self.net.visible:
            self.net.draw()
        if self.is_invincible:
            if int(self.powerup_timer * 5) % 2 == 0:
                self.actor.draw()
        else:
            self.actor.draw()

class CloudSpawner:
    """Uma classe para representar a nuvem que gera outros inimigos."""
    def __init__(self, x, y):
        self.actor = Actor('cloud')
        self.actor.midtop = (x, y)
        self.vx = CLOUD_SPEED if random.choice([True, False]) else -CLOUD_SPEED
        self.spawn_timer = 0.0
        self.spawn_cooldown = random.uniform(3, 8)
        self.base_cooldown = self.spawn_cooldown
        self.min_cooldown = self.base_cooldown / 2
        self.is_fleeing = False
    def move(self, dt):
        if not self.is_fleeing:
            self.actor.x += self.vx
            if self.actor.x > WIDTH or self.actor.x < 0:
                self.vx *= -1
            if game_timer > 0:
                difficulty_factor = min(1.0, game_timer / 90)
                self.spawn_cooldown = self.base_cooldown - (self.base_cooldown - self.min_cooldown) * difficulty_factor
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                new_enemy_x = self.actor.x
                new_enemy_y = self.actor.bottom
                if random.random() < 0.5:
                    enemies.append(Enemy(new_enemy_x, new_enemy_y))
                else:
                    enemies.append(Flyman(new_enemy_x, new_enemy_y))
                self.spawn_timer = self.spawn_cooldown
        else:
            self.actor.x += self.vx
    def draw(self):
        self.actor.draw()

class Enemy(PhysicsEntity):
    """Uma classe para os inimigos terrestres (espetos)."""
    def __init__(self, x, y):
        super().__init__(Actor('spikeman_walk_right1'))
        self.walk_right_frames = ['spikeman_walk_right1', 'spikeman_walk_right2']
        self.walk_left_frames = ['spikeman_walk_left1', 'spikeman_walk_left2']
        self.actor.midtop = (x, y)
        self.vx = 0
        self.frame_timer = 0.0
        self.frame_index = 0
        self.is_fleeing = False
    def move(self, dt):
        old_y = self.actor.y
        if self.on_ground:
            if not self.is_fleeing:
                if player.actor.x > self.actor.x:
                    self.vx = ENEMY_FOLLOW_SPEED
                elif player.actor.x < self.actor.x:
                    self.vx = -ENEMY_FOLLOW_SPEED
                else:
                    self.vx = 0
            else:
                if self.vx == 0:
                    self.vx = FLEEING_SPEED if self.actor.x < WIDTH / 2 else -FLEEING_SPEED
                self.vx = self.vx
            self.actor.x += self.vx
        self.apply_physics(old_y)
        self.animate(dt)
    def animate(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= ENEMY_WALK_ANIMATION_SPEED:
            self.frame_timer = 0
            if self.vx > 0:
                self.frame_index = (self.frame_index + 1) % len(self.walk_right_frames)
                self.actor.image = self.walk_right_frames[self.frame_index]
            elif self.vx < 0:
                self.frame_index = (self.frame_index + 1) % len(self.walk_left_frames)
                self.actor.image = self.walk_left_frames[self.frame_index]
            else:
                self.actor.image = self.walk_right_frames[0]
    def draw(self):
        self.actor.draw()

class Flyman(PhysicsEntity):
    """Uma classe para um novo tipo de inimigo que voa."""
    def __init__(self, x, y):
        super().__init__(Actor('flyman_stand'))
        self.stand_frames = ['flyman_still_stand', 'flyman_stand']
        self.fly_frames = ['flyman_fly']
        self.actor.midtop = (x, y)
        self.vx = 0
        self.frame_timer = 0.0
        self.frame_index = 0
        self.ground_timer = 4.0
        self.is_flying = False
        self.is_fleeing = False
    def move(self, dt):
        if not self.is_fleeing:
            if not self.is_flying:
                old_y = self.actor.y
                self.apply_physics(old_y)
                self.ground_timer -= dt
                if self.ground_timer <= 0:
                    self.is_flying = True
                    self.vy = 0
            else:
                if player.actor.x > self.actor.x:
                    self.vx = FLYMAN_FOLLOW_SPEED
                elif player.actor.x < self.actor.x:
                    self.vx = -FLYMAN_FOLLOW_SPEED
                else:
                    self.vx = 0
                if player.actor.y > self.actor.y:
                    self.vy = FLYMAN_FOLLOW_SPEED
                elif player.actor.y < self.actor.y:
                    self.vy = -FLYMAN_FOLLOW_SPEED
                else:
                    self.vy = 0
                self.actor.x += self.vx
                self.actor.y += self.vy
        else:
            if self.vx == 0:
                self.vx = FLEEING_SPEED if self.actor.x < WIDTH / 2 else -FLEEING_SPEED
            self.actor.x += self.vx
            self.actor.y += self.vy
            self.vy += GRAVITY
        self.animate(dt)
    def animate(self, dt):
        self.frame_timer += dt
        if self.is_flying and not self.is_fleeing:
            if self.frame_timer >= FLYMAN_FLY_SPEED:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.fly_frames)
                self.actor.image = self.fly_frames[self.frame_index]
        else:
            if self.frame_timer >= STAND_ANIMATION_SPEED:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.stand_frames)
                self.actor.image = self.stand_frames[self.frame_index]
    def draw(self):
        self.actor.draw()

class Coin:
    """Uma classe para as moedas coletáveis."""
    def __init__(self, x, y, coin_type):
        self.actor = Actor(f'{coin_type}_1')
        self.actor.midbottom = (x, y)
        self.points = 0
        self.animation_frames = [f'{coin_type}_{i}' for i in range(1, 5)]
        self.frame_index = 0
        self.frame_timer = 0.0
        if coin_type == 'bronze':
            self.points = 5
        elif coin_type == 'silver':
            self.points = 10
        elif coin_type == 'gold':
            self.points = 20
    def animate(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= COIN_ANIMATION_SPEED:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animation_frames)
            self.actor.image = self.animation_frames[self.frame_index]
    def draw(self):
        self.actor.draw()

class Carrot:
    """Uma classe para as cenouras que ativam o power-up."""
    def __init__(self, x, y):
        self.actor = Actor('carrot')
        self.actor.midbottom = (x, y)
        self.animation_frames = ['carrot']
        self.frame_index = 0
        self.frame_timer = 0.0
    def animate(self, dt):
        pass
    def draw(self):
        self.actor.draw()

class Boss:
    """Uma classe para o chefão do jogo."""
    def __init__(self):
        self.actor = Actor('sun1')
        self.animation_frames = ['sun1', 'sun2']
        self.actor.midtop = (WIDTH // 2, -100)
        self.target_y = 50
        self.vx = 0
        self.vy = 2
        self.frame_timer = 0.0
        self.frame_index = 0
        self.max_hp = 5
        self.hits_taken = 0
        self.attack_cooldown_min = 0.5
        self.attack_cooldown_max = 1.5
        self.attack_timer = random.uniform(self.attack_cooldown_min, self.attack_cooldown_max)
        self.max_flames = 3
        self.is_descending = True
        self.is_invincible = False
        self.invincibility_timer = 0.0
        self.is_moving_after_hit = False
        self.target_x = self.actor.x
    def move(self, dt):
        self.animate(dt)
        if self.is_descending:
            self.actor.y += self.vy
            if self.actor.y >= self.target_y:
                self.actor.y = self.target_y
                self.is_descending = False
                self.vy = 0
                try:
                    if not is_muted:
                        sounds.boss_arriving.play()
                except Exception:
                    print("Erro ao tentar tocar 'boss_arriving.wav'")
                return
        if self.is_moving_after_hit:
            if abs(self.actor.x - self.target_x) < 5:
                self.actor.x = self.target_x
                self.vx = 0
                self.is_moving_after_hit = False
            else:
                self.actor.x += self.vx
        if self.is_invincible:
            self.invincibility_timer += dt
            if self.invincibility_timer >= boss_invincibility_duration:
                self.is_invincible = False
                self.invincibility_timer = 0.0
        if not self.is_invincible and not self.is_descending and not self.is_moving_after_hit:
            self.attack_timer -= dt
            if self.attack_timer <= 0 and len(flames) < self.max_flames:
                self.attack()
                self.attack_timer = random.uniform(self.attack_cooldown_min, self.attack_cooldown_max)
    def attack(self):
        num_flames_to_shoot = random.choice([2, 3])
        for _ in range(num_flames_to_shoot):
            if len(flames) < self.max_flames:
                flames.append(Flame(self.actor.midbottom[0], self.actor.midbottom[1]))
                try:
                    if not is_muted:
                        sounds.boss_attack.play()
                except Exception:
                    print("Erro ao tentar tocar 'boss_attack.wav'")
    def take_damage(self):
        if self.is_invincible:
            return False
        self.hits_taken += 1
        self.is_invincible = True
        self.invincibility_timer = 0.0
        if self.hits_taken >= self.max_hp:
            return True
        else:
            self.target_x = random.randint(self.actor.width // 2, WIDTH - self.actor.width // 2)
            if self.target_x > self.actor.x:
                self.vx = 2
            else:
                self.vx = -2
            self.is_moving_after_hit = True
            return False
    def animate(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= 0.3:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animation_frames)
            self.actor.image = self.animation_frames[self.frame_index]
    def draw(self):
        if self.is_invincible:
            if int(self.invincibility_timer * 2.5) % 2 == 0:
                self.actor.draw()
        else:
            self.actor.draw()

class Flame:
    """Uma classe para a bolinha de fogo do boss."""
    def __init__(self, x, y):
        self.actor = Actor('flame_1')
        self.actor.midtop = (x, y)
        try:
            if not is_muted:
                sounds.flame_sound.play()
        except Exception:
            print("Erro ao tentar tocar 'flame_sound.wav'")
        self.vx = random.choice([-3, 3])
        self.vy = random.uniform(-9, -6)
        self.bounce_count = 0
        self.max_bounces = random.randint(7, 8)
    def move(self, dt):
        old_y = self.actor.y
        self.actor.x += self.vx
        self.actor.y += self.vy
        self.vy += GRAVITY
        if self.actor.x > WIDTH:
            self.actor.x = 0
        if self.actor.x < 0:
            self.actor.x = WIDTH
        for platform in platforms:
            if self.actor.colliderect(platform.actor):
                if self.vy > 0 and old_y + self.actor.height / 2 <= platform.actor.y + platform.actor.height / 2:
                    self.actor.bottom = platform.actor.top
                    self.vy *= -0.7
                    self.vx *= 0.9
                    self.bounce_count += 1
                    break
        if not player.is_invincible and self.actor.colliderect(player.actor):
            player.take_damage()
            if self in flames:
                flames.remove(self)
        if self.actor.y > HEIGHT or self.bounce_count >= self.max_bounces:
            if self in flames:
                flames.remove(self)
    def draw(self):
        self.actor.draw()

# ==============================================================================
#                      FUNÇÕES DE INICIALIZAÇÃO E LÓGICA
# ==============================================================================

def setup_platforms():
    """Cria e posiciona todas as plataformas no jogo."""
    ground_tile = Actor('ground_grass copia')
    ground_tile_width = ground_tile.width
    for i in range(int(WIDTH / ground_tile_width) + 2):
        platforms.append(Platform('ground_grass', i * ground_tile_width + (ground_tile_width // 2), HEIGHT - 20))
    platforms.append(Platform('ground_grass', 10, 520))
    platforms.append(Platform('ground_grass', 200, 220))
    platforms.append(Platform('ground_grass', 400, 420))
    platforms.append(Platform('ground_grass', 600, 220))
    platforms.append(Platform('ground_grass', 800, 520))
    platforms.append(Platform('ground_grass', 1000, 220))
    platforms.append(Platform('ground_grass', 1200, 420))

def spawn_coins_and_carrots():
    """Gera moedas e cenouras em posições aleatórias nas plataformas."""
    for p in platforms:
        if p.actor.midtop[1] < HEIGHT - 50:
            x = p.actor.x
            y = p.actor.top - 20
            if random.random() < 0.5:
                if random.random() < 0.6:
                    carrots.append(Carrot(x, y))
                else:
                    rand = random.random()
                    if rand < 0.5:
                        coins.append(Coin(x, y, 'bronze'))
                    elif rand < 0.8:
                        coins.append(Coin(x, y, 'silver'))
                    else:
                        coins.append(Coin(x, y, 'gold'))

def reset_game():
    """Reinicia todas as variáveis e entidades do jogo para um novo começo."""
    global game_timer, prelude_timer, player, enemies, spawners, coins, carrots, flames, boss, menu_music_playing, menu_selection
    try:
        music.stop()
    except Exception:
        print("Erro ao tentar parar a música.")
    menu_music_playing = False
    game_timer = 0.0
    prelude_timer = 0.0
    player = Player(150, 0)
    enemies.clear()
    spawners.clear()
    coins.clear()
    carrots.clear()
    flames.clear()
    platforms.clear()
    boss = None
    setup_platforms()
    spawners.append(CloudSpawner(600, 30))
    spawn_coins_and_carrots()
    menu_selection = 0

def start_prelude_phase():
    """Ativa o comportamento de fuga para inimigos e spawners."""
    global spawners
    coins.clear()
    carrots.clear()
    try:
        if not is_muted:
            sounds.boss_arriving.play()
    except Exception:
        print("Erro ao tentar tocar 'boss_arriving.wav'")
    for enemy in enemies:
        enemy.is_fleeing = True
        if enemy.actor.x < WIDTH / 2:
            enemy.vx = FLEEING_SPEED
        else:
            enemy.vx = -FLEEING_SPEED
    for spawner in spawners:
        spawner.is_fleeing = True
        if spawner.actor.x < WIDTH / 2:
            spawner.vx = FLEEING_SPEED
        else:
            spawner.vx = -FLEEING_SPEED

def toggle_mute():
    """Alterna entre silenciar e reativar o áudio."""
    global is_muted
    is_muted = not is_muted
    if is_muted:
        music.stop()
        is_muted = True
        mute_button.image = 'mute_icon'
    else:
        music.play('menu_game')
        is_muted = False
        mute_button.image = 'unmute_icon'

# ==============================================================================
#                          FUNÇÕES DO LOOP PRINCIPAL
# ==============================================================================

def draw():
    """Função de desenho principal, chamada 60 vezes por segundo."""
    global menu_music_playing

    if (game_state == 'MAIN_MENU' or game_state == 'HOW_TO_PLAY') and not menu_music_playing:
        try:
            music.play('menu_game')
            menu_music_playing = True
        except Exception:
            print("Erro ao tentar tocar 'menu_game.mp3'")
    elif game_state != 'MAIN_MENU' and game_state != 'HOW_TO_PLAY' and menu_music_playing:
        try:
            music.stop()
        except Exception:
            print("Erro ao tentar parar a música.")
        menu_music_playing = False

    start_color = (0, 139, 139)
    end_color = (173, 255, 47)
    transition_time = 120
    progress = min(1.0, game_timer / transition_time)
    red = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
    green = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
    blue = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
    current_color = (red, green, blue)
    screen.fill(current_color)

    if game_state == 'MAIN_MENU':
        draw_main_menu()
    elif game_state == 'HOW_TO_PLAY':
        draw_how_to_play()
    else:
        for platform in platforms:
            platform.draw()
        for coin in coins:
            coin.draw()
        for carrot in carrots:
            carrot.draw()
        player.draw()

        if game_state == 'PLAYING' or game_state == 'BOSS_PRELUDE':
            for spawner in spawners:
                spawner.draw()
            for enemy in enemies:
                enemy.draw()
        elif game_state == 'BOSS_FIGHT':
            if boss:
                boss.draw()
            for flame in flames:
                flame.draw()

        draw_hud()

        if game_state == 'BOSS_PRELUDE':
            if int(prelude_timer * 2) % 2 == 0:
                screen.draw.text("Atenção: Chefe!", center=(WIDTH // 2, HEIGHT // 2), fontsize=80, color="red")
        if game_state == 'GAMEOVER':
            screen.draw.text("Game Over", center=(WIDTH / 2, HEIGHT / 2 - 50), fontsize=80, color="red")
            screen.draw.text("Pressione ENTER para tentar novamente", center=(WIDTH / 2, HEIGHT / 2 + 50), fontsize=30, color="white")
        if game_state == 'WIN':
            screen.draw.text("Vitória!", center=(WIDTH / 2, HEIGHT / 2 - 50), fontsize=80, color="green")
            screen.draw.text("Pressione ENTER para jogar novamente", center=(WIDTH / 2, HEIGHT / 2 + 50), fontsize=30, color="white")
    
    # Desenha o botão de mudo em todas as telas
    mute_button.draw()

def draw_main_menu():
    """Desenha o menu principal."""
    screen.draw.text("Bunny Brave", center=(WIDTH / 2, HEIGHT / 4), fontsize=100, color="yellow")
    menu_options = ["Iniciar Jogo", "Como Jogar", "Sair"]
    for i, option in enumerate(menu_options):
        color = "white"
        if i == menu_selection:
            color = "red"
        screen.draw.text(option, center=(WIDTH / 2, HEIGHT / 2 + i * 80), fontsize=50, color=color)

def draw_how_to_play():
    """Desenha a tela de instruções."""
    screen.draw.text("Como Jogar", center=(WIDTH / 2, 50), fontsize=80, color="white")
    screen.draw.text("Controles:", (50, 150), fontsize=40, color="white")
    screen.draw.text("- Setas Esquerda/Direita: Mover o coelho", (70, 200), fontsize=30, color="white")
    screen.draw.text("- Seta para Cima: Pular", (70, 250), fontsize=30, color="white")
    screen.draw.text("- ESPAÇO: Atacar com a rede", (70, 300), fontsize=30, color="white")
    screen.draw.text("Objetivos:", (50, 400), fontsize=40, color="white")
    screen.draw.text("- Colete moedas para aumentar a pontuação.", (70, 450), fontsize=30, color="white")
    screen.draw.text("- Colete cenouras para ativar a invencibilidade.", (70, 500), fontsize=30, color="white")
    screen.draw.text("- Derrote inimigos para ganhar pontos e sobreviver.", (70, 550), fontsize=30, color="white")
    screen.draw.text("- Sobreviva até a luta contra o chefão!", (70, 600), fontsize=30, color="white")
    screen.draw.text("Pressione BACKSPACE para voltar ao menu", center=(WIDTH / 2, HEIGHT - 50), fontsize=30, color="yellow")

def draw_hud():
    """Desenha todos os elementos da interface do usuário."""
    life_icon = Actor('lifes')
    for i in range(player.lives):
        screen.blit('lifes', (10 + i * (life_icon.width + 5), 10))
    screen.draw.text(f"Pontuação: {player.score}", (WIDTH - 250, 10), fontsize=40, color="white")
    minutes = int(game_timer / 60)
    seconds = int(game_timer % 60)
    screen.draw.text(f"Tempo: {minutes:02}:{seconds:02}", (WIDTH - 250, 50), fontsize=40, color="white")
    BAR_HEIGHT = 20
    BAR_WIDTH = 200
    bar_x = WIDTH // 2 - BAR_WIDTH // 2
    bar_y = HEIGHT - BAR_HEIGHT - 10
    screen.draw.filled_rect(Rect(bar_x, bar_y, BAR_WIDTH, BAR_HEIGHT), (100, 100, 100))
    filled_width = (player.collected_carrots / powerup_carrots_required) * BAR_WIDTH
    screen.draw.filled_rect(Rect(bar_x, bar_y, filled_width, BAR_HEIGHT), (255, 165, 0))
    if player.is_invincible:
        time_left = round(powerup_duration - player.powerup_timer, 1)
        screen.draw.text(f"INVENCÍVEL! {time_left}s", center=(WIDTH // 2, HEIGHT - BAR_HEIGHT - 35), fontsize=30, color="yellow")
    if game_state == 'BOSS_FIGHT' and boss:
        boss_hp_text = f"Boss HP: {boss.max_hp - boss.hits_taken} / {boss.max_hp}"
        screen.draw.text(boss_hp_text, center=(WIDTH // 2, 20), fontsize=30, color="red")

def on_mouse_down(pos):
    """Lida com cliques do mouse."""
    if mute_button.collidepoint(pos):
        toggle_mute()

def on_key_down(key):
    """Lida com pressionamento de teclas para navegação do menu."""
    global game_state, menu_selection
    if game_state == 'MAIN_MENU':
        if key == keys.UP:
            menu_selection = (menu_selection - 1 + 3) % 3
        elif key == keys.DOWN:
            menu_selection = (menu_selection + 1) % 3
        elif key == keys.RETURN:
            if menu_selection == 0:
                reset_game()
                game_state = 'PLAYING'
            elif menu_selection == 1:
                game_state = 'HOW_TO_PLAY'
            elif menu_selection == 2:
                exit()
    elif game_state == 'HOW_TO_PLAY':
        if key == keys.BACKSPACE:
            game_state = 'MAIN_MENU'
    elif game_state == 'GAMEOVER' or game_state == 'WIN':
        if key == keys.RETURN:
            game_state = 'MAIN_MENU'

def update(dt):
    """Função de atualização principal, chamada 60 vezes por segundo."""
    global game_state, game_timer, prelude_timer, boss, menu_music_playing

    if game_state == 'PLAYING':
        game_timer += dt
        player.move(dt)
        if game_timer >= boss_fight_threshold - BOSS_PRELUDE_DURATION:
            game_state = 'BOSS_PRELUDE'
            start_prelude_phase()
        update_spawners(dt)
        update_enemies(dt)
        update_collectibles(dt)
        update_player_interactions()
        update_game_entities(dt)
    elif game_state == 'BOSS_PRELUDE':
        prelude_timer += dt
        update_spawners(dt)
        update_enemies(dt)
        update_collectibles(dt)
        update_player_interactions()
        player.move(dt)
        if prelude_timer >= BOSS_PRELUDE_DURATION:
            game_state = 'BOSS_FIGHT'
            boss = Boss()
            try:
                music.play('boss_appair', loop=True)
            except Exception:
                print("Erro ao tentar tocar 'boss_appair.mp3'")
    elif game_state == 'BOSS_FIGHT':
        if not music.is_playing('boss_appair'):
            try:
                music.play('boss_appair', loop=True)
            except Exception:
                print("Erro ao tentar tocar 'boss_appair.mp3'")
        player.move(dt)
        boss.move(dt)
        update_flames(dt)
        update_player_interactions()
        update_boss_fight_collisions(dt)
        if boss and boss.hits_taken >= boss.max_hp:
            game_state = 'WIN'
            try:
                music.stop()
                if not is_muted:
                    sounds.boss_defeat.play()
            except Exception:
                print("Erro ao tentar parar a música ou tocar 'boss_defeat.wav'")
        elif player.lives <= 0:
            game_state = 'GAMEOVER'
            try:
                music.stop()
            except Exception:
                print("Erro ao tentar parar a música.")

def update_spawners(dt):
    """Atualiza todos os spawners."""
    global spawners
    for spawner in list(spawners):
        spawner.move(dt)
        if spawner.is_fleeing and (spawner.actor.x > WIDTH + 50 or spawner.actor.x < -50):
            spawners.remove(spawner)

def update_enemies(dt):
    """Atualiza todos os inimigos."""
    for enemy in list(enemies):
        enemy.move(dt)
        if enemy.actor.y > HEIGHT + 50:
            enemies.remove(enemy)

def update_flames(dt):
    """Atualiza todas as chamas."""
    for flame in list(flames):
        flame.move(dt)

def update_collectibles(dt):
    """Atualiza a lógica de coleta de moedas e cenouras."""
    for coin in list(coins):
        coin.animate(dt)
        if player.actor.colliderect(coin.actor):
            player.score += coin.points
            try:
                if not is_muted:
                    sounds.coin_catch.play()
            except Exception:
                print("Erro ao tentar tocar 'coin_catch.wav'")
            coins.remove(coin)
    for carrot in list(carrots):
        carrot.animate(dt)
        if player.actor.colliderect(carrot.actor):
            player.collected_carrots += 1
            if player.collected_carrots >= powerup_carrots_required:
                player.activate_powerup()
            try:
                if not is_muted:
                    sounds.bunny_eat.play()
            except Exception:
                print("Erro ao tentar tocar 'bunny_eat.wav'")
            carrots.remove(carrot)

def update_player_interactions():
    """Verifica interações do jogador com inimigos e colecionáveis."""
    for enemy in list(enemies):
        if player.is_attacking and player.net.colliderect(enemy.actor):
            player.score += 50
            try:
                if not is_muted:
                    sounds.net_impact.play()
                    sounds.enemy_defeat.play()
            except Exception:
                print("Erro ao tentar tocar 'net_impact.wav' ou 'enemy_defeat.wav'")
            enemies.remove(enemy)
            continue
        if player.actor.colliderect(enemy.actor):
            player.take_damage()
    for flame in list(flames):
        if player.actor.colliderect(flame.actor):
            if not player.is_invincible:
                player.take_damage()
                flames.remove(flame)

def update_boss_fight_collisions(dt):
    """Lógica de colisão durante a luta contra o chefe."""
    global flames
    boss_hitbox = Rect(boss.actor.x - boss.actor.width // 2 + 20,
                       boss.actor.y - boss.actor.height // 2 + 20,
                       boss.actor.width - 40,
                       boss.actor.height - 40)
    if player.is_attacking and player.net.colliderect(boss_hitbox):
        if not boss.is_invincible:
            try:
                if not is_muted:
                    sounds.net_impact.play()
            except Exception:
                print("Erro ao tentar tocar 'net_impact.wav'")
        if boss.take_damage():
            game_state = 'WIN'
    if not player.is_invincible and player.actor.colliderect(boss_hitbox):
        player.take_damage()

def update_game_entities(dt):
    """Atualiza moedas e inimigos."""
    for coin in coins:
        coin.animate(dt)
    for enemy in list(enemies):
        enemy.move(dt)
        # remove inimigos que caíram da tela
        if enemy.actor.y > HEIGHT:
            enemies.remove(enemy)
    if game_state == 'BOSS_FIGHT' and boss:
        boss.move(dt)
    for coin in list(coins):
        if player.actor.colliderect(coin.actor):
            player.score += coin.points
            try:
                if not is_muted:
                    sounds.coin_catch.play()
            except Exception:
                print("Erro ao tentar tocar 'coin_catch.wav'")
            coins.remove(coin)
    for carrot in list(carrots):
        if player.actor.colliderect(carrot.actor):
            player.collected_carrots += 1
            if player.collected_carrots >= powerup_carrots_required:
                player.activate_powerup()
            try:
                if not is_muted:
                    sounds.bunny_eat.play()
            except Exception:
                print("Erro ao tentar tocar 'bunny_eat.wav'")
            carrots.remove(carrot)

# Inicializa o botão de mudo
mute_button = Actor('unmute_icon')
mute_button.topright = (WIDTH - 10, 10)

pgzrun.go()
