#!/usr/bin/env python3
"""
NEXUS Vision Module — Screenshot + OCR + Image Analysis
Uses: Pillow, Tesseract OCR, OpenAI CLIP (optional)
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

NEXUS_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = NEXUS_ROOT / "data" / "screenshots"


class NexusVision:
    """NEXUS Vision Engine — see and understand"""

    def __init__(self):
        self._tesseract_path = None
        self._find_tesseract()

    def _find_tesseract(self):
        """Auto-detect Tesseract installation"""
        possible = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
        ]
        for p in possible:
            if os.path.exists(p):
                self._tesseract_path = p
                return
        # Try PATH
        import shutil
        t = shutil.which("tesseract")
        if t:
            self._tesseract_path = t

    # === Screenshot ===

    def _cleanup_old_screenshots(self, max_age_days: int = 7):
        """Delete screenshots older than max_age_days to save disk space."""
        try:
            import time as _time
            cutoff = _time.time() - (max_age_days * 86400)
            removed = 0
            if SCREENSHOTS_DIR.exists():
                for f in SCREENSHOTS_DIR.glob("screen_*.png"):
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                        removed += 1
            if removed:
                print(f"[VISION] Auto-cleaned {removed} old screenshot(s)")
        except Exception:
            pass  # non-critical

    def take_screenshot(self, region: tuple = None) -> dict:
        """Take screenshot of full screen or region (x, y, w, h)"""
        try:
            from PIL import ImageGrab
        except ImportError:
            return {"error": "Pillow not installed. Run: pip install Pillow"}

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = SCREENSHOTS_DIR / f"screen_{timestamp}.png"

        try:
            if region:
                img = ImageGrab.grab(bbox=region)
            else:
                img = ImageGrab.grab()
            img.save(str(filepath))
            self._cleanup_old_screenshots()  # auto-cleanup
            return {
                "status": "captured",
                "path": str(filepath),
                "size": f"{img.size[0]}x{img.size[1]}",
            }
        except Exception as e:
            return {"error": f"Screenshot failed: {e}"}

    # === OCR (Tesseract) ===

    def read_image(self, image_path: str) -> dict:
        """Read text from image using OCR"""
        if not self._tesseract_path:
            return {"error": "Tesseract not installed. Download from: https://github.com/tesseract-ocr/tesseract"}

        try:
            from PIL import Image
        except ImportError:
            return {"error": "Pillow not installed. Run: pip install Pillow"}

        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_path
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return {
                "text": text.strip(),
                "size": f"{img.size[0]}x{img.size[1]}",
                "path": image_path,
            }
        except Exception as e:
            return {"error": f"OCR failed: {e}"}

    def read_screenshot(self) -> dict:
        """Take screenshot and read text from it"""
        result = self.take_screenshot()
        if "error" in result:
            return result
        return self.read_image(result["path"])

    def read_region(self, x: int, y: int, w: int, h: int) -> dict:
        """Take screenshot of region and read text"""
        result = self.take_screenshot(region=(x, y, w, h))
        if "error" in result:
            return result
        return self.read_image(result["path"])

    # === Image Analysis ===

    def analyze_image(self, image_path: str) -> dict:
        """Analyze image — get colors, objects, metadata"""
        try:
            from PIL import Image
        except ImportError:
            return {"error": "Pillow not installed"}

        try:
            img = Image.open(image_path)
            info = {
                "path": image_path,
                "size": f"{img.size[0]}x{img.size[1]}",
                "mode": img.mode,
                "format": img.format,
            }

            # Get dominant colors
            try:
                small = img.copy()
                small.thumbnail((50, 50))
                colors = small.getcolors(maxcolors=10000)
                if colors:
                    colors.sort(key=lambda x: x[0], reverse=True)
                    info["dominant_colors"] = len(colors)
            except Exception:
                pass

            # Get EXIF data
            try:
                exif = img._getexif()
                if exif:
                    info["has_exif"] = True
                    info["exif_tags"] = len(exif)
            except Exception:
                info["has_exif"] = False

            return info
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}

    def find_text_on_screen(self, search_text: str) -> dict:
        """Take screenshot, OCR it, search for specific text"""
        result = self.read_screenshot()
        if "error" in result:
            return result

        text = result.get("text", "")
        found = search_text.lower() in text.lower()
        return {
            "found": found,
            "searched": search_text,
            "screenshot_text": text[:500],
            "path": result.get("path"),
        }

    # === Status ===

    def get_status(self) -> dict:
        return {
            "tesseract": self._tesseract_path or "not found",
            "screenshots_dir": str(SCREENSHOTS_DIR),
            "screenshots_count": len(list(SCREENSHOTS_DIR.glob("*.png"))) if SCREENSHOTS_DIR.exists() else 0,
        }


# Singleton
_vision = None


def get_vision() -> NexusVision:
    global _vision
    if _vision is None:
        _vision = NexusVision()
    return _vision


if __name__ == "__main__":
    vision = get_vision()
    print("=== NEXUS Vision Module ===")
    print(f"Status: {json.dumps(vision.get_status(), indent=2)}")
