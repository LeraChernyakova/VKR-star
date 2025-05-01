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

        self.status_text = tk.Text(frame, height=5, width=50, wrap="word")
        self.status_text.pack(padx=10, pady=10)
        self.status_text.tag_config("green", foreground="green")
        self.status_text.tag_config("black", foreground="black")
        self.status_text.tag_config("blue", foreground="blue")
        self.status_text.tag_config("red", foreground="red")
        self.status_text.tag_config("orange", foreground="orange")
        self.status_text.insert("1.0", "Статус: —", "black")
        self.status_text.config(state="disabled")

        self.status_text.configure(background=self.root.cget("background"))

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

        self._update_status("В процессе...", "blue")
        threading.Thread(target=self._process_upload, daemon=True).start()

    def _process_upload(self):
        try:
            self._update_status("Начало обработки изображения...", "blue")

            result = self.controller.analyze_image(
                self.file_path,
                status_callback=self._update_status
            )

            if "error" in result:
                self._update_status(f"Ошибка: {result['error']}", "red")
                return

            self._display_results(result)

        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", "red")
            self.logger.error("AstrometryApp", f"Error while processing: {str(e)}")

    def _display_results(self, result):
        visualization_path = result.get("visualization_path")
        if visualization_path and os.path.exists(visualization_path):
            self._show_image(visualization_path)

            unknown_objects = result.get("truly_unknown_coords", [])

            text_parts = [
                ("Статус: Найдены неизвестные объекты на снимке", "green"),
                (f"\nКоличество объектов: {len(unknown_objects)} (выделены желтым)", "black")
            ]

            if unknown_objects:
                text_parts.append(("\nКоординаты объектов:", "black"))
                for i, obj in enumerate(unknown_objects):
                    text_parts.append((f"\n{i + 1}. RA={obj.get('ra_str')}, Dec={obj.get('dec_str')}", "black"))

            self._update_formatted_status(text_parts)
        else:
            self._update_status("Обработка завершена, но изображение с результатами недоступно", "orange")

    def _update_formatted_status(self, text_parts):
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", "end")

        self.status_text.configure(
            background=self.root.cget("background"),
            borderwidth=0,
            highlightthickness=0,
            relief="flat"
        )

        for text, color in text_parts:
            self.status_text.insert("end", text, color)

        self.status_text.config(state="disabled")

    def _update_status(self, text, color="black"):
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", f"Статус: {text}", color)
        self.status_text.config(state="disabled")

    def _show_image(self, image_path):
        try:
            image = Image.open(image_path)
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            self.image_preview.configure(image=photo)
            self.image_preview.image = photo
        except Exception as e:
            self.logger.error(f"Image display error: {str(e)}")