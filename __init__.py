
import bpy
import os
from . import pet_engine
from . import renderer

bl_info = {
    "name": "BlendPet",
    "author": "nova3D",
    "version": (1, 1),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > BlendPet",
    "description": "A useless but cute pet that lives in your Blender viewport.",
    "category": "3D View",
}

class BlendPetPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    
    pet_scale: bpy.props.FloatProperty(
        name="Pet Scale",
        default=4.0,
        min=1.0,
        max=10.0,
        description="How big the cat is"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "pet_scale")

# ... imports
import bpy.utils.previews

# Global preview collection
preview_collections = {}

def draw_pet_header(self, context):
    layout = self.layout
    # Header Toggle
    is_running = context.window_manager.get("blendpet_running", False)
    
    try:
        pcoll = preview_collections.get("main")
        if pcoll and "custom_icon" in pcoll:
            my_icon = pcoll["custom_icon"]
            layout.operator("view3d.toggle_blendpet", text="", icon_value=my_icon.icon_id, depress=is_running)
        else:
            # Fallback if icon is missing key
            layout.operator("view3d.toggle_blendpet", text="", icon='MONKEY', depress=is_running)
    except Exception as e:
        # Fallback on any error (e.g. pcoll missing)
        layout.operator("view3d.toggle_blendpet", text="", icon='MONKEY', depress=is_running)

class VIEW3D_OT_PetLoop(bpy.types.Operator):
    bl_idname = "view3d.blendpet_loop"
    bl_label = "BlendPet Loop"
    bl_options = {'REGISTER'}

    _timer = None

    def modal(self, context, event):
        if not context.window_manager.get("blendpet_running"):
            # Stop condition
            return self.cancel(context)

        if event.type == 'TIMER':
            width = 1000
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type in ['DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'TIMELINE']:
                         width = area.width
                         break
            pet_engine.update(width)
            
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type in ['DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'TIMELINE', 'SEQUENCE_EDITOR', 'CLIP_EDITOR']:
                        area.tag_redraw()

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        wm["blendpet_running"] = True
        base_path = os.path.dirname(__file__)
        sprite_path = os.path.join(base_path, "textures", "Cat Sprite Sheet.png")
        pet_engine.initialize(sprite_path)
        renderer.register_draw_handler()
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None
        renderer.unregister_draw_handler()
        wm["blendpet_running"] = False
        return {'FINISHED'}

class VIEW3D_OT_ToggleBlendPet(bpy.types.Operator):
    bl_idname = "view3d.toggle_blendpet"
    bl_label = "Toggle Pet"
    bl_description = "Summon or Banish the pet"

    def execute(self, context):
        wm = context.window_manager
        if wm.get("blendpet_running"):
            wm["blendpet_running"] = False
            self.report({'INFO'}, "Pet Banished!")
        else:
            bpy.ops.view3d.blendpet_loop()
            self.report({'INFO'}, "Pet Summoned!")
        return {'FINISHED'}

classes = (
    BlendPetPreferences,
    VIEW3D_OT_ToggleBlendPet,
    VIEW3D_OT_PetLoop,
)

def register():
    # Register Property
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Load Custom Icon
    pcoll = bpy.utils.previews.new()
    dir_path = os.path.dirname(__file__)
    icon_path = os.path.join(dir_path, "textures", "icon.png")
    
    print(f"BlendPet: Loading icon from {icon_path}")
    if not os.path.exists(icon_path):
        print("BlendPet: ICON FILE NOT FOUND!")
    
    try:
        pcoll.load("custom_icon", icon_path, 'IMAGE')
        preview_collections["main"] = pcoll
        print(f"BlendPet: Icon loaded. ID: {pcoll['custom_icon'].icon_id}")
    except Exception as e:
        print(f"BlendPet: Failed to load icon: {e}")
    
    # Append to Header
    bpy.types.VIEW3D_HT_header.append(draw_pet_header)

def unregister():
    # Remove from Header
    bpy.types.VIEW3D_HT_header.remove(draw_pet_header)
    
    # Unload Icon
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
