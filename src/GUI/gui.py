import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

from src.pipeline.astrometry_api_client import AstrometryAPIClient
from src.pipeline.image_processor import ImageProcessor
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
            if job_id:
                result = self.client.get_job_result(job_id)
                self._update_status("Готово", "green")
                print("Результат:", result)
            else:
                self._update_status("Ошибка: обработка не завершилась", "red")

        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", "red")

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