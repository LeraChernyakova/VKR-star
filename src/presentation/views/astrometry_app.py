import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from PIL import Image, ImageTk
from src.infrastructure.utils.logger import Logger


class AstrometryApp:
    def __init__(self, root, controller):
        self.root = root
        self.root.title("Определение местоположения космического объекта")
        self.controller = controller
        self.file_path = None
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

        ttk.Label(frame, text="Загрузка изображения", font=("Arial", 12)).pack(**padding)

        self.btn_choose = ttk.Button(frame, text="Выбрать файл", command=self.choose_file)
        self.btn_choose.pack(**padding)

        self.label_filename = ttk.Label(frame, text="Файл не выбран", foreground="gray")
        self.label_filename.pack(**padding)

        ttk.Label(frame, text="Поддерживаемые форматы: JPEG, PNG", foreground="black").pack(**padding)

        self.btn_upload = ttk.Button(frame, text="Обработать", command=self.upload_file)
        self.btn_upload.pack(**padding)

        self.label_status = ttk.Label(frame, text="Статус: —", foreground="black")
        self.label_status.pack(**padding)

        self.image_preview = tk.Label(frame)
        self.image_preview.pack(pady=10)

    def _build_info_tab(self, frame):
        info_text = (
            "Эта программа выполняет определение местоположения космического объекта.\n\n"
            "Для работы загрузите астрономический снимок в поддерживаемом формате.\n"
            "Программа выполнит астрометрическую калибровку и поиск объектов, после чего\n"
            "определит неизвестные (не присутствующие в астрономических каталогах) объекты."
        )

        text_widget = tk.Text(frame, wrap="word", bg=self.root.cget("bg"), borderwidth=0)
        text_widget.insert("1.0", info_text)
        text_widget.config(state="disabled")
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)

    def choose_file(self):
        self.file_path = self.controller.select_image()

        if self.file_path:
            filename = os.path.basename(self.file_path)
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
            self._update_status("Начало обработки изображения...", "blue")

            result = self.controller.analyze_image(self.file_path)

            if "error" in result:
                self._update_status(f"Ошибка: {result['error']}", "red")
                return

            self._display_results(result)

        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", "red")
            self.logger.error(f"Ошибка при обработке: {str(e)}")

    def _display_results(self, result):
        visualization_path = result.get("visualization_path")
        if visualization_path and os.path.exists(visualization_path):
            self._show_image(visualization_path)

            unknown_objects = result.get("truly_unknown_coords", [])

            count_message = f"Неизвестные объекты: {len(unknown_objects)} (выделены желтым)"

            if unknown_objects:
                coord_details = "\nКоординаты объектов:"
                for i, obj in enumerate(unknown_objects[:3]):
                    coord_details += f"\n{i + 1}. RA={obj.get('ra'):.5f}, Dec={obj.get('dec'):.5f}"

                if len(unknown_objects) > 3:
                    coord_details += f"\n... и еще {len(unknown_objects) - 3} объект(ов)"

                self._update_status(f"{count_message}{coord_details}", "black")
            else:
                self._update_status(count_message, "black")
        else:
            self._update_status("Обработка завершена, но изображение с результатами недоступно", "orange")

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
            self.logger.error(f"Ошибка отображения изображения: {str(e)}")