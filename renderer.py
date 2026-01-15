
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import os
import blf

_handles = []
texture = None
cached_shader = None

def load_texture():
    global texture
    # Calculate absolute path to sprite
    # Assumes this renderer.py is in the same folder as the sprite
    dir_path = os.path.dirname(os.path.abspath(__file__))
    sprite_path = os.path.join(dir_path, "Cat Sprite Sheet.png")
    
    if not os.path.exists(sprite_path):
        print(f"BlendPet Error: Sprite not found at {sprite_path}")
        return None

    # Load into Blender Data if not present
    img_name = "BlendPetSprite"
    img = bpy.data.images.get(img_name)
    if not img:
        try:
            img = bpy.data.images.load(sprite_path)
            img.name = img_name
        except Exception as e:
            print(f"BlendPet Error: Could not load image data: {e}")
            return None
    
    # Load into GPU
    if img:
        try:
            # -- SOFTWARE UPSCALING WORKAROUND --
            # Since GPU filtering is failing/ignoring 'NEAREST', we manually
            # upscale the pixel data so even 'Linear' looks sharp.
            try:
                import numpy as np
                
                # Get raw dimensions
                w, h = img.size
                
                # Access pixels (float array)
                # Optimization: resizing 256x320 is cheap with numpy
                px = np.array(img.pixels)
                px = px.reshape((h, w, 4))
                
                # Upscale factor (8x makes 1 pixel = 8x8 block)
                filescale = 8
                
                # Kronecker product / Repeat
                # Note: Blender images are bottom-up? flatten happens row by row.
                # reshape order is usually row-major.
                upscaled = px.repeat(filescale, axis=0).repeat(filescale, axis=1)
                
                # Create new container
                up_name = "BlendPetSprite_Upscaled"
                if up_name in bpy.data.images:
                    bpy.data.images.remove(bpy.data.images[up_name])
                
                up_img = bpy.data.images.new(up_name, w * filescale, h * filescale, alpha=True)
                up_img.pixels = upscaled.flatten()
                up_img.alpha_mode = 'STRAIGHT'
                
                # Use this for texture
                texture = gpu.texture.from_image(up_img)
                
            except Exception as e:
                print(f"BlendPet: Numpy Upscale failed ({e}), using raw image.")
                texture = gpu.texture.from_image(img)

            # FORCE PIXELATED LOOK (Still try, just in case)
            try:
                texture.filter_type = 'NEAREST' 
            except:
                pass
            return texture
        except Exception as e:
            print(f"BlendPet Error: GPU Texture creation failed: {e}")
            return None
    return None

def draw_callback():
    global texture
    
    if not texture:
        texture = load_texture()
        
    from . import pet_engine
    state = pet_engine.get_render_data()
    if not state:
        return
        
    x, y, row, frame_index, facing_right = state # unpack

    context = bpy.context
    region_width = context.region.width
    
    # Visual Configuration
    try:
        # Access Addon Preferences
        # __package__ is likely 'blend_pet'
        prefs = context.preferences.addons[__package__].preferences
        scale = prefs.pet_scale
    except:
        scale = 4.0 
    sprite_w = 32
    sprite_h = 32
    
    # Snap these to integers to avoid sub-pixel blurring
    w = int(sprite_w * scale)
    h = int(sprite_h * scale)
    
    # Position
    draw_x = int(x % region_width)
    draw_y = 0 # Walk on the absolute bottom edge of the region

    # -- Sprite Rendering --
    if texture:
        # UV Calculations
        tex_w, tex_h = texture.width, texture.height
        
        # Invert Row logic (assuming top-down row indices from user, but UV is bottom-up)
        # Row 0 (Top) -> UV Y near 1.0
        row_uv = row 
        
        # NOTE: Since we upscaled the texture uniformly, UV ratios remain identical.
        # 32 / 256 is same as (32*8) / (256*8).
        
        uv_y_top = 1.0 - (row_uv * sprite_h) / 320.0 # hardcoded base height to avoid confusion
        uv_y_bot = 1.0 - ((row_uv + 1) * sprite_h) / 320.0
        
        uv_x_left = (frame_index * sprite_w) / 256.0 # hardcoded base width
        uv_x_right = ((frame_index + 1) * sprite_w) / 256.0
        
        if not facing_right:
            uv_x_left, uv_x_right = uv_x_right, uv_x_left
            
        vertices = (
            (draw_x, draw_y),       # Bottom-Left
            (draw_x + w, draw_y),   # Bottom-Right
            (draw_x + w, draw_y + h), # Top-Right
            (draw_x, draw_y + h),   # Top-Left
        )
        
        indices = ((0, 1, 2), (2, 3, 0))
        
        texture_coords = (
            (uv_x_left, uv_y_bot),
            (uv_x_right, uv_y_bot),
            (uv_x_right, uv_y_top),
            (uv_x_left, uv_y_top),
        )
        
        # -- BUILTIN SHADER (Reliable) --
        shader_img = gpu.shader.from_builtin('IMAGE')
        batch_img = batch_for_shader(shader_img, 'TRIS', {"pos": vertices, "texCoord": texture_coords}, indices=indices)
        
        gpu.state.blend_set('ALPHA')
        shader_img.bind()
        try:
             shader_img.uniform_sampler("image", texture)
        except:
            pass
            
        batch_img.draw(shader_img)
        gpu.state.blend_set('NONE')
    else:
        # Fallback text only if texture completely fails
        pass


def register_draw_handler():
    if _handles:
        return
    
    print("BlendPet: Registering draw handler...")
    
    # Target Dope Sheet / Timeline / Graph
    space_types = [bpy.types.SpaceDopeSheetEditor, bpy.types.SpaceGraphEditor]
    
    for st in space_types:
        try:
            h = st.draw_handler_add(draw_callback, (), 'WINDOW', 'POST_PIXEL')
            _handles.append((st, h))
            print(f"BlendPet: Handler registered for {st}.")
        except Exception as e:
            print(f"BlendPet: Failed to register {st}: {e}")

def unregister_draw_handler():
    global _handles
    print(f"BlendPet: Unregistering {len(_handles)} handlers...")
    
    for st, h in _handles:
        try:
            st.draw_handler_remove(h, 'WINDOW')
            print(f"BlendPet: Removed handler for {st}")
        except Exception as e:
            print(f"BlendPet: Failed to remove handler from {st}: {e}")
            
    _handles.clear()
    
    # Force clear screen (Redraw one last time to remove the drawing)
    print("BlendPet: Forcing redraw...")
    try:
        context = bpy.context
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in ['DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'TIMELINE']:
                    area.tag_redraw()
    except Exception as e:
        print(f"BlendPet: Redraw force failed: {e}")
