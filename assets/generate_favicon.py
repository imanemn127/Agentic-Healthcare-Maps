# assets/generate_favicon.py
from PIL import Image, ImageDraw
import os

OUT = os.path.join(os.path.dirname(__file__), "favicon.png")
img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Dessinez le tracé ECG en bleu marine (#1E4D7B) sur fond transparent
points = [
    (2, 32), (10, 32),           # ligne horizontale depuis la gauche
    (14, 32), (16, 10),          # montée
    (18, 10), (20, 50),          # descente profonde (pic QRS)
    (22, 50), (24, 32),          # remontée
    (28, 32), (62, 32)           # ligne horizontale jusqu'à droite
]
draw.line(points, fill="#1E4D7B", width=4, joint="curve")
img.save(OUT, "PNG")
print(f"Favicon créé : {OUT}")