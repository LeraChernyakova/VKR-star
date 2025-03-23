from src.pipeline.processing_chain import ProcessingChain
from src.utils.logger import Logger
import tkinter as tk
from tkinter import filedialog
import os


class ImageProcessor(ProcessingChain):
    def __init__(self, next_processor=None):
        super().__init__(next_processor)
        self.logger = Logger()

    def handle(self, data=None):
        root = tk.Tk()
        root.withdraw()

        self.logger.info(f"Current log file: {self.logger.get_log_file_path()}")

        self.logger.info("Opening file dialog for image selection")
        image_path = filedialog.askopenfilename(
            title="Выберите изображение для обработки",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.tif *.tiff *.fits"),
                ("All files", "*.*")
            ]
        )

        if image_path and os.path.isfile(image_path):
            self.logger.info(f"Selected image: {image_path}")
            return image_path
        else:
            self.logger.warning("No file selected or file does not exist")
            return None