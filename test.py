import pytesseract
from PIL import Image

# Set the Tesseract executable path if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Test with a sample image
image = Image.open('tooth_xray.jpg')  # Replace with an actual image file path
text = pytesseract.image_to_string(image)
print(text)
