# BlendPet

![Demo 1](assets/demos/Demo%201.gif)

A completely useless (but kinda adorable) little pet that lives in your Blender animation editors.  
BlendPet adds a pixel-art cat — and maybe more pets later — that wanders around, sleeps, stretches, and generally distracts you while you’re trying to animate.

## Features
- **Animated pet** – A pixel cat with animations for walking, running, idling, licking, cleaning, playing, pouncing, stretching, and sleeping.
- **Animation Editor Overlay** – Lives in your Timeline, Dope Sheet, and Graph Editor.
- **Customizable** – Change its size to fit your workflow.
- **Non-intrusive** – It just hangs out. It won’t mess with your scene (just your focus 😉).

### Compatibility Matrix
| Blender Version | Status | Notes |
| :--- | :--- | :--- |
| **4.2.0+ LTS** | ✅ Supported | Primary target version. |
| **4.0.0+** | ⚠️ Limited | May work, but UI elements might shift. |
| **3.x and below** | ❌ Unsupported | Uses modern `gpu` module calls. |


## Installation
1. Download the latest release `.zip`.
2. Open Blender.
3. Go to `Edit > Preferences > Add-ons`.
4. Click **Install…** and select the zip file.
5. Enable **BlendPet** using the checkbox.

## How to use

1. **Summon the Pet**: Once enabled, look for the **Cat icon** in the top header of your 3D Viewport. Click it to bring the pet into your workspace.
2. **Where to find it**: The pet wanders along the bottom edge of your **Timeline**, **Dope Sheet**, or **Graph Editor**. If you don't see it, make sure one of these animation editors is open!
3. **Change its size**: If the cat is taking up too much (or too little) space, go to `Edit > Preferences > Add-ons > BlendPet` and adjust the **Pet Scale** slider.

## Troubleshooting

- **"Numpy not found" in Console**: The addon uses Numpy to upscale the pixel art for a sharper look. If it's missing, the cat will still appear but might look a bit blurry (linear filtering).
- **Pet not appearing**: Ensure you have a Timeline, Dope Sheet, or Graph Editor open. The pet only lives in these animation-focused windows.
- **Icon is a monkey**: If `icon.png` is missing from the `/textures` folder, Blender will fallback to the default Suzanne icon.


![Demo 2](assets/demos/Demo%202.gif)

## Contributing 

**Want to add to the project?**

I’m not amazing at coding 😅  
The addon works, but there’s definitely room to clean things up, optimize stuff, or just do things in a smarter way. If you know Python and bpy feel free to help improve it/add features.

- **Found a bug?** Open an issue and tell me what broke.
- **Want to improve the code?** Fork the repo. Most of the logic is in `pet_engine.py` (state machine) and `renderer.py` (drawing).
- **New feature idea?** Go for it. Code away and submit a PR.
- **Sprites?** If you’re a pixel artist and want to improve the cat (look in `textures/`) or add a dog 👀, open an issue or reach out.
- **Tests**: You can run `python3 tests/test_pet_engine.py` to verify logic changes without launching Blender.


