from SampleGenerator import generate_samples
import bpy
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, PointerProperty, IntProperty, EnumProperty, StringProperty, IntVectorProperty

bl_info = {
    "name": "Sample Generator",
    "author": "Bertram Sändig",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "View3D",
    "description": "Sample Generator for Machine Learning",
    "category": "Development",
}

class SampleGeneratorPanel(bpy.types.Panel):
    bl_idname = "WORLD_PT_sample_generator"
    bl_label = "Sample Generator"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"

    def draw(self, context):
      # box = self.layout.box()
      # box.prop(context.scene, 'sg_label_mode')
      # box.prop(context.scene, 'sg_render_mode')
      box = self.layout.box()
      # box.label(text="Custom Interface!")
      box.prop(context.scene, 'sg_objectGroup')
      box.prop(context.scene, 'sg_backgroundPath')
      box = self.layout.box()
      box.prop(context.scene, 'sg_cam')
      box.prop(context.scene, 'sg_sun')
      box.prop(context.scene, 'sg_ground')
      box.prop(context.scene, 'sg_cam_target')
      box = self.layout.box()
      box.prop(context.scene, 'sg_cam_dist')
      box.prop(context.scene, 'sg_img_size')
      box.prop(context.scene, 'sg_nSamples')
      self.layout.operator("object.generate_samples", text="Generate Samples")

class GenerateSamplesOperator(bpy.types.Operator):
    bl_idname = "object.generate_samples"
    bl_label = "Generate Training Samples"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}


    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
      # box = self.layout.box()
      # box.prop(context.scene, 'sg_label_mode')
      # box.prop(context.scene, 'sg_render_mode')
      box = self.layout.box()
      box.prop(context.scene, 'sg_objectGroup')
      box.prop(context.scene, 'sg_backgroundPath')
      box = self.layout.box()
      box.prop(context.scene, 'sg_cam')
      box.prop(context.scene, 'sg_sun')
      box.prop(context.scene, 'sg_ground')
      box.prop(context.scene, 'sg_cam_target')
      box = self.layout.box()
      box.prop(context.scene, 'sg_cam_dist')
      box.prop(context.scene, 'sg_img_size')
      box.prop(context.scene, 'sg_nSamples')

    def execute(self, context):
        generate_samples.main()
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(GenerateSamplesOperator.bl_idname)

def register():
    bpy.utils.register_class(SampleGeneratorPanel)

    # bpy.types.Scene.sg_label_mode = EnumProperty(
    #   items = [('sgSegment', 'Segmented','Segment'), ('sgBBox', 'Bounding Box','Bounding Box')],
    #   name = "Label Mode",
    #   description = "Controls which kind of labels are generated." )

    # bpy.types.Scene.sg_render_mode = EnumProperty(
    #   items = [('sgBackground', 'Background','Background'), ('sgCropped', 'Cropped','Cropped')],
    #   name = "Render Mode",
    #   description = "The rendering Mode.")

    bpy.types.Scene.sg_objectGroup = PointerProperty(
      type=bpy.types.Group,
      name = "Object Group",
      description = "An Object group with all objects that are to be rendered."
    )
    bpy.types.Scene.sg_backgroundPath = StringProperty(
      subtype = "FILE_PATH",
      name = "Background Path",
      description = "Path to background images."
    )

    bpy.types.Scene.sg_nSamples = IntProperty(
      name = "Number Samples",
      min = 0,
      max = 999999999,
      description = "Number of generated Samples.")

    bpy.types.Scene.sg_cam = PointerProperty(name="Camera", type=bpy.types.Object,
    description = "The scenes camera Object. (needed for perspective changes)")
    bpy.types.Scene.sg_sun = PointerProperty(name="Sun", type=bpy.types.Object,
    description = "The scenes Lightsource. (needed for light rotation and intensity adjustments)")
    bpy.types.Scene.sg_ground = PointerProperty(name="Ground", type=bpy.types.Object,
    description = "The scenes Ground Object. (will be set to shadow catcher and disabled for shadowless rendering)")
    bpy.types.Scene.sg_cam_target = PointerProperty(name="Camera Target", type=bpy.types.Object,
    description = "The camera Target. (Camera is always pointed at this)")
    bpy.types.Scene.sg_cam_dist = FloatProperty(
      name="Camera distance",
      default=2.2,
      subtype='DISTANCE',
      unit='LENGTH',
      description="Cameras distance to Objects."
      )
    bpy.types.Scene.sg_img_size = IntVectorProperty(
      name="Image Size",
      size=2,
      default=(300,300),
      description="Size of the rendered image (In Background rendering this is set to size of background image)."
      )

    bpy.utils.register_class(GenerateSamplesOperator)
    bpy.types.INFO_MT_render.append(menu_func)
 
def unregister():
    bpy.utils.unregister_class(GenerateSamplesOperator)