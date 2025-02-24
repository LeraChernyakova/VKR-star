import cv2
import numpy as np
from skimage.feature import corner_harris
from skimage.feature import corner_peaks
import matplotlib.pyplot as plt


class StarDetector:
    def __init__(self, min_distance=5):
        self.min_distance = min_distance

    def detect_stars(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        print(image)
        if image is None:
            raise ValueError("Error loading image")

        corners = corner_peaks(corner_harris(image), min_distance=self.min_distance)
        return image, corners

    def draw_detections(self, image, corners):
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(image, cmap='gray')
        for y, x in corners:
            c = plt.Circle((x, y), 3, color='red', linewidth=2, fill=False)
            ax.add_patch(c)
        plt.show()