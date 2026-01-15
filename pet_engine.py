import random
import time
from typing import Optional, Dict, List, Tuple

# -- Constants --
DEFAULT_FPS = 10
DEFAULT_SCALE = 4.0
DEFAULT_MARGIN = 40
DEFAULT_FRAME_COUNT = 4

# Animation Row Mapping
ANIM_ROWS: Dict[str, int] = {
    'IDLE': 0,
    'IDLE2': 1,
    'LICK': 2,
    'CLEAN': 3,
    'WALK': 4,
    'RUN': 5,
    'SLEEP': 6,
    'PLAY': 7,
    'POUNCE': 8,
    'LOOK_BEHIND': 9
}

# Number of frames per animation row
FRAME_COUNTS: Dict[str, int] = {
    'IDLE': 4,
    'IDLE2': 4,
    'LICK': 4,
    'CLEAN': 4,
    'WALK': 6,
    'RUN': 6, 
    'SLEEP': 4,
    'PLAY': 6,
    'POUNCE': 7,
    'LOOK_BEHIND': 4
}

# Custom FPS per state
STATE_FPS: Dict[str, int] = {
    'LOOK_BEHIND': 5,
    'SLEEP': 2,
}

NON_LOOPING_STATES = {'LOOK_BEHIND', 'PLAY', 'POUNCE', 'IDLE2'}

def log(msg: str, is_error: bool = False):
    prefix = "BlendPet Error" if is_error else "BlendPet"
    print(f"{prefix}: {msg}")

class PetEngine:
    """Handles pet logic, state transitions, and animation timing."""
    def __init__(self, sprite_path: str):
        self.sprite_path = sprite_path
        self.x: float = 100.0
        self.y: float = 0.0
        
        self.state: str = 'IDLE'
        self.row: int = ANIM_ROWS['IDLE']
        self.frame_index: int = 0
        
        self.facing_right: bool = True
        
        self.timer: float = 0.0
        self.last_tick: float = time.time()
        
        self.state_timer: float = 0.0
        self.state_duration: float = 5.0
        
        self.target_x: float = 100.0
        self.speed: float = 2.0

    def set_state(self, new_state: str):
        """Transition to a new animation state."""
        if new_state not in ANIM_ROWS:
            log(f"Unknown state: {new_state}", is_error=True)
            return
            
        self.state = new_state
        self.row = ANIM_ROWS[new_state]
        self.frame_index = 0
        self.state_timer = 0.0
        
        # Determine how long to stay in this state
        if self.state == 'SLEEP':
            self.state_duration = random.uniform(20.0, 40.0)
        elif self.state in NON_LOOPING_STATES:
            self.state_duration = 3.0 
        else:
            self.state_duration = random.uniform(5.0, 10.0)
        
        # Initialize state-specific logic
        if self.state in ['WALK', 'RUN']:
            self.target_x = random.uniform(100, 1000) 
            self.facing_right = self.target_x > self.x
            
    def update(self, screen_width: Optional[float] = None):
        """Update physics and animation frames."""
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now
        
        self.timer += dt
        self.state_timer += dt
        
        # -- Animation Loop --
        target_fps = STATE_FPS.get(self.state, DEFAULT_FPS)
        frame_time = 1.0 / target_fps
        
        limit = FRAME_COUNTS.get(self.state, DEFAULT_FRAME_COUNT)
        if self.timer >= frame_time:
            if self.state in NON_LOOPING_STATES:
                 if self.frame_index >= limit - 1:
                     self.set_state('IDLE')
                     return 
            
            self.frame_index = (self.frame_index + 1) % limit
            self.timer = 0.0
            
        # -- Movement --
        moved = False
        if self.state == 'WALK':
            dx = self.target_x - self.x
            step = 1.5 * (dt * 60.0) 
            
            if abs(dx) < step:
                self.x = self.target_x
                self.set_state('IDLE')
            else:
                self.x += step if dx > 0 else -step
                moved = True
                
        elif self.state == 'RUN':
             dx = self.target_x - self.x
             step = 4.0 * (dt * 60.0)
             
             if abs(dx) < step:
                 self.x = self.target_x
                 self.set_state('IDLE')
             else:
                 self.x += step if dx > 0 else -step
                 moved = True
        
        # -- Wall Collision --
        if screen_width and moved:
             margin = DEFAULT_MARGIN
             if self.x <= margin:
                 self.x = margin + 1.0
                 self.facing_right = True
                 self.target_x = random.uniform(self.x + 100, screen_width - margin)
                 
             elif self.x >= screen_width - margin:
                 self.x = screen_width - margin - 1.0
                 self.facing_right = False
                 self.target_x = random.uniform(margin, self.x - 100)

        # -- State Transitions --
        if self.state_timer > self.state_duration:
            self.pick_new_state()

    def pick_new_state(self):
        """Decide the next state based on current behavior."""
        if self.state == 'SLEEP':
            self.set_state('IDLE2')
            return
            
        if self.state == 'IDLE2':
            choices = ['IDLE', 'WALK']
            weights = [0.5,    0.5]
            self.set_state(random.choices(choices, weights=weights, k=1)[0])
            return

        choices = ['IDLE', 'IDLE2', 'SLEEP', 'LICK', 'WALK', 'RUN', 'LOOK_BEHIND', 'CLEAN', 'PLAY', 'POUNCE']
        weights = [0.35,   0.05,    0.1,     0.1,    0.25,   0.05,  0.02,           0.05,    0.02,   0.01]
        
        next_state = random.choices(choices, weights=weights, k=1)[0]
        self.set_state(next_state)

# -- Singleton Instance --
engine: Optional[PetEngine] = None

def initialize(sprite_path: str):
    """Initialize the engine singleton."""
    global engine
    engine = PetEngine(sprite_path)
    engine.set_state('IDLE')

def update(screen_width: Optional[float] = None):
    """Update logic for the singleton engine."""
    if engine:
        engine.update(screen_width)

def get_render_data() -> Optional[Tuple[float, float, int, int, bool]]:
    """Get state data for rendering."""
    if engine:
        return (engine.x, engine.y, engine.row, engine.frame_index, engine.facing_right)
    return None

def set_state(name: str):
    """Manually force a state on the engine."""
    if engine:
        engine.set_state(name)
