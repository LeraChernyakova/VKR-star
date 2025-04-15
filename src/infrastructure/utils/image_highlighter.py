from PIL import Image, ImageDraw

class ImageHighlighter:
    def __init__(self, image_path):
        self.image = Image.open(image_path).convert("RGB")
        self.draw = ImageDraw.Draw(self.image)

    def highlight_points(self, points, radius=10, color="red"):
        for x, y in points:
            bbox = [x - radius, y - radius, x + radius, y + radius]
            self.draw.ellipse(bbox, outline=color, width=2)

    def save(self, output_path):
        self.image.save(output_path)
