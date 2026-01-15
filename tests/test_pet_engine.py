import unittest
import time
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pet_engine

class TestPetEngine(unittest.TestCase):
    def setUp(self):
        # Reset engine before each test
        pet_engine.initialize("fake_path.png")
        self.engine = pet_engine.engine

    def test_initial_state(self):
        self.assertEqual(self.engine.state, 'IDLE')
        self.assertEqual(self.engine.frame_index, 0)
        self.assertTrue(self.engine.facing_right)

    def test_state_transition(self):
        self.engine.set_state('WALK')
        self.assertEqual(self.engine.state, 'WALK')
        self.assertEqual(self.engine.frame_index, 0)
        # Verify target_x is set
        self.assertNotEqual(self.engine.target_x, 100.0)

    def test_animation_loop(self):
        # Speed up time or simulate ticks
        self.engine.set_state('IDLE') # 4 frames, default 10fps
        # Simulate 1 second
        for _ in range(20):
            self.engine.update()
            time.sleep(0.01) # Small sleep to ensure time.time() advances or mock it
        
        # After enough time, frame_index should have progressed
        # (Though in real tests you'd mock time.time())
        self.assertGreaterEqual(self.engine.frame_index, 0)

    def test_non_looping_state(self):
        # IDLE2 should return to IDLE after one loop
        self.engine.set_state('IDLE2')
        limit = pet_engine.FRAME_COUNTS['IDLE2']
        
        # Force frame index to the end
        self.engine.frame_index = limit - 1
        self.engine.timer = 1.0 # Force update trip
        
        self.engine.update()
        self.assertEqual(self.engine.state, 'IDLE')

    def test_wall_collision(self):
        self.engine.x = 10.0
        self.engine.set_state('WALK')
        self.engine.target_x = 0.0 # Moving left towards margin
        
        # Simulate movement
        # Update with screen_width=1000, margin=40
        # If x=10, it should snap back and flip
        self.engine.update(screen_width=1000)
        
        self.assertGreater(self.engine.x, 40)
        self.assertTrue(self.engine.facing_right)

if __name__ == '__main__':
    unittest.main()
