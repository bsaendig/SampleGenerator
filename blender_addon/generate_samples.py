import bpy
from math import radians, pi, sin, cos
import random
import os, glob
from scipy import ndimage, misc
from skimage import draw, color
import numpy as np

def getChildren(objs):
    ## returns children of a blender object
    result = []
    for o in bpy.data.objects:
        p = o.parent
        if p:
            for target in objs:
                if p.name == target.name:
                    result.append(o)
                    break;
    return result

def place_objects_rand_on_bg(objects, img_list, step, tree_nodes):
    # not used in current version

    ## load background images and adjust blender scene
    # bg_img_path = img_list[random.randint(0, len(img_list)-1)] # randomized images
    bg_img_path = img_list[step % len(img_list)-1] # unrandomized
    print(bg_img_path)
    tree_nodes["Image"].image = bpy.data.images.load(bg_img_path)
    bg_size = np.asarray(bpy.data.images[bg_img_path.split('/')[-1]].size[:],dtype='float64')
    print(bg_size)
    bpy.data.scenes["Scene"].render.resolution_x = bg_size[0]
    bpy.data.scenes["Scene"].render.resolution_y = bg_size[1]

    # random list object positions
    OD = bpy.data.worlds["World"]["obj_distance"]
    object_positions = [(OD,0),(OD,OD),(0,OD),(-OD,OD),(-OD,0),(-OD,-OD),(0,-OD),(OD,-OD),(0,0)]
    random.shuffle(object_positions)
    object_positions = np.asarray(object_positions, 'float32')
    # hide all objects
    for obj in objects:
        obj.hide_render = True
        # obj.hide = True
    for child in getChildren(objects):
        child.hide_render = True
    # choose objects from the list; make visible, move and rotate
    objects_order = list(range(len(objects)))
    random.shuffle(objects_order)
    n_objects = random.randint(1,len(objects)-1)
    obj_center = np.asarray([0,0], 'float32')
    for i in range(n_objects):
        obj = objects[objects_order[i]]
        ## unhide
        obj.hide_render= False
        for child in getChildren([obj]):
            child.hide_render = False

        ## random rotation
        rotation_min = obj['rotation_range'][0]
        rotation_range = obj['rotation_range'][1] - rotation_min
        rotation_angle = rotation_min + rotation_range*random.random()
        obj.rotation_euler[2] = radians(rotation_angle)

        ## position
        pos = object_positions[i]
        obj.location[0] = pos[0]
        obj.location[1] = pos[1]
        obj_center+=pos
    # center_obj = objects[objects_order[0]]
    obj_center/=n_objects
    # Ground Texture to background for more realistic reflections
    bpy.data.images["ground.jpg"].filepath = bg_img_path
    return obj_center, bg_size

def cyclic_arangement(objects, camera, cam_dist, step, step_count, img_list):
    ## hides, reveals and rotates the objects and moves the camera so every object is visible for the same amount of images from a diverse range of viewpoints

    MAX_CAM_STEPS = 20 ## the max amount of camera steps to go from the lowest to the highest position and start again. lowest and highest position are defined by cam_pos_range
    BACKGROUND_REFLECTIONS = True

    # Image texture onto background for more realistic reflections
    if BACKGROUND_REFLECTIONS:
        bg_img_path = img_list[step % len(img_list)-1] # unrandomized
        bpy.data.images["ground.jpg"].filepath = bg_img_path

    # hide all objects
    for obj in objects:
        obj.hide_render = True
        # obj.hide = True
    for child in getChildren(objects):
        child.hide_render = True

    # get the current object when every object should be visible in the same number of render steps
    # (step_count/len(objects) is the number of steps for each object)
    steps_per_obj = step_count/len(objects)
    obj = objects[int(step/steps_per_obj)]

    # visibility and rotation of object
    obj.hide_render = False
    for child in getChildren([obj]):
        child.hide_render = False
    # obj.hide = False
    rotation_min = obj['rotation_range'][0]
    rotation_range = obj['rotation_range'][1] - rotation_min
    rotation_angle = rotation_min + (step % steps_per_obj) * (rotation_range / steps_per_obj)
    obj.rotation_euler[2] = radians(rotation_angle)
    
    # cam placement
    cam_steps = min(steps_per_obj, MAX_CAM_STEPS)
    cam_pos_min = obj['cam_pos_range'][0]
    cam_pos_range = obj['cam_pos_range'][1] - cam_pos_min
    camera.location[0] = cam_dist*cos(radians(cam_pos_min + (step%cam_steps)*cam_pos_range/cam_steps))
    camera.location[1] = 0
    camera.location[2] = cam_dist*sin(radians(cam_pos_min + (step%cam_steps)*cam_pos_range/cam_steps))

def random_cam_placement(camera, focus, target_obj):
    # not used in current version

    ## places the camera randomly
    
    x_range = camera["x_range"] #[.6,3.0]
    y_range = camera["y_range"] #[-0.25,0.25]
    z_range = camera["z_range"] #[.45,1.60]
    # x_rot_range = camera["x_rot_range"] #[-0.15,0.15]
    # y_rot_range = camera["y_rot_range"] #[-0.15,0.15]
    # z_rot_range = camera["z_rot_range"] #[-0.15,0.15]
    rand_pos = np.random.rand(3)
    # rand_rot = np.random.rand(3)
    camera.location[0] =x_range[1]-(x_range[1]-x_range[0])*rand_pos[0]
    camera.location[1] =y_range[1]-(y_range[1]-y_range[0])*rand_pos[1]
    camera.location[2] =z_range[1]-(z_range[1]-z_range[0])*rand_pos[2]

    # place the camera target
    target_obj.location[0] = focus[0]
    target_obj.location[1] = focus[1]

def shape_key_adjustments(objects):
    ## iterates all shape keys of all objects and sets them to a random value
    for obj in objects:
        if obj.data.shape_keys:
            keys = obj.data.shape_keys.key_blocks
            if len(keys):
                for i, k in enumerate(keys):
                    if i:
                        k.value = random.random()

def texture_adjustments():
    ## iterates all materials in the blender file and applies random adjustments based on naming conventions
    textures = bpy.data.materials #['rand_plastic']
    for t in textures:
        # random color for rand
        if "rand" in t.name:
            tex_nodes = t.node_tree.nodes
            for n in tex_nodes:
                if "RGB" in n.name:
                    if random.random() < .3: #30% chance for grey else random color
                        c=random.random()
                        n.outputs[0].default_value = [c, c, c, 1]
                    else:
                        n.outputs[0].default_value = [random.random(), random.random(), random.random(), 1]
                if "rand" in n.name:
                    n.outputs[0].default_value = random.random()
                if "switch" in n.name:
                    n.outputs[0].default_value = random.randint(0,1)
        # random shift for shift
        if "shift" in t.name:
            tex_nodes = t.node_tree.nodes
            for n in tex_nodes:
                if "Mapping" in n.name:
                    n.translation = [random.random()*10,random.random()*10,0]
        # random mix for mix
        if "mix" in t.name:
            tex_nodes = t.node_tree.nodes
            for n in tex_nodes:
                if "noise_mix" in n.name:
                    n.inputs[0].default_value = .35 + random.random()*.65

def save_label(output_path, bg_size, objects, bg_img_path=None, read_classes=True, segmentation=False):
    if segmentation:
        ## Save the segmentation image
        classImg = np.array(bpy.data.images['Viewer Node'].pixels[:]).reshape(bg_size[0],bg_size[1],-1)
        # One value per pixel
        classImg = classImg[::-1,:,0]
        # classImg = np.array( [ [ pixel[0] for pixel in row ] for row in classImg ] )
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        misc.toimage(classImg, cmin=0, cmax=255).save(output_path + str(bpy.data.scenes['Scene'].frame_current).zfill(4) + '.png')
        # misc.imsave(output_path + str(bpy.data.scenes['Scene'].frame_current).zfill(4) + '.png', classImg)
    else:
        f_label = open(output_path + str(bpy.data.scenes['Scene'].frame_current).zfill(4) + '.txt', 'w')
        if read_classes and os.path.isfile(bg_img_path[:-4] + '.txt'):
            bg_annotation = open(bg_img_path[:-4] + '.txt', 'r')
            f_label.write(bg_annotation.read())
            bg_annotation.close()
        classImg = np.array(bpy.data.images['Viewer Node'].pixels[:]).reshape(bg_size[1],bg_size[0],-1)
        # One value per pixel
        classImg = classImg[::-1,:,0]
        # YOLO style boundingboxes
        for i in range(len(objects)):
            # Finding non zero values
            mask = (classImg == i+1)
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            if rows.any():
                # min and max indices for bounding box
                ymin, ymax = np.where(rows)[0][[0, -1]]
                xmin, xmax = np.where(cols)[0][[0, -1]]
                print(ymin, ymax, xmin, xmax)
                x = ((xmin + xmax)/2)/ bg_size[0]
                width = (xmax - xmin) / bg_size[0]
                y = ((ymin + ymax)/2)/ bg_size[1]
                height = (ymax - ymin) / bg_size[1]
                if (width*height)>.005:
                    print("{} {} {} {} {}".format(objects[i]['class'],x,y,width,height))
                    print("{} {} {} {} {}".format(objects[i]['class'],x,y,width,height), file = f_label)

        f_label.close()

def main():
    # SEGMENTATION = bpy.context.scene.sg_label_mode == "sgSegment"
    # RENDER_CROPPED = bpy.context.scene.sg_render_mode == "sgCropped"
    SEGMENTATION = False
    RENDER_CROPPED = True

    cam = bpy.context.scene.sg_cam
    objects = bpy.context.scene.sg_objectGroup.objects
    # objects = [bpy.data.objects[obj] for obj in objectsList]
    sun = bpy.context.scene.sg_sun
    ground = bpy.context.scene.sg_ground
    lamp_sun = bpy.data.lamps[sun.name]
    cam_target = bpy.context.scene.sg_cam_target
    tree_nodes = bpy.context.scene.node_tree.nodes
    bg_size = bpy.context.scene.sg_img_size
    cam_dist = bpy.context.scene.sg_cam_dist
    compositing_node_group = bpy.data.scenes["Scene"].node_tree

    step_count = bpy.context.scene.sg_nSamples
    bg_path = bpy.context.scene.sg_backgroundPath.replace("//","")
    output_path = tree_nodes['File Output'].base_path.replace('//','./')

    img_list = sorted(glob.glob(bg_path+"*.png")+glob.glob(bg_path+"*.jpg"))
    
    if RENDER_CROPPED:
        output_path += 'rgba/'
    elif SEGMENTATION:
        output_path+="SegmentationClass/"
    else: 
        output_path+="rgb/"

    # Initial settings
    ground.cycles.is_shadow_catcher = True
    for i, o in enumerate(objects):
        if not 'class' in o:
            print(o.name, 'has no class yet. Set to 1.')
            o["class"] = 1
        if not 'rotation_range' in o:
            print(o.name, 'has no rotation range yet. Set to [0,360].')
            o["rotation_range"] = (0,360)
        if not 'cam_pos_range' in o:
            print(o.name, 'has no camera position range yet. Set to [0,90].')
            o["cam_pos_range"] = (0,90)
        o.pass_index = i + 1
        

    ## adjustments for cropped rendering
    if RENDER_CROPPED:
        ## place objects in the center of the scene
        for o in objects:
            o.location[0]=0
            o.location[1]=0
        cam_target.location[0]=0
        cam_target.location[1]=0
        bpy.data.scenes["Scene"].render.resolution_x = bg_size[0]
        bpy.data.scenes["Scene"].render.resolution_y = bg_size[1]
        c_nodes = compositing_node_group.nodes
        ## remove all links from render layers
        for out in c_nodes["Render Layers"].outputs:
            for l in out.links:
                compositing_node_group.links.remove(l)
        compositing_node_group.links.new(c_nodes["Render Layers"].outputs["Image"],c_nodes["File Output"].inputs[3])
        compositing_node_group.links.new(c_nodes["Render Layers"].outputs["IndexOB"],c_nodes["Viewer"].inputs[0])


    for step in range(0, step_count):

        if RENDER_CROPPED:
            cyclic_arangement(objects, cam, cam_dist, step, step_count, img_list)

        else:
            # Object placement
            obj_center, bg_size = place_objects_rand_on_bg(objects, img_list, step, tree_nodes)

            # random camera position
            random_cam_placement(cam, obj_center, cam_target)

        # random changes to textures
        texture_adjustments()

        # random changes to shape keys
        shape_key_adjustments(objects)

        # randomize light angle
        sun.rotation_euler[2] = random.random()*pi
        sun.rotation_euler[1] = random.random()*pi/2
        # randomize light strength
        sun.data.node_tree.nodes['Emission'].inputs[1].default_value = random.random()*7 + .8
        lamp_sun.shadow_soft_size = random.random()*.3+.015

        ## Rendering
        bpy.ops.render.render( write_still=True )

        # save Label
        if RENDER_CROPPED:
            save_label(output_path, bg_size, objects, read_classes=False, segmentation=SEGMENTATION)
        else:
            save_label(output_path, bg_size, objects, bg_img_path=bg_img_path, segmentation=SEGMENTATION)

        bpy.data.scenes['Scene'].frame_current += 1
    
    # hide all objects again
    for obj in objects:
        obj.hide_render = True

    bpy.data.scenes['Scene'].frame_current = 0

if __name__ == "__main__":
    main()