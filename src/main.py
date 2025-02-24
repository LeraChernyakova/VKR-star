from src.ImageProcessing.StarDetector import StarDetector

if __name__ == "__main__":
    detector = StarDetector()
    image, corners = detector.detect_stars("../images/star.jpg")
    detector.draw_detections(image, corners)