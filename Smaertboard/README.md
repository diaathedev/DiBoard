# Smart Teaching Board (Desktop Application)

A distraction-free infinite whiteboard and document presenter for teachers, smart boards, and interactive displays.

## Quick Start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```
   *(You can also run directly with: `python smart_teaching_board/main.py`)*

## Key Features & Controls
- **Toolbar Toggle (Arrow Button)**: Click the **◀** arrow button at the top of the toolbar or press **T** on the keyboard to minimize/hide the toolbar for a completely unobstructed view. Click **▶** to expand it back anytime.
- **Pen Tool**: Smooth anti-aliased drawing over empty board, imported PDFs, images, and slides.
- **Eraser Tool**: Geometrical erasing that strictly erases pen strokes and never deletes your documents or images.
- **Move Tool**: Drag to pan across the infinite canvas. Zoom centered around cursor with mouse wheel.
- **Edit Tool**: Bounding box selection, resize handles, bring forward, send backward, and delete.
- **Fullscreen Mode**: Press **F11** or click Fullscreen in the top bar.
