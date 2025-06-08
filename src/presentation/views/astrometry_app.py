import os
import threading
import tkinter as tk

from PIL import Image, ImageTk
from tkinter import ttk, messagebox
from src.infrastructure.utils.logger import Logger


class AstrometryApp:
    def __init__(self, root, controller):
        self.root = root
        self.root.title("Определение местонахождения космического объекта")
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

        default_font = ttk.Style().lookup("TButton", "font") or "TkDefaultFont"

        self.status_text = tk.Text(
            frame,
            height=3,
            width=50,
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            padx=0,
            pady=0,
            font=default_font
        )
        self.status_text.pack(padx=3, pady=3)
        self.status_text.tag_config("green", foreground="green", justify="center")
        self.status_text.tag_config("black", foreground="black", justify="center")
        self.status_text.tag_config("blue", foreground="blue", justify="center")
        self.status_text.tag_config("red", foreground="red", justify="center")
        self.status_text.tag_config("orange", foreground="orange", justify="center")
        self.status_text.insert("1.0", "Статус: —", "black")
        self.status_text.config(state="disabled")

        self.status_text.configure(background=self.root.cget("background"))

        self.image_frame = ttk.Frame(frame)

        self.canvas = tk.Canvas(self.image_frame, width=600, height=600,
                                highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(side=tk.TOP)

        self.zoom_frame = ttk.Frame(self.image_frame)
        self.zoom_frame.pack(pady=2)

        self.btn_zoom_out = ttk.Button(self.zoom_frame, text="–", width=3, command=self.zoom_out)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=2)

        self.zoom_label = ttk.Label(self.zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)

        self.btn_zoom_in = ttk.Button(self.zoom_frame, text="+", width=3, command=self.zoom_in)
        self.btn_zoom_in.pack(side=tk.LEFT, padx=2)

        self.btn_zoom_reset = ttk.Button(self.zoom_frame, text="Сброс", command=self.zoom_reset)
        self.btn_zoom_reset.pack(side=tk.LEFT, padx=2)

        self.original_image = None
        self.displayed_image = None
        self.zoom_level = 100
        self.canvas_image_id = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.image_position = [0, 0]

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.mouse_wheel(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self.mouse_wheel(e, -1))

    def _build_info_tab(self, frame):
        info_text = (
            "Данная программа предназначеня для выполнения определение местоположения неизвестного космического объекта по снимку звёздного неба.\n\n"
            "Инструкция по работе:\n\n"
            "Шаг 1. Для работы загрузите астрономический снимок в поддерживаемом формате.\n\n"
            "Шаг 2. Нажмите кнопку обработки.\n\n"
            "Шаг 3. Программа выполнит астрономическую калибровку и поиск неизвестных объектов.\n\n"
            "Шаг 4. Результат работы программы - координаты объектов и изображение с выделенными объектами."
        )

        text_widget = tk.Text(
            frame,
            height=5,
            width=50,
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            padx=0,
            pady=0,
            font=ttk.Style().lookup("TButton", "font") or "TkDefaultFont"
        )
        text_widget.configure(background=self.root.cget("background"))
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

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event):
        if not self.canvas_image_id:
            return

        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        self.image_position[0] += dx
        self.image_position[1] += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.canvas.move(self.canvas_image_id, dx, dy)

    def mouse_wheel(self, event, delta=None):
        if not self.original_image:
            return

        if delta is None:
            delta = 1 if event.delta > 0 else -1

        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        if self.original_image and self.zoom_level < 300:
            self.zoom_level += 20
            self._update_image_with_zoom()

    def zoom_out(self):
        if self.original_image and self.zoom_level > 20:
            self.zoom_level -= 20
            self._update_image_with_zoom()

    def zoom_reset(self):
        if self.original_image:
            self.zoom_level = 100
            self.image_position = [0, 0]
            self._update_image_with_zoom()

    def _update_image_with_zoom(self):
        if not self.original_image:
            return

        self.zoom_label.config(text=f"{self.zoom_level}%")

        width = int(self.original_image.width * self.zoom_level / 100)
        height = int(self.original_image.height * self.zoom_level / 100)

        resized_img = self.original_image.resize((width, height), Image.LANCZOS)

        self.displayed_image = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")

        if self.zoom_level == 100 and self.image_position == [0, 0]:
            x = max(0, (self.canvas.winfo_width() - width) // 2)
            y = max(0, (self.canvas.winfo_height() - height) // 2)
            self.image_position = [x, y]

        self.canvas_image_id = self.canvas.create_image(
            self.image_position[0], self.image_position[1],
            image=self.displayed_image, anchor="nw"
        )

    def _show_image(self, image_path):
        try:
            self.original_image = Image.open(image_path)

            if not self.image_frame.winfo_ismapped():
                self.image_frame.pack(pady=3)

            self.zoom_level = 100
            self.image_position = [0, 0]

            canvas_width = min(600, self.original_image.width)
            canvas_height = min(600, self.original_image.height)
            self.canvas.config(width=canvas_width, height=canvas_height)

            self._update_image_with_zoom()
        except Exception as e:
            self.logger.error("AstrometryApp", f"Image display error: {str(e)}")