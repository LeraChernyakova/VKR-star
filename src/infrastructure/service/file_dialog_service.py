import os
import tkinter as tk

from tkinter import filedialog
from src.infrastructure.utils.logger import Logger
from src.domain.interfaces.file_selection_service import IFileSelectionService


class FileDialogService(IFileSelectionService):
    def __init__(self):
        self.service_name = "FileDialogService"
        self.logger = Logger()

    def select_image(self):
        root = tk.Tk()
        root.withdraw()

        image_path = filedialog.askopenfilename(
            title="Выберите изображение для обработки",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )

        if image_path and os.path.isfile(image_path):
            return image_path
        else:
            self.logger.warning(self.service_name,"No file selected or file does not exist")
            return None