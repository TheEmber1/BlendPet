
import random
import time

# -- Constants --
SLICE_SIZE = 32
SCALE = 4.0 # How big on screen
FPS = 10
FRAME_TIME = 1.0 / FPS

# Animation Row Mapping (Source: User Request)
# "Top: Idle. Second: Idle2. Third: Lick. Fourth: Clean. Fith: Walk. Sixth: Run. Seventh: Sleep. Eighth: Play. Nineth: Pounce. Tenth: LookBehind."
# 0-indexed rows
ANIM_ROWS = {
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
FRAME_COUNTS = {
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
# Default if missing
DEFAULT_FRAME_COUNT = 4

# Custom FPS per state (Default 10)
STATE_FPS = {
    'LOOK_BEHIND': 5, # Slower
    'SLEEP': 2, # Very slow breathing
}

class PetEngine:
    def __init__(self, sprite_path):
        self.sprite_path = sprite_path
        self.x = 100.0 # Screen coordinates (bottom left origin?)
        self.y = 100.0
        
        self.state = 'IDLE'
        self.row = ANIM_ROWS['IDLE']
        self.frame_index = 0
        
        self.facing_right = True # User said "All of them are facing right."
        
        self.timer = 0.0
        self.last_tick = time.time()
        
        self.state_timer = 0.0
        self.state_duration = 5.0 # Slower updates
        
        self.target_x = 100.0
        self.target_y = 100.0
        self.speed = 2.0
        
        # Energy System (0-100)
        self.energy = 100.0

    def set_state(self, new_state):
        if new_state not in ANIM_ROWS:
            print(f"Unknown state: {new_state}")
            return
            
        self.state = new_state
        self.row = ANIM_ROWS[new_state]
        self.frame_index = 0
        self.state_timer = 0.0
        
        # Duration Logic
        if self.state == 'SLEEP':
            # Sleep for a long time
            self.state_duration = random.uniform(20.0, 40.0)
        elif self.state in ['LOOK_BEHIND', 'IDLE2', 'PLAY', 'POUNCE']:
            # Short actions
            self.state_duration = 3.0 
        else:
            # Idle/Move duration
            self.state_duration = random.uniform(5.0, 10.0)
        
        # State init logic
        if self.state in ['WALK', 'RUN']:
            # Pick a target (will be clamped in update)
            self.target_x = random.uniform(100, 1000) 
            self.facing_right = self.target_x > self.x
            
    def update(self, screen_width=None):
        # Update Timer
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now
        
        self.timer += dt
        self.state_timer += dt
        
        # -- Animation Loop --
        target_fps = STATE_FPS.get(self.state, FPS)
        frame_time = 1.0 / target_fps
        
        limit = FRAME_COUNTS.get(self.state, DEFAULT_FRAME_COUNT)
        if self.timer >= frame_time:
            # Check for non-looping states (Play once then Idle)
            if self.state in ['LOOK_BEHIND', 'PLAY', 'POUNCE', 'IDLE2']:
                 if self.frame_index >= limit - 1:
                     self.set_state('IDLE')
                     return 
            
            self.frame_index = (self.frame_index + 1) % limit
            self.timer = 0.0
            
        # -- Movement --
        moved = False
        if self.state == 'WALK':
            dx = self.target_x - self.x
            step = 1.5 * (dt * 60) # Slower (1.5px per frame @ 60hz)
            
            if abs(dx) < step:
                self.x = self.target_x
                self.set_state('IDLE')
            else:
                self.x += step if dx > 0 else -step
                moved = True
                
        elif self.state == 'RUN':
             dx = self.target_x - self.x
             step = 4.0 * (dt * 60) # Slower (4.0px per frame)
             
             if abs(dx) < step:
                 self.x = self.target_x
                 self.set_state('IDLE')
             else:
                 self.x += step if dx > 0 else -step
                 moved = True
        
        # -- Wall Collision --
        if screen_width and moved:
             margin = 40
             if self.x <= margin:
                 self.x = margin + 1.0
                 self.facing_right = True # Turn back
                 self.target_x = random.uniform(self.x + 100, screen_width - margin)
                 
             elif self.x >= screen_width - margin:
                 self.x = screen_width - margin - 1.0
                 self.facing_right = False # Turn back
                 self.target_x = random.uniform(margin, self.x - 100)

        # -- State Transitions --
        
        # Time based switch
        if self.state_timer > self.state_duration:
            self.pick_new_state()

    def pick_new_state(self):
        # Logical Chains
        
        # If was Sleeping -> Stretch
        if self.state == 'SLEEP':
            self.set_state('IDLE2')
            return
            
        # If was Stretching -> Walk or Idle
        if self.state == 'IDLE2':
            choices = ['IDLE', 'WALK']
            weights = [0.5,    0.5]
            self.set_state(random.choices(choices, weights=weights, k=1)[0])
            return

        # General Random Logic
        choices = ['IDLE', 'IDLE2', 'SLEEP', 'LICK', 'WALK', 'RUN', 'LOOK_BEHIND', 'CLEAN', 'PLAY', 'POUNCE']
        # Weights: Idle is extremely likely. Sleep is rare but sticky. High energy rare.
        weights = [0.35,   0.05,    0.1,     0.1,    0.25,   0.05,  0.02,           0.05,    0.02,   0.01]
        
        next_state = random.choices(choices, weights=weights, k=1)[0]
        self.set_state(next_state)

# -- Singleton Instance --
engine = None

def initialize(sprite_path):
    global engine
    engine = PetEngine(sprite_path)
    engine.set_state('IDLE')

def update(screen_width=None):
    """Called by modal operator"""
    if engine:
        engine.update(screen_width)

def get_render_data():
    """Returns (x, y, row, frame, facing_right) for the renderer"""
    if engine:
        return (engine.x, engine.y, engine.row, engine.frame_index, engine.facing_right)
    return None

def set_state(name):
    if engine:
        engine.set_state(name)
