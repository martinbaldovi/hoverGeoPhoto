# hoverGeoPhoto Plugin for QGIS 4.0

Displays a photo when hovering over a point feature that contains a valid image link (local path or URL). The popup is elegant, non‑obstructive, and adapts to the workspace.

## How to install

1. Download the source code as a ZIP archive.
2. Uncompress the ZIP file.
3. Move the extracted `hoverGeoPhoto` parent folder to the QGIS 4 plugins directory (create folders if they don't exist):  
   `%APPDATA%\QGIS\QGIS4\profiles\default\python\plugins`

> **Note:** A point layer with a photo attribute (local file path or http:// / https:// URL) is required.

## How to use

1. Load a point vector layer in QGIS 4.0.
2. Enable **hoverGeoPhoto** from the **Plugin Manager**.
3. A toolbar button **📷 hoverGeoPhoto** appears. Click it to open the settings dialog.
4. In the dialog:
   - **Check** “Enable hover preview”.
   - **Select** the point layer you want to monitor.
   - **Choose** the attribute field that stores the photo link.
5. Click **OK** – the toolbar button stays pressed (enabled) when hover preview is active.
6. Hover your mouse over any point feature in the chosen layer.  
   A beautiful popup will show the photo (loading indicator for remote images).

## Notes

- Local file paths can be absolute or relative to the current QGIS project file.
- Remote images (http:// or https://) are fetched asynchronously.
- The popup automatically positions itself near the cursor, stays inside the canvas, and hides when you stop hovering.
- Settings are saved between QGIS sessions.
