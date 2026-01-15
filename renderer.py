import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import os
import blf
from typing import Optional, List, Tuple, Any

# -- Constants --
SPRITE_SIZE = 32
SPRITE_COLUMNS = 8
SPRITE_ROWS = 10
UPSCALE_FACTOR = 8
IMAGE_NAME = "BlendPetSprite"
UPSCALED_IMAGE_NAME = "BlendPetSprite_Upscaled"

_handles: List[Tuple[Any, Any]] = []
texture: Optional[gpu.types.GPUTexture] = None
cached_shader: Optional[gpu.types.GPUShader] = None

def log(msg: str, is_error: bool = False):
    prefix = "BlendPet Error" if is_error else "BlendPet"
    print(f"{prefix}: {msg}")

def load_texture() -> Optional[gpu.types.GPUTexture]:
    global texture
    
    dir_path = os.path.dirname(os.path.abspath(__file__))
    sprite_path = os.path.join(dir_path, "textures", "Cat Sprite Sheet.png")
    
    if not os.path.exists(sprite_path):
        log(f"Sprite not found at {sprite_path}", is_error=True)
        return None

    img = bpy.data.images.get(IMAGE_NAME)
    if not img:
        try:
            img = bpy.data.images.load(sprite_path)
            img.name = IMAGE_NAME
        except Exception as e:
            log(f"Could not load image data: {e}", is_error=True)
            return None
    
    if img:
        try:
            # Try software upscaling for better 'Linear' filtering look if 'Nearest' fails
            upscale_success = False
            try:
                import numpy as np
                w, h = img.size
                px = np.array(img.pixels)
                px = px.reshape((h, w, 4))
                
                upscaled = px.repeat(UPSCALE_FACTOR, axis=0).repeat(UPSCALE_FACTOR, axis=1)
                
                if UPSCALED_IMAGE_NAME in bpy.data.images:
                    bpy.data.images.remove(bpy.data.images[UPSCALED_IMAGE_NAME])
                
                up_img = bpy.data.images.new(UPSCALED_IMAGE_NAME, w * UPSCALE_FACTOR, h * UPSCALE_FACTOR, alpha=True)
                up_img.pixels = upscaled.flatten()
                up_img.alpha_mode = 'STRAIGHT'
                
                texture = gpu.texture.from_image(up_img)
                upscale_success = True
                
            except ImportError:
                log("Numpy not found. Skipping software upscale.")
            except Exception as e:
                log(f"Numpy upscale failed: {e}")

            if not upscale_success:
                texture = gpu.texture.from_image(img)

            # Attempt to set NEAREST filtering
            try:
                texture.filter_type = 'NEAREST' 
            except:
                pass
            return texture
        except Exception as e:
            log(f"GPU Texture creation failed: {e}", is_error=True)
            return None
    return None

def draw_callback():
    global texture
    
    if not texture:
        texture = load_texture()
        
    try:
        from . import pet_engine
        state = pet_engine.get_render_data()
    except ImportError:
        # If running as relative package fails (e.g. standalone test)
        import pet_engine
        state = pet_engine.get_render_data()
        
    if not state:
        return
        
    x, y, row, frame_index, facing_right = state 

    context = bpy.context
    region_width = context.region.width
    
    # Visual Configuration
    try:
        prefs = context.preferences.addons[__package__].preferences
        scale = prefs.pet_scale
    except:
        scale = 4.0 
    
    # Snap these to integers to avoid sub-pixel blurring
    w = int(SPRITE_SIZE * scale)
    h = int(SPRITE_SIZE * scale)
    
    # Position
    draw_x = int(x % region_width)
    draw_y = 0 

    if texture:
        # UV Calculations
        uv_y_top = 1.0 - (row * SPRITE_SIZE) / (SPRITE_SIZE * SPRITE_ROWS)
        uv_y_bot = 1.0 - ((row + 1) * SPRITE_SIZE) / (SPRITE_SIZE * SPRITE_ROWS)
        
        uv_x_left = (frame_index * SPRITE_SIZE) / (SPRITE_SIZE * SPRITE_COLUMNS)
        uv_x_right = ((frame_index + 1) * SPRITE_SIZE) / (SPRITE_SIZE * SPRITE_COLUMNS)
        
        if not facing_right:
            uv_x_left, uv_x_right = uv_x_right, uv_x_left
            
        vertices = (
            (draw_x, draw_y),
            (draw_x + w, draw_y),
            (draw_x + w, draw_y + h),
            (draw_x, draw_y + h),
        )
        
        indices = ((0, 1, 2), (2, 3, 0))
        
        texture_coords = (
            (uv_x_left, uv_y_bot),
            (uv_x_right, uv_y_bot),
            (uv_x_right, uv_y_top),
            (uv_x_left, uv_y_top),
        )
        
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
