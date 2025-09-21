from ursina import *
from ursina import Audio
from ursina.shaders import lit_with_shadows_shader
from ursina.shaders import basic_lighting_shader
from ursina.prefabs.first_person_controller import FirstPersonController

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
max_bullets = 0


scope = False

def settings():
    window.vsync = False

    sky = Sky(texture='sky_sunset')

    scene.fog_color = color.black
    scene.fog_density = fog + 0.05

    window.fullscreen = True
    window.entity_counter.enabled = False
    window.collider_counter.enabled = False

def build():
    # first_house = Entity(model='assets/models/stalker_house.glb',collider='mesh')

    forest_collider = Entity(model='assets/models/forest.glb', collider='mesh', alpha=0, rotation_x=90, y=2, scale=7.6, parrent=forest_model)
    if not forest:
        forest_collider.collider = None

    ground = Entity(model='plane', scale=(500, 1, 500), texture='grass', texture_size=100, collider='box', y=2, visible=False)

    field_gate_border = Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(48.732334, 2.001, -26.814523), rotation_y=0)
    field_gate_border_collider = Entity(scale=(3.25, 5, .6), collider='box', parrent=field_gate_border, position=field_gate_border.position, rotation_y=field_gate_border.rotation.y)

    wall = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(37, 3.4, -40), rotation_y=90)
    wall = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(37, 2.2, 24), rotation_y=90)

    concrete_wall_protection = Entity(model='assets/models/concrete_wall_protection.glb', position=Vec3(54, 2, 14.19676), scale=1.5, collider='box', rotation_y=3, rotation_x=0.2)
    concrete_wall_protection = Entity(model='assets/models/concrete_wall_protection.glb', position=Vec3(73.2, 2, 14.19676), scale=1.5, collider='box', rotation_y=-3, rotation_x=3.4)

    block_post = Entity(model='assets/models/stalker_blockpost.glb', position=Vec3(130, 1.9, -15), rotation_y=-90, scale=43)

    first_stalker_house = Entity(model='assets/models/stalker_house.glb', scale=1.1)
    first_stalker_house_collider = Entity(model='assets/models/stalker_house.glb', alpha=0, collider='mesh', rotation=Vec3(90, -90, 90), parent=first_stalker_house, x=-.9145,y=2.402, z=-0.265)

    first_stalker_house_collider.collider.visible = False

    first_stalker_house.position = Vec3(65, 2, -2.49)
    first_stalker_house.rotation_y = -19

    sandbag_wall = Entity(model='assets/models/sandbag_wall.glb', position=Vec3(48.9, 2, 9), scale=1.9, rotation_y=-9, collider='box')

    btr = Entity(model='assets/models/btr.glb', position=Vec3(59, 2, -44), scale=1.76, rotation_y=-101, collider='box')

    pallet_of_boxes = Entity(model='assets/models/pallet_of_boxes.glb', position=Vec3(49, 2, -41), scale=3, rotation_y=1.2, collider='box')

    field = Entity(model='assets/models/field.glb', scale=20, position=Vec3(54, 2, -51))
    field = Entity(model='assets/models/field.glb', scale=20, position=Vec3(74, 2, -51))
    field = Entity(model='assets/models/field.glb', scale=20, position=Vec3(94, 2, -51))

    wall = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(62, 2.7, -67))
        
    concrete_wall_protection = Entity(model='assets/models/concrete_wall_protection.glb', position=Vec3(74, 2, -49), scale=1.6, collider='box', rotation_y=43, rotation_x=3)


lit_with_shadows_fog_shader = Shader(
    language=Shader.GLSL,
    vertex=open("assets/shaders/lit_with_fog_vertex.glsl").read(),
    fragment=open("assets/shaders/lit_with_fog_fragment.glsl").read(),
)

shoot_sound = Audio('assets/sounds/pm_shoot.mp3', autoplay=False)

reload_sound = Audio('assets/sounds/reload.mp3', autoplay=False)

empty_sound = Audio('assets/sounds/empty.mp3', autoplay=False)

pick_up_sound = Audio('assets/sounds/pick_up.mp3', autoplay=False)

running_sound = Audio('assets/sounds/running.mp3', autoplay=False, loop=True, volume=.4)

ambient_rain = Audio('assets/sounds/ambient_rain.mp3', autoplay=True, loop=True, volume=.3)

forest_model = Entity(model='assets/models/forest.glb',y=2,shader=lit_with_shadows_fog_shader,scale=7.6, visible=forest)
forest_model.set_shader_input("camera_pos", camera.world_position)
forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
forest_model.set_shader_input("fog_density", 0.0)

big_metal_door = Entity(model='assets/models/big_metal_door.glb', visible=False, collider=None, scale=3.7, position=Vec3(46.76389, 1.9, -25.409944))

wall1 = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-47, 2, 7), rotation_y=-90)
wall11 = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-47, 2.1, -47), rotation_y=-90)

wall2 = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-20, 3.9, -51.5), rotation_y=-180)
wall22 = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(30, 4, -51.5), rotation_y=-180)

wall3 = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(11, 2, 36))
wall33 = Entity(model='assets/models/wall_01.glb', collider='box', position=Vec3(-42, 2, 36))

box = Entity(model='assets/models/box.glb', position=Vec3(50, 1.74, 46.5), scale=5, rotation_y=86.7)

field_gate_border2 = Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(-4.8, 2, 46), rotation_y=87)

field_gate_border3 = Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(-57, 2, -10), rotation_y=-38)

oak_trees1 = Entity(model='assets/models/oak_trees.glb', position=Vec3(-3, 0.2, 48), scale=4)
oak_trees2 = Entity(model='assets/models/oak_trees.glb', position=Vec3(4, 0.5, 50.2), scale=4.4, rotation_y=87)
oak_trees3 = Entity(model='assets/models/oak_trees.glb', position=Vec3(-7, 1.1, -62.4), scale=4, rotation_y=71)
oak_trees4 = Entity(model='assets/models/oak_trees.glb', position=Vec3(-57, 1.4, -6.1), scale=4.4, rotation_y=11)

field_gate_border1 = Entity(model='assets/models/field_gate_01.glb', scale=1.5, position=Vec3(44, 2.05, 42), rotation_y=83)
field_gate_border_collider = Entity(scale=(3.25, 5, .6), collider='box', parrent=field_gate_border1, position=field_gate_border1.position, rotation_y=field_gate_border1.rotation.y)

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

ammo_9m = Entity(model='assets/models/9mm_ammo_box.glb', scale=.0008, position=Vec3(62, 2.9, -7), collider='box')
pistol = Entity(parent=scene, model='assets/models/pm.glb', origin_y=-.5, collider='box', position=Vec3(61, 2.6, -5.6), scale=.007, rotation_z=78, rotation_x=90, rotation_y=104)

def get_pistol():
    global magazine, magazine_size

    pick_up_sound.play()

    pistol.parent = camera
    pistol.position = Vec3(.5,-.24,.5)
    pistol.rotation = Vec3(0, 86, -1)
    player.pistol = pistol
    magazine_size = 12
    magazine = magazine_size
pistol.on_click = get_pistol

reload_time = 3
reloading = False

def get_ammo():
    global max_bullets

    pick_up_sound.play()
    max_bullets += 60

    destroy(ammo_9m)
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
    global last_shot_time, current_recoil, magazine, reloading, run

    now = time.time()

    if key == 'left mouse down' and player.pistol and magazine > 0 and not reloading:
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

            pistol.animate_rotation(pistol.rotation + Vec3(0,0,recoil_angle),
                                    duration=recoil_time, curve=curve.linear)
            invoke(lambda: pistol.animate_rotation(pistol.rotation - Vec3(0,0,recoil_angle/1.47),
                                                   duration=recoil_time, curve=curve.linear),
                   delay=recoil_time)
    if magazine == 0 and max_bullets == 0 and key == 'left mouse down' and not reloading and not run:
        empty_sound.stop()
        empty_sound.play()
        reload()

    if key == 'r' and not reloading and not run:
        reload()
    elif key == 'left mouse down' and player.pistol and magazine == 0 and max_bullets > 0 and not reloading and not run:
        empty_sound.stop()
        empty_sound.play()
        reload()

big_metal_door_close_flag = False
village_spawm = False
run_sound_flag = False

def update():
    global current_recoil, fog, big_metal_door_close_flag, village_spawm, run_sound_flag, scope, reloading, run

    # print(player.position)

    ammo_text.text = f"  [{magazine}/{magazine_size}] | {max_bullets}  "

    forest_model.set_shader_input("camera_pos", camera.world_position)
    forest_model.set_shader_input("fog_color", Vec4(0,0,0,1))
    forest_model.set_shader_input("fog_density", fog)

    camera.rotation_x = lerp(camera.rotation_x, -current_recoil, time.dt * recoil_recovery_speed)
    current_recoil = lerp(current_recoil, 0, time.dt * (recoil_recovery_speed/2))

    if held_keys['right mouse'] and player.pistol and not reloading:
        scope = True
        pistol.position = Vec3(-0.0217, -.432 - current_recoil*0.01, .5)
        pistol.rotation = Vec3(0, 90, .00001)
    else:
        if player.pistol:
            scope = False
            pistol.position = Vec3(.5, -.24, .5)
            pistol.rotation = Vec3(0, 86, -1)


    if player.position.x > 15 and not village_spawm:
        village_spawm = True

        acacia_tree = Entity(model='assets/models/acacia_tree.glb', position=Vec3(49, 2.1, -53), rotation_y=10)
        acacia_tree = Entity(model='assets/models/acacia_tree.glb', position=Vec3(48.7, 2.1, -46), rotation_y=30)
        acacia_tree = Entity(model='assets/models/acacia_tree.glb', position=Vec3(55, 2, -54), rotation_y=40)
        acacia_tree = Entity(model='assets/models/acacia_tree.glb', position=Vec3(60, 2.1, -52), rotation_y=70)
        acacia_tree = Entity(model='assets/models/acacia_tree.glb', position=Vec3(65, 1.9, -55), rotation_y=180)

        fern_grass = Entity(model='assets/models/fern_grass.glb', scale=62, position=Vec3(64, 2.4, -47))
        fern_grass = Entity(model='assets/models/fern_grass.glb', scale=62, position=Vec3(67, 2.4, -52))


    if player.position.x >= 49 and not big_metal_door_close_flag:
        big_metal_door_close_flag = True
        big_metal_door.visible = True
        big_metal_door.collider = 'box'

        ambient_rain.stop()

        scene.fog_density = 0.02
        fog = 0

        destroy(wall1)
        destroy(wall11)
        destroy(wall2)
        destroy(wall22)
        destroy(wall3)
        destroy(wall33)
        destroy(oak_trees1)
        destroy(oak_trees2)
        destroy(oak_trees3)
        destroy(oak_trees4)
        destroy(box)
        destroy(field_gate_border1)
        destroy(field_gate_border2)
        destroy(field_gate_border3)
        destroy(field_gate_border_collider)

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

if __name__ == '__main__':
    settings()
    build()

    player = FirstPersonController(y=2.2, x=0, z=0, origin_y=2, height=1, collider='capsule', speed=speed, jump_height=1.55, mouse_sensivity=(60, 60))
    player.cursor.color = color.red
    player.cursor.model = 'sphere'
    player.cursor.scale = 0.003
    player.cursor.position = (0,0)

    player.rifle = None
    player.pistol = None
    player.knife = None
    player.heal = None

    app.run()
