import os
import tkinter as tk
from tkinter import filedialog
from src.domain.interfaces.file_selection_service import IFileSelectionService
from src.infrastructure.utils.logger import Logger


class FileDialogService(IFileSelectionService):
    def __init__(self):
        self.service_name = "FileDialogService"
        self.logger = Logger()

    def select_image(self):
        root = tk.Tk()
        root.withdraw()

        self.logger.info(self.service_name,"Opening file dialog for image selection")
        image_path = filedialog.askopenfilename(
            title="Выберите изображение для обработки",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )

        if image_path and os.path.isfile(image_path):
            self.logger.info(self.service_name,f"Selected image: {image_path}")
            return image_path
        else:
            self.logger.warning(self.service_name,"No file selected or file does not exist")
            return None