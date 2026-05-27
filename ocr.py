import easyocr
import numpy as np

# Initialize the EasyOCR reader
# For Japanese, you can pass ['ja', 'en']
# We initialize it lazily or globally
_reader = None

def get_reader(lang_list=['ja', 'en']):
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(lang_list, gpu=True) # use gpu=False if no CUDA
    return _reader

def extract_dialogue(image_pil, lang_list=['ja', 'en']):
    """
    Extracts text from the image using EasyOCR.
    Finds the largest text bounding box to likely be the dialogue box.
    Returns the bounding box and the text.
    """
    reader = get_reader(lang_list)
    image_np = np.array(image_pil)
    
    # Do OCR
    results = reader.readtext(image_np,paragraph=True)
    
    if not results:
        return None, None
    
    # Results format: [(bounding_box, text, confidence), ...]
    # bounding box: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
    
    # Heuristic: Find the text with the largest area, or simply the one with highest confidence,
    # or the lowest position on the screen (since dialog is usually at the bottom).
    # Here, we look for the text box with the largest area as requested ("biggest segmentation").
    
    largest_area = 0
    best_text = ""
    best_bbox = None
    
    for bbox, text in results:
        # Calculate area of bounding box
        x_coords = [int(point[0]) for point in bbox]
        y_coords = [int(point[1]) for point in bbox]
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        area = width * height
        
        if area > largest_area:
            largest_area = area
            best_text = text
            best_bbox = bbox
            
    # For bounding box, return (left, top, width, height)
    if best_bbox:
        x_coords = [int(point[0]) for point in best_bbox]
        y_coords = [int(point[1]) for point in best_bbox]
        x_min = int(min(x_coords))
        y_min = int(min(y_coords))
        w = int(max(x_coords) - min(x_coords))
        h = int(max(y_coords) - min(y_coords))
        
        return (x_min, y_min, w, h), best_text
        
    return None, None

def extract_all_text(image_pil, lang_list=['ja', 'en']):
    """
    Extracts all text from the image using EasyOCR and concatenates them with newlines.
    """
    reader = get_reader(lang_list)
    image_np = np.array(image_pil)
    results = reader.readtext(image_np, paragraph=True)
    if not results:
        return ""
    return "\n".join([text for _, text in results])
