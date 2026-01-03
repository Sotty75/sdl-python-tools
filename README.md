# SOT Sprite Editor

**SOT Sprite Editor** is a lightweight, Python-based visual tool designed for Game Developers. It simplifies the process of creating texture atlases and defining animation cycles for 2D game engines.

Instead of manually calculating pixel coordinates, you can visually draw, tag, and organize your sprite frames, then export a clean, engine-ready JSON file containing all metadata.

## 🚀 Key Features

* **Visual Editor:** Load any `.png` or `.jpg` sprite sheet and draw collision/animation quads directly on top of it.
* **Tagging System:** Organize frames into named animations (e.g., "Idle", "Run", "Attack").
* **Color Coding:** Automatically assigns unique colors to different tags for easy visual distinction.
* **Smart Selection:**
    * **Click** to select.
    * **Shift + Click** for multi-selection.
    * **Drag & Drop** to move frames (with auto-clamping to image bounds).
* **Strip Cloner:** Instantly generate rows of animation frames with automatic wrapping and customizable offsets.
* **Precise Inspector:** Manually edit coordinates (`X`, `Y`, `W`, `H`) for pixel-perfect precision.
* **Duplicate Prevention:** Intelligent logic prevents creating duplicate or overlapping frames.
* **JSON Import/Export:**
    * Exports a compact, human-readable JSON file.
    * Includes metadata: Atlas Name, Image Path, Frame Counts.
    * Supports importing existing JSON files to resume work.

## 🛠️ Installation

No complex installation is required. You only need **Python 3.x** installed on your system.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/sot-sprite-editor.git](https://github.com/your-username/sot-sprite-editor.git)
   cd sot-sprite-editor
   ```
   
2. **Run the application:**

     ```bash
        # Windows
        python atlas_tool.py
        # Mac/Linux
        python3 atlas_tool.py
     ```

Dependencies: This tool uses only standard Python libraries (tkinter, json, random, os), so no pip install is needed!

## How To Use

1. Load an Atlas
Click Load Image to open your sprite sheet (PNG/JPG). Use Zoom + / - to get a better view of pixel art.

2. Create Frames
Stamp Mode: Input your desired Width/Height in the Inspector (default 16x16). Click anywhere on the image to "stamp" a new frame.
Strip Cloning: Select a frame, set the Count in the "Strip Cloner" panel, and click Clone Strip. The tool will automatically generate the next frames in the sequence.

3. Organize & Tag
Rename Tag: Select a tag in the right-hand list and click Rename.
Colorize: Click Pick Color to assign a custom color to a specific animation tag.
Move Selection: Select multiple frames (Shift+Click) and click Move Selection to Tag... to reassign them to a different animation.

4. Export
Click Export JSON. The tool generates a file compatible with C/C++ game engines (and others).

Output Example:
```JSON
{
    "atlas_name": "hero_sheet",
    "image_path": "C:/gamedev/assets/hero.png",
    "animations": {
        "Idle": {
            "frame_count": 2,
            "frames": [
                { "x": 0, "y": 0, "w": 32, "h": 32 },
                { "x": 32, "y": 0, "w": 32, "h": 32 }
            ]
        },
        "Run": {
            "frame_count": 4,
            "frames": [
                { "x": 0, "y": 32, "w": 32, "h": 32 },
                { "x": 32, "y": 32, "w": 32, "h": 32 },
                { "x": 64, "y": 32, "w": 32, "h": 32 },
                { "x": 96, "y": 32, "w": 32, "h": 32 }
            ]
        }
    }
}
```

## 4. Shortcuts
- Delete / Backspace: Delete selected frame(s).
- Shift + Click: Add/Remove frame from selection.
- Drag Mouse: Move selected frames.

## 5. Contributing
Feel free to fork this project and submit Pull Requests. Suggestions for new features (like auto-slicing or GIF preview) are welcome!

📄 License
This project is open-source and available under the MIT License.
