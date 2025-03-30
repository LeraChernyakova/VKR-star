import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from PIL import Image, ImageTk

from src.pipeline.astrometry_api_client import AstrometryAPIClient
from src.pipeline.image_processor import ImageProcessor
from src.pipeline.astrometry_calibrator import AstrometryCalibrator
from src.pipeline.object_classifier import ObjectClassifier
from src.utils.logger import Logger

class AstrometryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Определение местоположения космического объекта")
        self.api_key = "lyjwakywqahzzjvj"
        self.client = AstrometryAPIClient(self.api_key)
        self.file_path = None
        self.image_processor = ImageProcessor()
        self.logger = Logger()

        self.object_classifier = ObjectClassifier()
        self.astrometry_calibrator = AstrometryCalibrator(self.api_key, self.object_classifier)

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
            "🔭 Эта программа выполняет определение координат изображения звёздного неба.\n\n"
            "📝 В будущем здесь будет инструкция пользователя: как загружать изображения, "
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
            submission_id = self.client.upload_image(self.file_path)
            self._update_status("Файл загружен. Ожидание обработки...", "blue")

            job_id = self._wait_for_job(submission_id)
            if not job_id:
                self._update_status("Ошибка: обработка не завершилась", "red")
                return

            self._update_status("Загрузка результатов...", "blue")
            base_dir = os.path.dirname(self.file_path)
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]

            wcs_path = os.path.join(base_dir, f"{base_name}_wcs.fits")
            rdls_path = os.path.join(base_dir, f"{base_name}_rdls.rdls")

            self.client.download_result_file(job_id, "wcs_file", wcs_path)
            self.client.download_result_file(job_id, "rdls_file", rdls_path)

            context = {
                "image_path": self.file_path,
                "job_id": job_id,
                "wcs_path": wcs_path,
                "rdls_path": rdls_path
            }

            self._update_status("Анализ объектов...", "blue")
            result = self.object_classifier.handle(context)

            highlighted_path = result.get("highlighted_path")
            if highlighted_path and os.path.exists(highlighted_path):
                self._show_image(highlighted_path)
                unknown_count = result.get("unknown_count", 0)
                total_objects = result.get("total_objects", 0)
                self._update_status(f"Обнаружено {unknown_count} неизвестных объектов из {total_objects}", "green")
            else:
                self._update_status("Обработка завершена, но изображение недоступно", "orange")

        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", "red")
            self.logger.error(f"Error in processing upload: {str(e)}")

    def _wait_for_job(self, subid, timeout=300, interval=5):
        import time
        elapsed = 0
        while elapsed < timeout:
            status = self.client.get_submission_status(subid)
            jobs = status.get("jobs", [])
            for job_id in jobs:
                if job_id:
                    job_status = self.client.get_job_status(job_id)
                    if job_status.get("status") == "success":
                        return job_id
                    elif job_status.get("status") == "failure":
                        raise Exception("Обработка завершилась с ошибкой")
            time.sleep(interval)
            elapsed += interval
        return None

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