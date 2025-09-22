import socketio
import json
from ursina import *
from ursina import Audio
from ursina.shaders import lit_with_shadows_shader
from ursina.shaders import basic_lighting_shader
from ursina.prefabs.first_person_controller import FirstPersonController

sio = socketio.Client()
sio.connect('https://stalker-server-z2l9.onrender.com', transports=['websocket'])

other_players = {}
tutorial = False

max_bullets = 0
health = 100

with open('settings.json', 'r', encoding='utf-8') as f:
    JSON_settings = json.load(f)

    tutorial = JSON_settings["game_settings"]["tutorial"]
    max_bullets = JSON_settings["game_settings"]["max_bullets"]

@sio.event
def hit(data):
    global health

    health -= data["damage"]

@sio.event
def update_players(data):
    global other_players
    for sid, pos in data.items():
        if sid == sio.sid:
            continue
        if sid not in other_players:
            other_players[sid] = Entity(
                model='assets/models/stalker.glb',
                scale=2,
                collider='box'
            )
        other_players[sid].position = Vec3(pos['x'], pos['y'] + 2.4, pos['z'])
        other_players[sid].rotation_y = pos.get('ry', 0) + 180


@sio.event
def new_player(data):
    sid = data['sid']
    if sid != sio.sid and sid not in other_players:
        other_players[sid] = Entity(
            model='assets/models/stalker.glb',
            scale=2,
            collider='box'
        )
        other_players[sid].position = Vec3(data['x'], data['y'] + 2.4, data['z'])
        other_players[sid].rotation_y = data.get('ry', 0) + 180


@sio.event
def move(data):
    sid = data['sid']
    if sid in other_players:
        other_players[sid].position = Vec3(data['x'], data['y'] + 2.4, data['z'])
        other_players[sid].rotation_y = data.get('ry', 0) + 180


@sio.event
def remove_player(sid):
    if sid in other_players:
        destroy(other_players[sid])
        del other_players[sid]

@sio.event
def disconnect():
    print("disconnected.")

@sio.event
def connect():
    print("connected.")

app = Ursina()

fog = 0.5
speed = 6
forest = True
max_recoil = 120
recoil_per_shot = 6
recoil_recovery_speed = 14
current_recoil = 0
recoil_angle = 5
recoil_time = 0.05
fire_rate = 0.14
last_shot_time = 0
magazine_size = 0
magazine = magazine_size

scope = False

current_location = []
location_id = 0

lit_with_shadows_fog_shader = Shader(
    language=Shader.GLSL,
    vertex=open("assets/shaders/lit_with_fog_vertex.glsl").read(),
    fragment=open("assets/shaders/lit_with_fog_fragment.glsl").read(),
)

ground = Entity(model='plane', scale=(1000, 1, 1000), collider='box', y=2, visible=False)

shoot_sound = Audio('assets/sounds/pm_shoot.mp3', autoplay=False)

reload_sound = Audio('assets/sounds/reload.mp3', autoplay=False)

empty_sound = Audio('assets/sounds/empty.mp3', autoplay=False)

pick_up_sound = Audio('assets/sounds/pick_up.mp3', autoplay=False)
get_key_sound = Audio('assets/sounds/get_key.mp3', autoplay=False)

running_sound = Audio('assets/sounds/running.mp3', autoplay=False, loop=True, volume=.4)

ambient_rain = Audio('assets/sounds/ambient_rain.mp3', autoplay=True, loop=True, volume=.3)

forest_model = Entity(model='assets/models/forest.glb',y=2,shader=lit_with_shadows_fog_shader,scale=7.6, visible=forest, enabled=True)
forest_model.set_shader_input("camera_pos", camera.world_position)
forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
forest_model.set_shader_input("fog_density", 0.0)
forest_collider = Entity(model='assets/models/forest.glb', collider='mesh', alpha=0, rotation_x=90, y=2, scale=7.6, parrent=forest_model, visible=0)

field_gate_border = Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(48.732334, 2.001, -26.814523), rotation_y=0, enabled=False)
field_gate_border_collider = Entity(scale=(3.25, 5, .6), collider='box', parrent=field_gate_border, position=field_gate_border.position, rotation_y=field_gate_border.rotation.y)

first_stalker_house = Entity(model='assets/models/stalker_house.glb', scale=1.1, enabled=False)
first_stalker_house_collider = Entity(model='assets/models/stalker_house.glb', alpha=0, collider='mesh', rotation=Vec3(90, -90, 90), parent=first_stalker_house, x=-.9145,y=2.402, z=-0.265)

Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(37, 3.4, -40), rotation_y=90)
Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(37, 2.2, 24), rotation_y=90)

big_metal_door = Entity(model='assets/models/big_metal_door.glb', collider='box', scale=3.7, position=Vec3(46.76389, 1.9, -25.409944), enabled=False)

def settings():
    window.vsync = False

    sky = Sky(texture='sky_sunset')

    scene.fog_color = color.black
    scene.fog_density = fog + 0.04

    window.fullscreen = False
    window.entity_counter.enabled = False
    window.collider_counter.enabled = False

def build():
    # first_house = Entity(model='assets/models/stalker_house.glb',collider='mesh')
    if not forest:
        forest_collider.collider = None

    first_stalker_house_collider.collider.visible = False

    first_stalker_house.position = Vec3(65, 2, -2.49)
    first_stalker_house.rotation_y = -19

    field_gate_border1 = Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(44, 2.05, 42), rotation_y=83)
    Entity(scale=(3.25, 5, .6), collider='box', parrent=field_gate_border1, position=field_gate_border1.position, rotation_y=field_gate_border1.rotation.y)

    a = Entity(model='quad', position=Vec3(46.7, 8, 9.7), collider='box', scale=(32,27,5), rotation_y=90, visible=False)
    a.collider.visible = True


ammo_bg = Entity(
    parent=camera.ui,
    model='quad',
    color=color.rgba(0, 0, 0, 180),
    scale=(0.25, 0.12),
    position=(0.75, -0.45)
)

ammo_text = Text(
    parent=ammo_bg,
    text=f"{magazine}/{magazine_size} | {max_bullets}",
    origin=(0,0),
    scale=6,
    position=(0,0),
    color=color.white
)

ammo_9m = Entity(model='assets/models/9mm_ammo_box.glb', scale=.0008, position=Vec3(62, 2.9, -7), collider='box', enabled=False)
pistol = Entity(parent=scene, model='assets/models/pm.glb', origin_y=-.5, collider='box', position=Vec3(61, 2.6, -5.6), scale=.007, rotation_z=78, rotation_x=90, rotation_y=104, enabled=False)

if tutorial and JSON_settings["game_settings"]["weapon"] == None:
    ammo_9m.enabled = True
    pistol.enabled = True
elif tutorial and JSON_settings["game_settings"]["weapon"] == 'pm':
    pistol.enabled = True
    pistol.parent = camera
    pistol.collider = None
    pistol.position = Vec3(.5,-.24,.5)
    pistol.rotation = Vec3(0, 86, -1)
    magazine_size = 12
    magazine = JSON_settings["game_settings"]["magazine"]
    speed -= 0.4

first_door_key = Entity(model='assets/models/door_key.glb', scale=.01, collider='box', position=Vec3(-28.65, 2, 13.), parent=scene, enabled=True)
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

        ammo_9m.enabled = True
        pistol.enabled = True

        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

big_metal_door.on_click = open_first_door

def get_pistol():
    global magazine, magazine_size, speed, JSON_settings

    pick_up_sound.play()

    pistol.parent = camera
    pistol.collider = None
    pistol.position = Vec3(.5,-.24,.5)
    pistol.rotation = Vec3(0, 86, -1)
    player.weapon = pistol
    magazine_size = 12
    magazine = magazine_size
    speed -= 0.4

    JSON_settings["game_settings"]["weapon"] = 'pm'
    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

pistol.on_click = get_pistol

reload_time = 3
reloading = False

def get_ammo():
    global max_bullets, JSON_settings

    pick_up_sound.play()
    max_bullets += 60

    destroy(ammo_9m)

    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

ammo_9m.on_click = get_ammo

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
    global last_shot_time, current_recoil, magazine, reloading, run, JSON_settings

    now = time.time()

    JSON_settings["game_settings"]["magazine"] = magazine
    JSON_settings["game_settings"]["max_bullets"] = max_bullets

    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

    if key == 'left mouse down' and player.weapon and magazine > 0 and not reloading:
        fire_rate = 0.17
        if now - last_shot_time >= fire_rate:
            bullet = Entity(model='sphere', scale=.09, color=color.black, position=pistol.world_position + Vec3(.3, .5, 0))
            bullet.animate_position(bullet.position + (camera.forward * 100), curve=curve.linear, duration=.7)
            destroy(bullet, delay=5)
            last_shot_time = now
            magazine -= 1
            shoot_sound.stop()
            shoot_sound.play()
            current_recoil += recoil_per_shot
            if current_recoil > max_recoil:
                current_recoil = max_recoil

        ray = raycast(
            player.position,
            camera.forward,
            distance=100,
            ignore=[player, forest, ground, field_gate_border_collider]
        )

        weapon_name = player.weapon_name
        print(player.weapon_name)

        for sid, ent in other_players.items():
            if ray.entity is ent:
                sio.emit('hit', {'player': sid,'weapon': weapon_name,'distance': ray.distance})
                print(f'HIT {sid} with {weapon_name}')

            pistol.animate_rotation(pistol.rotation + Vec3(0,0,recoil_angle),
                                    duration=recoil_time, curve=curve.linear)
            invoke(lambda: pistol.animate_rotation(pistol.rotation - Vec3(0,0,recoil_angle/1.47),
                                                   duration=recoil_time, curve=curve.linear),
                   delay=recoil_time)
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


def load_village():
    global current_location, forest, location_id, fog

    location_id = 1

    player.position.y = 20

    fog = 0

    forest_model.set_shader_input("camera_pos", camera.world_position)
    forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
    forest_model.set_shader_input("fog_density", fog)

    scene.fog_color = color.black
    scene.fog_density = fog + 0.02

    for e in current_location:
        destroy(e)
    current_location = [
        Entity(model='assets/models/concrete_wall_protection.glb', position=Vec3(54, 2, 14.19676), scale=1.5, collider='box', rotation_y=3, rotation_x=0.2),
        Entity(model='assets/models/concrete_wall_protection.glb', position=Vec3(73.2, 2, 14.19676), scale=1.5, collider='box', rotation_y=-3, rotation_x=3.4),
        Entity(model='assets/models/stalker_blockpost.glb', position=Vec3(130, 1.9, -15), rotation_y=-90, scale=43),
        Entity(model='assets/models/sandbag_wall.glb', position=Vec3(48.9, 2, 9), scale=1.9, rotation_y=-9, collider='box'),
        Entity(model='assets/models/btr.glb', position=Vec3(59, 2, -44), scale=1.76, rotation_y=-101, collider='box'),
        Entity(model='assets/models/pallet_of_boxes.glb', position=Vec3(49, 2, -41), scale=3, rotation_y=1.2, collider='box'),
        Entity(model='assets/models/field.glb', scale=20, position=Vec3(54, 2, -51)),
        Entity(model='assets/models/field.glb', scale=20, position=Vec3(74, 2, -51)),
        Entity(model='assets/models/field.glb', scale=20, position=Vec3(94, 2, -51)),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(62, 2.7, -67)),
        Entity(model='assets/models/concrete_wall_protection.glb', position=Vec3(74, 2, -49), scale=1.6, collider='box', rotation_y=43, rotation_x=3),
        Entity(model='assets/models/acacia_tree.glb', position=Vec3(49, 2.1, -53), rotation_y=10),
        Entity(model='assets/models/acacia_tree.glb', position=Vec3(48.7, 2.1, -46), rotation_y=30),
        Entity(model='assets/models/acacia_tree.glb', position=Vec3(55, 2, -54), rotation_y=40),
        Entity(model='assets/models/acacia_tree.glb', position=Vec3(60, 2.1, -52), rotation_y=70),
        Entity(model='assets/models/acacia_tree.glb', position=Vec3(65, 1.9, -55), rotation_y=180),
        Entity(model='assets/models/fern_grass.glb', scale=62, position=Vec3(64, 2.4, -47)),
        Entity(model='assets/models/fern_grass.glb', scale=62, position=Vec3(67, 2.4, -52)),
    ]

    forest_model.enabled = True
    big_metal_door.enabled = True
    field_gate_border.enabled = True

    first_stalker_house.enabled = True

def load_first_scene():
    global current_location, forest, location_id
    
    location_id = 0

    for e in current_location:
        destroy(e)

    current_location = [
        Entity(model='assets/models/big_metal_door.glb', visible=False, collider=None, scale=3.7, position=Vec3(46.76389, 1.9, -25.409944)),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-47, 2, 7), rotation_y=-90),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-47, 2.1, -47), rotation_y=-90),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-20, 3.9, -51.5), rotation_y=-180),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(30, 4, -51.5), rotation_y=-180),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(11, 2, 36)),
        Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-42, 2, 36)),
        Entity(model='assets/models/box.glb', position=Vec3(50, 1.74, 46.5), scale=5, rotation_y=86.7),
        Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(-4.8, 2, 46), rotation_y=87),
        Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(-57, 2, -10), rotation_y=-38),
        Entity(model='assets/models/oak_trees.glb', position=Vec3(-3, 0.2, 48), scale=4),
        Entity(model='assets/models/oak_trees.glb', position=Vec3(4, 0.5, 50.2), scale=4.4, rotation_y=87),
        Entity(model='assets/models/oak_trees.glb', position=Vec3(-7, 1.1, -62.4), scale=4, rotation_y=71),
        Entity(model='assets/models/oak_trees.glb', position=Vec3(-57, 1.4, -6.1), scale=4.4, rotation_y=11)
    ]

    forest_model.enabled = True
    big_metal_door.enabled = True
    field_gate_border.enabled = False

    first_stalker_house.enabled = False

village_spawn = False
run_sound_flag = False

def update():
    global current_recoil, fog, village_spawn, run_sound_flag, scope, reloading, run, tutorial, health

    if health <= 0:
        player.position = Vec3(52, 2.4, -18)
        health = 100

    if tutorial: sio.emit('move', {'x': player.x, 'y': player.y, 'z': player.z, 'ry': player.rotation.y})

    move_speed = 20

    x, y = window.position

    if held_keys['left arrow']:
        x -= move_speed
    if held_keys['right arrow']:
        x += move_speed

    window.position = (x, y)

    ammo_text.text = f"  [{magazine}/{magazine_size}] | {max_bullets}  "

    forest_model.set_shader_input("camera_pos", camera.world_position)
    forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
    forest_model.set_shader_input("fog_density", fog)

    camera.rotation_x = lerp(camera.rotation_x, -current_recoil, time.dt * recoil_recovery_speed)
    current_recoil = lerp(current_recoil, 0, time.dt * (recoil_recovery_speed/2))

    if held_keys['right mouse'] and player.weapon and not reloading:
        scope = True
        pistol.position = Vec3(-0.0217, -.432 - current_recoil*0.01, .5)
        pistol.rotation = Vec3(0, 90, .00001)
    else:
        if player.weapon:
            scope = False
            pistol.position = Vec3(.5, -.24, .5)
            pistol.rotation = Vec3(0, 86, -1)

    if player.x > 49 and not village_spawn:
        village_spawn = True

        JSON_settings["game_settings"]["spawn_lokation"] = 'kordon'

        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(JSON_settings, f, indent=4, ensure_ascii=False)

        load_village()

    elif player.x < 46 and village_spawn:
        village_spawn = False

        JSON_settings["game_settings"]["spawn_lokation"] = 'tutorial'

        with open('settings.json', 'w', encoding='utf-8') as f:
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
        running_sound.pitch = 1.56
        run = True
    elif scope and not reloading:
        player.speed = speed - 1.7
        camera.fov = 115
        running_sound.pitch = .7
    elif not reloading:
        run = False
        player.speed = speed
        camera.fov = 130
        running_sound.pitch = 1

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
        player.weapon = pistol
        player.weapon_name = "pm"

    player.first_door_key = None

    if not tutorial: load_first_scene()
    elif tutorial and JSON_settings["game_settings"]["spawn_lokation"] == 'tutorial': load_first_scene()
    elif tutorial and JSON_settings["game_settings"]["spawn_lokation"] == 'kordon':
        load_village()
        player.position = Vec3(52, 2.4, -18)

    app.run()
