import mss
from PIL import Image

def capture_screen():
    """
    Captures the primary screen and returns it as a PIL Image.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 1 is the primary monitor
        sct_img = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img, monitor
