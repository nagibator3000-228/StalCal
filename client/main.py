import socketio
import json
from random import uniform
from ursina import *
from ursina import Audio
from ursina import application
from ursina.shaders import lit_with_shadows_shader
from ursina.shaders import basic_lighting_shader
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.health_bar import HealthBar
from panda3d.core import loadPrcFileData
from pathlib import Path

loadPrcFileData('', '''
icon-filename ""
win-size 1440 1080
window-type onscreen
notify-level error
''')

sio = socketio.Client()
# sio.connect('wss://stalker-server-z2l9.onrender.com', transports=['websocket'])
sio.connect('ws://localhost:5000/', transports=['websocket'])

other_players = {}
tutorial = False
move_window = False

max_bullets = 0
health = 100
magazine_size = 0
magazine = 0
duel_map_spawn_point = 0

class Particle(Entity):
    def __init__(self, position, color):
        super().__init__(
            model='cube',
            color=color,
            position=position,
            scale=uniform(0.04, 0.1),
            rotation=Vec3(uniform(0,360), uniform(0,360), uniform(0,360)),
        )
        self.velocity = Vec3(random.randint(-20,20),random.randint(-20,20),random.randint(-20,20))
        self.lifetime = uniform(1, 3)

    def update(self):
        if hasattr(self, 'velocity'):
            self.position += self.velocity * time.dt
            self.lifetime -= time.dt * 20
            if self.lifetime <= 0:
                destroy(self)

def resource_path(relative_path):
    return relative_path

with open(resource_path('settings.json'), 'r', encoding='utf-8') as f:
    JSON_settings = json.load(f)

    tutorial = JSON_settings["game_settings"]["tutorial"]
    max_bullets = JSON_settings["game_settings"]["max_bullets"]

@sio.event()
def hit(data):
    global health

    health -= data["damage"]

@sio.event()
def update_players(data):
    global other_players

    players_data = data["players"]
    for sid, pos in players_data.items():
        if sid not in other_players:
            other_players[sid] = Entity(
                model=resource_path('assets/models/stalker.glb'),
                scale=1.7
            )
            other_players[sid].colliders = Entity(parent=other_players[sid], collider='box', scale=(1.4, 5, 1.2), y=-3)
            other_players[sid].position = Vec3(pos['x'], pos['y'] + 1.85, pos['z'])
            other_players[sid].rotation_y = pos.get('ry', 0) + 180
    print(data)


@sio.event()
def new_player(data):
    sid = data['sid']
    if sid != sio.sid and sid not in other_players:
        other_players[sid] = Entity(
            model=resource_path('assets/models/stalker.glb'),
            scale=1.7
            )
        other_players[sid].colliders = Entity(parent=other_players[sid], collider='box', scale=(1.4, 5, .7), y=-3)
        other_players[sid].position = Vec3(data['x'], data['y'] + 1.85, data['z'])
        other_players[sid].rotation_y = data.get('ry', 0) + 180

@sio.event()
def player_left(sid):
    player = sid['sid']

    if player in other_players:
        destroy(other_players[sid])
        del other_players[sid]

@sio.event()
def kill(data):
    if duel:
        if not duel_map_spawn_point:
            player.position = Vec3(965, 520, 905)
        else:
            player.position = Vec3(1044, 525, 1090)

    for i in range(100):
        Particle(Vec3(data['position'][0], data['position'][1]+3.4, data['position'][2]), color=color.red)


@sio.event()
def move(data):
    sid = data['sid']
    if sid in other_players:
        other_players[sid].position = Vec3(data['x'], data['y'] + 1.85, data['z'])
        other_players[sid].rotation_y = data.get('ry', 0) + 180


@sio.event()
def remove_player(sid):
    if sid in other_players:
        destroy(other_players[sid])
        del other_players[sid]

@sio.event()
def disconnect():
    print("disconnected.")


@sio.event()
def connect():
    print("connected.")

app = Ursina()

fog = 0.02
speed = 6
forest = True
max_recoil = 120
recoil_per_shot = 6
recoil_recovery_speed = 14
current_recoil = 0
recoil_angle = 5
recoil_time = 0.05
fire_rate = 0
last_shot_time = 0
weapon_distance = 0
duel = False

scope = False

current_location = []

lit_with_shadows_fog_shader = Shader(
    language=Shader.GLSL,
    vertex=open(resource_path("assets/shaders/lit_with_fog_vertex.glsl")).read(),
    fragment=open(resource_path("assets/shaders/lit_with_fog_fragment.glsl")).read(),
)

ground = Entity(model='plane', scale=(600, 1, 600), collider='box', y=2, visible=False)

hit_sound = Audio(resource_path('assets/sounds/hit.wav'), autoplay=False)

reload_sound = Audio(resource_path('assets/sounds/reload.wav'), autoplay=False)

empty_sound = Audio(resource_path('assets/sounds/empty.wav'), autoplay=False)

pick_up_sound = Audio(resource_path('assets/sounds/pick_up.wav'), autoplay=False)
get_key_sound = Audio(resource_path('assets/sounds/get_key.wav'), autoplay=False)

running_sound = Audio(resource_path('assets/sounds/running.wav'), autoplay=False, loop=True, volume=.4)

ambient_rain = Audio(resource_path('assets/sounds/ambient_rain.wav'), autoplay=True, loop=True, volume=.3)

health_bar = HealthBar(
    max_value=100, 
    value=Default, 
    roundness=0.25, 
    bar_color=color.red.tint(-0.2), 
    highlight_color=color.black66, 
    animation_duration=0.1, 
    show_text=True, 
    show_lines=False, 
    text_size=0.7, 
    scale=(0.5, 0.025), 
    origin=(-2.88, 33), 
    name='health_bar'
    )


forest_model = Entity(model=resource_path('assets/models/forest.glb'),y=2,shader=lit_with_shadows_fog_shader,scale=7.6, visible=forest, enabled=True)
forest_model.set_shader_input("camera_pos", camera.world_position)
forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
forest_model.set_shader_input("fog_density", 0.0)
forest_collider = Entity(model=resource_path('assets/models/forest.glb'), collider='mesh', alpha=0, rotation_x=90, y=2, scale=7.6, parent=forest_model, visible=0, enabled=False)

field_gate_border = Entity(model=resource_path('assets/models/field_gate_01.glb'), scale=1.5, position=Vec3(50, 2, -12), rotation_y=-0.15, enabled=False)
field_gate_border_collider = Entity(scale=(3.25, 5, .6), collider='box', parent=field_gate_border, visible=False)

first_stalker_house = Entity(model=resource_path('assets/models/stalker_house.glb'), scale=1.1, enabled=False)
first_stalker_house_collider = Entity(model=resource_path('assets/models/stalker_house.glb'), alpha=0, collider='mesh', rotation=Vec3(90, -90, 90), parent=first_stalker_house, x=-.9145,y=2.402, z=-0.265)

Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(37, 3.4, -40), rotation_y=90)
Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(37, 2.2, 24), rotation_y=90)

big_metal_door = Entity(model=resource_path('assets/models/big_metal_door.glb'), collider='box', scale=3.7, position=Vec3(46.76389, 1.9, -25.409944), enabled=False)

def settings():
    window.vsync = False

    sky = Sky(texture='sky_sunset')

    scene.fog_color = color.black
    scene.fog_density = fog + 0.04

    window.fullscreen = False
    window.cog_menu = False
    window.entity_counter.enabled = False
    window.collider_counter.enabled = False

def build():
    if not forest:
        forest_collider.collider = None

    first_stalker_house.position = Vec3(65, 2, -2.49)
    first_stalker_house.rotation_y = -19

    field_gate_border1 = Entity(model=resource_path('assets/models/field_gate_01.glb'), scale=1.5, position=Vec3(44, 2.05, 42), rotation_y=83)
    Entity(scale=(3.25, 5, .6), collider='box', parent=field_gate_border1, position=field_gate_border1.position, rotation_y=field_gate_border1.rotation.y)

ammo_bg = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(0, 0, 0, 180),
    scale=(0.25, 0.12),
    position=(0.75, -0.45)
)

info_bar = Text(
    parent=ammo_bg,
    text=f"{magazine}/{magazine_size} | {max_bullets}",
    origin=(0,0),
    scale=6,
    position=(0,0),
    color=color.white
)

shoot_sound = Audio(resource_path('assets/sounds/pm_shoot.wav'), autoplay=False)

ammo_9mm = Entity(model=resource_path('assets/models/9mm_ammo_box.glb'), scale=.0008, position=Vec3(62, 2.9, -7), collider='box', enabled=False)
ammo_9mm_1 = Entity(model=resource_path('assets/models/9mm_ammo_box.glb'), scale=ammo_9mm.scale, position=Vec3(71, 2, -36), collider='box', enabled=True)
ammo_9mm_2 = Entity(model=resource_path('assets/models/9mm_ammo_box.glb'), scale=ammo_9mm.scale, position=Vec3(112, 2, 2), collider='box', enabled=True)

pm = Entity(parent=scene, model=resource_path('assets/models/pm.glb'), origin_y=-.5, collider='box', position=Vec3(61, 2.6, -5.6), scale=.007, rotation_z=78, rotation_x=90, rotation_y=104, enabled=False)

goldEagle = Entity(parent=scene, model=resource_path('assets/models/gold_deagle.glb'), origin_y=-.5, collider='box', position=Vec3(70, 2.2, -52), scale=.0023, rotation=Vec3(0, 0, 0), enabled=True)

def get_deagle():
    global magazine, magazine_size, speed, JSON_settings, fire_rate, recoil_time, weapon_distance, shoot_sound

    pick_up_sound.play()

    fire_rate = 0.4
    weapon_distance = 600

    if player.weapon:
        player.weapon.enabled = False

    recoil_time = 0.2
    goldEagle.parent = camera
    goldEagle.collider = None
    goldEagle.position = Vec3(.6, -.16, .33)
    goldEagle.rotation = Vec3(0, 178, -.1)
    player.weapon = goldEagle
    player.weapon_name = 'gold_deagle'
    magazine_size = 6
    magazine = magazine_size
    speed -= 0.6

    JSON_settings["game_settings"]["weapon"] = 'gold_deagle'
    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    shoot_sound = Audio(resource_path('assets/sounds/deagle-shot-sound.wav'), autoplay=False)

    with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)
goldEagle.on_click = get_deagle

if tutorial and JSON_settings["game_settings"]["weapon"] == None:
    ammo_9mm.enabled = True
    pm.enabled = True
elif tutorial and JSON_settings["game_settings"]["weapon"] == 'pm':
    weapon_distance = 100
    pm.enabled = True
    pm.parent = camera
    pm.collider = None
    pm.position = Vec3(.5,-.26,.5)
    pm.rotation = Vec3(0, 86, -1)
    magazine_size = 12
    magazine = JSON_settings["game_settings"]["magazine"]
    speed -= 0.4
    fire_rate = 0.17
elif tutorial and JSON_settings["game_settings"]["weapon"] == 'gold_deagle':
    weapon_distance = 600
    recoil_time = 0.2
    goldEagle.parent = camera
    goldEagle.collider = None
    goldEagle.position = Vec3(.6, -.16, .33)
    goldEagle.rotation = Vec3(0, 178, -.1)
    magazine_size = 6
    magazine = JSON_settings["game_settings"]["magazine"]
    speed -= 0.6
    fire_rate = 0.4
    shoot_sound = Audio(resource_path('assets/sounds/pm_shoot.wav'), autoplay=False)

first_door_key = Entity(model=resource_path('assets/models/door_key.glb'), scale=.01, collider='box', position=Vec3(-28.65, 2, 13.), parent=scene, enabled=True)
first_door_key.shader = lit_with_shadows_shader
first_door_key.set_shader_input("emission_color", color.red*5)

def get_first_door_key():
    player.first_door_key = True
    get_key_sound.play()

    first_door_key.collider = None
    first_door_key.shader = None
    first_door_key.parent = camera
    first_door_key.position = Vec3(.5,-.24,.8)
    first_door_key.rotation = Vec3(-44, -10, -57)

first_door_key.on_click = get_first_door_key

def open_first_door():
    global tutorial

    if player.first_door_key:
        big_metal_door.enabled = False
        player.first_door_key = False
        destroy(first_door_key)

        JSON_settings["game_settings"]["tutorial"] = True
        tutorial = True

        ammo_9mm.enabled = True
        pm.enabled = True

        with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
            json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

big_metal_door.on_click = open_first_door

def get_pm():
    global magazine, magazine_size, speed, JSON_settings, fire_rate, weapon_distance

    pick_up_sound.play()

    if player.weapon:
        player.weapon.enabled = False

    weapon_distance = 100
    pm.parent = camera
    pm.collider = None
    pm.position = Vec3(.5,-.26,.5)
    pm.rotation = Vec3(0, 86, -1)
    player.weapon = pm
    player.weapon_name = 'pm'
    magazine_size = 12
    magazine = magazine_size
    speed -= 0.4
    fire_rate = 0.17

    JSON_settings["game_settings"]["weapon"] = 'pm'
    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

pm.on_click = get_pm

reload_time = 3
reloading = False

def get_ammo():
    global max_bullets, JSON_settings

    pick_up_sound.play()
    max_bullets += 60

    destroy(ammo_9mm)

    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

ammo_9mm.on_click = get_ammo

def get_ammo_1():
    global max_bullets, JSON_settings

    pick_up_sound.play()
    max_bullets += 60

    destroy(ammo_9mm_1)

    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

ammo_9mm_1.on_click = get_ammo_1

def get_ammo_2():
    global max_bullets, JSON_settings

    pick_up_sound.play()
    max_bullets += 60

    destroy(ammo_9mm_2)

    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

ammo_9mm_2.on_click = get_ammo_2

def reload():
    global magazine, max_bullets, reloading

    if not reloading and max_bullets > 0 and magazine < magazine_size:
        reloading = True
        reload_sound.stop()
        reload_sound.play()
        invoke(finish_reload, delay=reload_time)
        print("reloading...")


def finish_reload():
    global magazine, max_bullets, reloading

    needed = magazine_size - magazine
    if needed <= max_bullets:
        magazine = magazine_size
        max_bullets -= needed
    else:
        magazine += max_bullets
        max_bullets = 0

    reloading = False

run = False

def input(key):
    global last_shot_time, current_recoil, magazine, reloading, run, JSON_settings, weapon_distance, duel

    now = time.time()

    if key == 'left mouse down' and player.weapon and magazine > 0 and not reloading:
        if now - last_shot_time >= fire_rate:
            bullet = Entity(model='sphere', scale=.09, color=color.black, position=player.weapon.world_position + Vec3(.3, .5, 0))
            bullet.animate_position(bullet.position + (camera.forward * 500), curve=curve.linear, duration=.7)
            destroy(bullet, delay=2)
            last_shot_time = now
            magazine -= 1
            shoot_sound.stop()
            shoot_sound.play()
            current_recoil += recoil_per_shot
            if current_recoil > max_recoil:
                current_recoil = max_recoil

            ray = raycast(player.position, camera.forward, distance=weapon_distance, ignore=[camera, player, forest, ground])

            weapon_name = player.weapon_name

            for sid, ent in other_players.items():
                if ray.entity == ent.colliders:
                    hit_sound.stop()
                    hit_sound.play()
                    sio.emit('hit', {'player': sid, 'weapon': weapon_name, 'distance': ray.distance})
                    print(f'HIT {sid} with {weapon_name}')

            JSON_settings["game_settings"]["magazine"] = magazine
            JSON_settings["game_settings"]["max_bullets"] = max_bullets

            with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
                json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

        if player.weapon_name == 'pm':
            player.weapon.animate_rotation(player.weapon.rotation + Vec3(0,0,recoil_angle), duration=recoil_time, curve=curve.linear)
            invoke(lambda: player.weapon.animate_rotation(player.weapon.rotation - Vec3(0,0,recoil_angle/1.47), duration=recoil_time, curve=curve.linear), delay=recoil_time/1.7)
        else:
            player.weapon.animate_rotation(player.weapon.rotation + Vec3(recoil_angle,0,0), duration=recoil_time, curve=curve.linear)
            invoke(lambda: player.weapon.animate_rotation(player.weapon.rotation - Vec3(recoil_angle/1.47,0,0), duration=recoil_time, curve=curve.linear), delay=recoil_time/1.7)

    if magazine == 0 and max_bullets == 0 and key == 'left mouse down' and not reloading and not run and player.weapon:
        empty_sound.stop()
        empty_sound.play()
        reload()

    if key == 'r' and not reloading and not run:
        reload()
    elif key == 'left mouse down' and player.weapon and magazine == 0 and max_bullets > 0 and not reloading and not run and player.weapon:
        empty_sound.stop()
        empty_sound.play()
        reload()

    if key == 'insert': print(player.position)

    if key == 'escape':
        sio.disconnect()
        application.quit()

def load_duelMap():
    global current_location, forest, fog, duel, duel_map_spawn_point, speed
    duel = True

    fog = 0.001

    speed = 20

    if not duel_map_spawn_point:
        player.position = Vec3(965, 525, 905)
    else:
        player.position = Vec3(1044, 525, 1090)
        player.rotation.y = 90

    forest_model.set_shader_input("camera_pos", camera.world_position)
    forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
    forest_model.set_shader_input("fog_density", fog)

    scene.fog_color = color.black
    scene.fog_density = fog + 0

    for e in current_location:
        destroy(e)
    current_location = [
        Entity(model='plane', scale=(200, 2, 200), position=Vec3(1000, 500, 1000), texture='grass', collider='box'),
        Entity(model='cube', scale=(3, 40, 200), position=Vec3(1100, 520, 1000), collider='box', texture='brick'),
        Entity(model='cube', scale=(3, 40, 200), position=Vec3(900, 520, 1000), collider='box', texture='brick'),
        Entity(model='cube', scale=(3, 40, 200), position=Vec3(1000, 520, 900), collider='box', texture='brick', rotation_y=90),
        Entity(model='cube', scale=(3, 40, 200), position=Vec3(1000, 520, 1100), collider='box', texture='brick', rotation_y=90),
        Entity(model='cube', scale=(20, 25, 100), position=Vec3(1006, 500, 910), collider='box', texture='brick', rotation_y=90),
        Entity(model='cube', scale=(20, 25, 100), position=Vec3(1006, 500, 1090), collider='box', texture='brick', rotation_y=90),
        Entity(model='cube', scale=(5, 3, 97), position=Vec3(1009, 513, 922), collider='box', rotation_y=90, texture='brick'),
        Entity(model='cube', scale=(5, 3, 97), position=Vec3(1002, 513, 1078), collider='box', rotation_y=90, texture='brick')
    ]
    
    ladder = Entity(model=resource_path('assets/models/ladder.glb'), scale=7, position=Vec3(959, 505, 934), rotation_y=90)
    ladder_collider = Entity(model='cube', position=Vec3(959, 506, 934), collider='box', scale=(5, 1, 24), rotation_x=32, visible=False)
    ladder_collider2 = Entity(model='cube', position=Vec3(959, 512, 922), scale=(5, 1, 5), collider='box', visible=False)

    ladder2 = Entity(model=resource_path('assets/models/ladder.glb'), scale=7, position=Vec3(1053, 505, 1067), rotation_y=-90)
    ladder2_collider = Entity(model='cube', position=Vec3(1053, 506, 1067), collider='box', scale=(5, 1, 24), rotation_x=32, rotation_y=-180, visible=True)
    ladder2_collider2 = Entity(model='cube', position=Vec3(1053, 512, 1079), scale=(5, 1, 5), collider='box', visible=True)

    forest_model.enabled = False
    forest_collider.enabled = False
    big_metal_door.enabled = False
    field_gate_border.enabled = False
    first_stalker_house.enabled = False


def load_village():
    global current_location, forest, fog, speed

    player.position = Vec3(52, 2.4, -18)

    fog = 0

    speed = 6

    forest_model.set_shader_input("camera_pos", camera.world_position)
    forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
    forest_model.set_shader_input("fog_density", fog)

    scene.fog_color = color.black
    scene.fog_density = fog + 0.02

    for e in current_location:
        destroy(e)
    current_location = [
        Entity(model=resource_path('assets/models/concrete_wall_protection.glb'), position=Vec3(54, 2, 14.19676), scale=1.5, collider='box', rotation_y=3, rotation_x=0.2),
        Entity(model=resource_path('assets/models/concrete_wall_protection.glb'), position=Vec3(73.2, 2, 14.19676), scale=1.5, collider='box', rotation_y=-3, rotation_x=3.4),
        Entity(model=resource_path('assets/models/stalker_blockpost.glb'), position=Vec3(130, 1.9, -15), rotation_y=-90, scale=43),
        Entity(model=resource_path('assets/models/sandbag_wall.glb'), position=Vec3(48.9, 2, 9), scale=1.9, rotation_y=-9, collider='box'),
        Entity(model=resource_path('assets/models/btr.glb'), position=Vec3(59, 2, -44), scale=1.76, rotation_y=-101, collider='box'),
        Entity(model=resource_path('assets/models/pallet_of_boxes.glb'), position=Vec3(52.4, 2, -41), scale=2, rotation_y=4, collider='box'),
        Entity(model=resource_path('assets/models/field.glb'), scale=20, position=Vec3(54, 2, -51)),
        Entity(model=resource_path('assets/models/field.glb'), scale=20, position=Vec3(74, 2, -51)),
        Entity(model=resource_path('assets/models/field.glb'), scale=20, position=Vec3(94, 2, -51)),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(62, 2.7, -67)),
        Entity(model=resource_path('assets/models/concrete_wall_protection.glb'), position=Vec3(74, 2, -49), scale=1.6, collider='box', rotation_y=43, rotation_x=3),
        Entity(model=resource_path('assets/models/acacia_tree.glb'), position=Vec3(49, 2.1, -53), rotation_y=10),
        Entity(model=resource_path('assets/models/acacia_tree.glb'), position=Vec3(48.7, 2.1, -46), rotation_y=30),
        Entity(model=resource_path('assets/models/acacia_tree.glb'), position=Vec3(55, 2, -54), rotation_y=40),
        Entity(model=resource_path('assets/models/acacia_tree.glb'), position=Vec3(60, 2.1, -52), rotation_y=70),
        Entity(model=resource_path('assets/models/acacia_tree.glb'), position=Vec3(65, 1.9, -55), rotation_y=180),
        Entity(model=resource_path('assets/models/fern_grass.glb'), scale=62, position=Vec3(64, 2.4, -47)),
        Entity(model=resource_path('assets/models/fern_grass.glb'), scale=62, position=Vec3(67, 2.4, -52)),
    ]

    forest_model.enabled = True
    forest_collider.enabled = False
    big_metal_door.enabled = True
    field_gate_border.enabled = True

    first_stalker_house.enabled = True

def load_first_scene():
    global current_location, forest, speed

    speed = 6

    for e in current_location:
        destroy(e)

    current_location = [
        Entity(model=resource_path('assets/models/big_metal_door.glb'), visible=False, collider=None, scale=3.7, position=Vec3(46.76389, 1.9, -25.409944)),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(-47, 2, 7), rotation_y=-90),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(-47, 2.1, -47), rotation_y=-90),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(-20, 3.9, -51.5), rotation_y=-180),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(30, 4, -51.5), rotation_y=-180),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(11, 2, 36)),
        Entity(model=resource_path('assets/models/wall_01.glb'), collider='box', position=Vec3(-42, 2, 36)),
        Entity(model=resource_path('assets/models/box.glb'), position=Vec3(50, 1.74, 46.5), scale=5, rotation_y=86.7),
        Entity(model=resource_path('assets/models/field_gate_01.glb'), scale=1.5, position=Vec3(-4.8, 2, 46), rotation_y=87),
        Entity(model=resource_path('assets/models/field_gate_01.glb'), scale=1.5, position=Vec3(-57, 2, -10), rotation_y=-38),
        Entity(model=resource_path('assets/models/oak_trees.glb'), position=Vec3(-3, 0.2, 48), scale=4),
        Entity(model=resource_path('assets/models/oak_trees.glb'), position=Vec3(4, 0.5, 50.2), scale=4.4, rotation_y=87),
        Entity(model=resource_path('assets/models/oak_trees.glb'), position=Vec3(-7, 1.1, -62.4), scale=4, rotation_y=71),
        Entity(model=resource_path('assets/models/oak_trees.glb'), position=Vec3(-57, 1.4, -6.1), scale=4.4, rotation_y=11)
    ]

    forest_model.enabled = True
    forest_collider.enabled = True
    big_metal_door.enabled = True
    field_gate_border.enabled = False

    first_stalker_house.enabled = False

village_spawn = False
run_sound_flag = False
sneak_flag = False

def sneak():
    player.camera_pivot.y = 2.2 - held_keys['left control']
    player.height = 2 - held_keys['left control']
    player.speed = speed - 2

    ray = raycast(origin=camera.world_position, direction=Vec3(0, 1, 0), distance=1, ignore=[camera, player])
   
    if ray.hit:
        player.jump_height = 0
    else:
        player.jump_height = 1.55

def stay():
    global sneak_flag

    ray = raycast(origin=camera.world_position, direction=Vec3(0, 1, 0), distance=1, ignore=[camera, player])

    if not ray.hit:
        player.camera_pivot.y = 2.7 - held_keys['left control']
        player.height = 2 - held_keys['left control']
        player.speed = speed + 2
        sneak_flag = True

def update():
    global current_recoil, fog, village_spawn, run_sound_flag, scope, reloading, run, tutorial, health, speed, sneak_flag, move_window, duel, health

    if health <= 0 and not duel:
        sio.emit('kill', { 'position': [player.x, player.y, player.z] })
        player.position = Vec3(52, 2.4, -18)
        health = 100
    elif health <= 0:
        sio.emit('kill', { 'position': [player.x, player.y, player.z] })
        if not duel_map_spawn_point:
            player.position = Vec3(965, 525, 905)
        else:
            player.position = Vec3(1044, 525, 1090)

        health = 100

    if tutorial:
        if not sneak_flag:
            sio.emit('move', {'x': player.x, 'y': player.y, 'z': player.z, 'ry': player.rotation.y})
        else:
            sio.emit('move', {'x': player.x, 'y': player.y - 1.4, 'z': player.z, 'ry': player.rotation.y})


    # move_speed = 20

    # x, y = window.position

    # if held_keys['left arrow']:
    #     x -= move_speed
    # if held_keys['right arrow']:
    #     x += move_speed

    # window.position = (x, y)

    info_bar.text = f"  {magazine}/{magazine_size}] | {max_bullets}  "
    health_bar.value = health

    forest_model.set_shader_input("camera_pos", camera.world_position)
    forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
    forest_model.set_shader_input("fog_density", fog)

    camera.rotation_x = lerp(camera.rotation_x, -current_recoil, time.dt * recoil_recovery_speed)
    current_recoil = lerp(current_recoil, 0, time.dt * (recoil_recovery_speed/2))

    if held_keys['right mouse'] and player.weapon and not reloading:
        if player.weapon_name == 'pm':
            scope = True
            pm.position = Vec3(-0.0217, -.432 - current_recoil*0.01, .5)
            pm.rotation = Vec3(0, 90, .00001)
        elif player.weapon_name == 'gold_deagle':
            scope = True
            goldEagle.position = Vec3(0, -.205 - current_recoil*0.01, .35)
            goldEagle.rotation = Vec3(0, 180, 0)
    elif player.weapon:
        if player.weapon_name == 'pm':
            scope = False
            goldEagle.position = Vec3(.5, -.24, .5)
            goldEagle.rotation = Vec3(0, 86, -1)
        elif player.weapon_name == 'gold_deagle':
            scope = False
            goldEagle.position = Vec3(.6, -.16, .33)
            goldEagle.rotation = Vec3(0, 178, -.1)

    if player.x > 49 and not village_spawn and not duel:
        village_spawn = True

        JSON_settings["game_settings"]["spawn_location"] = 'kordon'

        with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
            json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

        load_village()

    elif player.x < 46 and village_spawn:
        village_spawn = False

        JSON_settings["game_settings"]["spawn_location"] = 'tutorial'

        with open(resource_path('settings.json'), 'w', encoding='utf-8') as f:
            json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

        load_first_scene()

    # print(player.position)

    if (held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']) and player.grounded:
        if not run_sound_flag:
            running_sound.stop()
            running_sound.play()
            run_sound_flag = True
    else:
        if run_sound_flag:
            running_sound.stop()
            run_sound_flag = False


    if held_keys['shift'] and not scope and not reloading:
        player.speed = speed + 4
        camera.fov = 145
        if running_sound._clip is not None: running_sound.pitch = 1.6
        run = True
    elif scope and not reloading and player.weapon:
        player.speed = speed - 1.5
        camera.fov = 115
        if running_sound._clip is not None: running_sound.pitch = .7
    elif not reloading:
        run = False
        player.speed = speed
        camera.fov = 130
        if running_sound._clip is not None: running_sound.pitch = 1

    if held_keys['control'] and not sneak_flag:
        sneak()
        if running_sound._clip is not None: running_sound.pitch = 1.45
        sneak_flag = True
    elif sneak_flag and not held_keys['control']:
        stay()
        sneak_flag = False

    if player.y < -5:
        player.position = Vec3(player.x, 10, player.z)

if __name__ == '__main__':
    settings()
    build()

    player = FirstPersonController(y=2.2, x=0, z=0, origin_y=2, height=1, collider='capsule', speed=speed, jump_height=1.55, mouse_sensivity=(60, 60))
    player.camera_pivot.y = 2.7
    player.cursor.color = color.red
    player.cursor.model = 'sphere'
    player.cursor.scale = 0.003
    player.cursor.position = (0,0)

    if not tutorial: player.weapon = None
    elif tutorial and JSON_settings["game_settings"]["weapon"] == 'pm':
        player.weapon = pm
        player.weapon_name = "pm"
    elif tutorial and JSON_settings["game_settings"]["weapon"] == 'gold_deagle':
        player.weapon = goldEagle
        player.weapon_name = 'gold_deagle'

    player.first_door_key = None

    if not tutorial: load_first_scene()
    elif tutorial and JSON_settings["game_settings"]["spawn_location"] == 'tutorial': load_first_scene()
    elif tutorial and JSON_settings["game_settings"]["spawn_location"] == 'kordon':
        load_village()
    elif tutorial and JSON_settings["game_settings"]["spawn_location"] == 'duel':
        load_duelMap()


    app.run()