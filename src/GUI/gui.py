import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time

import numpy as np
from PIL import Image, ImageTk

from src.controllers.processing_controller import ProcessingController
from src.pipeline.astrometry_processor import AstrometryProcessor
from src.pipeline.catalog_verification_processor import CatalogVerificationProcessor
from src.pipeline.sextractor_processor import SExtractorProcessor
from src.pipeline.comparison_processor import ComparisonProcessor
from src.pipeline.image_processor import ImageProcessor
from src.utils.logger import Logger

class AstrometryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Определение местоположения космического объекта")
        self.api_key = "lyjwakywqahzzjvj"
        self.file_path = None
        self.image_processor = ImageProcessor()
        self.logger = Logger()
        self.controller = ProcessingController()

        self._build_ui()

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_main = ttk.Frame(self.notebook)
        self.tab_info = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_main, text="Обработка")
        self.notebook.add(self.tab_info, text="Информация")

        self._build_main_tab(self.tab_main)
        self._build_info_tab(self.tab_info)

    def _build_main_tab(self, frame):
        padding = {'padx': 10, 'pady': 10}

        ttk.Label(frame, text="Загрузка изображения для астрометрии", font=("Arial", 12)).pack(**padding)

        self.btn_choose = ttk.Button(frame, text="Выбрать файл", command=self.choose_file)
        self.btn_choose.pack(**padding)

        self.label_filename = ttk.Label(frame, text="Файл не выбран", foreground="gray")
        self.label_filename.pack(**padding)

        ttk.Label(frame, text="Поддерживаемые форматы: JPEG, PNG, FITS", foreground="black").pack(**padding)

        self.btn_upload = ttk.Button(frame, text="Загрузить", command=self.upload_file)
        self.btn_upload.pack(**padding)

        self.label_status = ttk.Label(frame, text="Статус: —", foreground="black")
        self.label_status.pack(**padding)

        self.image_preview = tk.Label(frame)
        self.image_preview.pack(pady=10)

    def _build_info_tab(self, frame):
        info_text = (
            "Эта программа выполняет определение местоположения космического объекта.\n\n"
            "В будущем здесь будет инструкция пользователя: как загружать изображения, "
            "какие форматы поддерживаются, как интерпретировать результат и т.д."
        )

        text_widget = tk.Text(frame, wrap="word", bg=self.root.cget("bg"), borderwidth=0)
        text_widget.insert("1.0", info_text)
        text_widget.config(state="disabled")
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)

    def choose_file(self):
        selected_path = self.image_processor.handle()

        if selected_path:
            self.file_path = selected_path
            filename = os.path.basename(selected_path)
            self.label_filename.config(text=f"Выбран: {filename}", foreground="black")
        else:
            self.label_filename.config(text="Файл не выбран", foreground="gray")

    def upload_file(self):
        if not self.file_path:
            messagebox.showwarning("Нет файла", "Пожалуйста, выберите файл.")
            return

        self.label_status.config(text="Статус: В процессе...", foreground="blue")
        threading.Thread(target=self._process_upload, daemon=True).start()

    def _process_upload(self):
        try:
            context = {"image_path": self.file_path}

            astrometry_processor = AstrometryProcessor(self.api_key)
            sextractor_processor = SExtractorProcessor()
            comparison_processor = ComparisonProcessor()
            catalog_verification_processor = CatalogVerificationProcessor()

            self._update_status("Запуск параллельной обработки...", "blue")

            # First run astrometry and sextractor in parallel
            result = self.controller.run_parallel_processing(
                context,
                astrometry_processor,
                sextractor_processor,
                comparison_processor
            )

            # Then verify the unique objects against catalogs
            self._update_status("Проверка объектов по астрономическим каталогам...", "blue")
            catalog_verification_processor.handle(result)

            self._display_results(result)

        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", "red")
            self.logger.error(f"Error in processing upload: {str(e)}")

    def _display_results(self, result):
        """Display the processing results"""
        # Show all Astrometry.net objects
        all_objects_path = result.get("all_objects_path")
        if all_objects_path and os.path.exists(all_objects_path):
            self._show_image(all_objects_path)
            field_center = result.get("field_center", {})
            field_info = f"Field center: RA={field_center.get('ra_formatted', 'Unknown')}, Dec={field_center.get('dec_formatted', 'Unknown')}"
            self._update_status(f"Astrometry.net: все обнаруженные объекты (синим)\n{field_info}", "blue")
            time.sleep(2)

        # Show all SExtractor objects
        sep_all_objects_path = result.get("sep_all_objects_path")
        if sep_all_objects_path and os.path.exists(sep_all_objects_path):
            self._show_image(sep_all_objects_path)
            sep_count = len(result.get("sep_pixel_coords", []))
            self._update_status(f"SExtractor: найдено {sep_count} объектов (фиолетовым)", "purple")
            time.sleep(2)

        # Show unknown objects from astrometry
        highlighted_path = result.get("highlighted_path")
        if highlighted_path and os.path.exists(highlighted_path):
            self._show_image(highlighted_path)
            unknown_count = result.get("unknown_count", 0)
            total_objects = result.get("total_objects", 0)
            self._update_status(f"Astrometry: {unknown_count} неизвестных из {total_objects} (красным)", "red")
            time.sleep(2)

        # Show objects unique to SExtractor
        unique_objects_path = result.get("unique_objects_path")
        if unique_objects_path and os.path.exists(unique_objects_path):
            self._show_image(unique_objects_path)
            unique_count = len(result.get("unique_sep_objects", []))
            self._update_status(f"Объекты только в SExtractor: {unique_count} (зеленым)", "green")
            time.sleep(2)

        # Show truly unknown objects (not in any catalog)
        truly_unknown_path = result.get("truly_unknown_path")
        if truly_unknown_path and os.path.exists(truly_unknown_path):
            self._show_image(truly_unknown_path)

            # Get coordinates for unknown objects
            truly_unknown_coords = result.get("truly_unknown_coords", [])

            # Show number of unknown objects
            count_message = f"Действительно неизвестные объекты: {len(truly_unknown_coords)} (желтым)"

            # Add coordinate details if objects exist
            if truly_unknown_coords:
                coord_details = "\nКоординаты объектов:"
                for i, obj in enumerate(truly_unknown_coords[:3]):  # Show up to 3 objects
                    coord_details += f"\n{i + 1}. RA={obj['ra_formatted']}, Dec={obj['dec_formatted']}"

                if len(truly_unknown_coords) > 3:
                    coord_details += f"\n... и еще {len(truly_unknown_coords) - 3} объект(ов)"

                self._update_status(f"{count_message}{coord_details}", "black")
            else:
                self._update_status(count_message, "black")

    def _update_status(self, text, color):
        self.label_status.config(text=f"Статус: {text}", foreground=color)

    def _show_image(self, image_path):
        try:
            image = Image.open(image_path)
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            self.image_preview.configure(image=photo)
            self.image_preview.image = photo
        except Exception as e:
            print(f"Ошибка отображения изображения: {e}")