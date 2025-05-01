import time
import os
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

from src.infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter
from src.infrastructure.adapters.celestial_catalog_adapter import CelestialCatalogAdapter
from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter

from src.infrastructure.service.parallel_processing_service import ParallelProcessingService
from src.infrastructure.service.object_comparison_service import ObjectComparisonService

from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase
from src.application.use_cases.verify_unknown_objects_use_case import VerifyUnknownObjectsUseCase
from src.application.use_cases.process_image_use_case import ProcessImageUseCase
from src.application.use_cases.detect_objects_use_case import DetectObjectsUseCase


class TestAnalyzer:
    def __init__(self, results_file):
        self.results_file = results_file

        # Инициализация компонентов
        api_key = "lyjwakywqahzzjvj"
        self.astrometry_service = AstrometryNetAdapter(api_key)
        self.catalog_service = CelestialCatalogAdapter()
        self.detection_service = SepDetectionAdapter()
        self.parallel_service = ParallelProcessingService()
        self.comparison_service = ObjectComparisonService()

        # Инициализация use cases
        self.calibrate_image_use_case = CalibrateImageUseCase(self.astrometry_service)
        self.detect_objects_use_case = DetectObjectsUseCase(self.detection_service)
        self.verify_objects_use_case = VerifyUnknownObjectsUseCase(self.catalog_service)
        self.process_image_use_case = ProcessImageUseCase(
            self.parallel_service,
            self.comparison_service
        )

    def process_image(self, image_path):
        # Этап 1: обработка изображения
        result = self.process_image_use_case.execute(
            image_path,
            self.calibrate_image_use_case,
            self.detect_objects_use_case
        )

        # Получение данных о найденных объектах
        sep_result = result.get("detection", {})
        astrometry_result = result.get("astrometry", {})

        sep_coords = sep_result.get("pixel_coords", [])
        astro_coords = astrometry_result.get("pixel_coords", [])
        wcs = astrometry_result.get("wcs")

        # Сохраняем количество найденных объектов
        detected_objects_count = len(sep_coords)

        # Начинаем отсчет времени
        start_time = time.time()

        # Находим уникальные объекты
        unique_coords = self.comparison_service.find_unique_objects(
            sep_coords, astro_coords, match_threshold=10
        )

        # Этап 2: проверка объектов
        verify = self.verify_objects_use_case.execute(
            image_path, unique_coords, wcs
        )

        # Заканчиваем отсчет времени
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Получаем количество неизвестных объектов
        unknown = verify.get("unknown_objects", [])
        unknown_count = len(unknown)

        # Записываем результаты
        with open(self.results_file, "a", encoding="utf-8") as f:
            f.write(f"Изображение: {os.path.basename(image_path)}\n")
            f.write(f"Объектов найдено SepDetectionAdapter: {detected_objects_count}\n")
            f.write(f"Неизвестных объектов: {unknown_count}\n")
            f.write(f"Время обработки: {elapsed_time:.4f} секунд\n")
            f.write("-" * 50 + "\n")

        return {
            "image": os.path.basename(image_path),
            "detected_objects": detected_objects_count,
            "unknown_objects": unknown_count,
            "processing_time": elapsed_time
        }


def main():
    parser = argparse.ArgumentParser(description="Тестирование скорости обработки изображений")
    parser.add_argument("--images_dir", required=True, help="Директория с изображениями")
    parser.add_argument("--results_file", default="performance_results.txt", help="Файл для результатов")
    args = parser.parse_args()

    with open(args.results_file, "w", encoding="utf-8") as f:
        f.write(f"РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    image_files = []
    for file in os.listdir(args.images_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(os.path.join(args.images_dir, file))

    image_files = image_files[:10]

    if not image_files:
        print("Не найдены изображения в указанной директории.")
        return

    # Создаем анализатор
    analyzer = TestAnalyzer(args.results_file)

    # Обрабатываем изображения последовательно
    print(f"Начинаем обработку {len(image_files)} изображений...")
    results = []
    for i, image_path in enumerate(image_files):
        print(f"[{i + 1}/{len(image_files)}] Обработка {os.path.basename(image_path)}...")
        result = analyzer.process_image(image_path)
        results.append(result)
        print(f"  Время: {result['processing_time']:.4f} сек, "
              f"Найдено: {result['detected_objects']}, "
              f"Неизвестных: {result['unknown_objects']}")

    # Записываем статистику
    print("Построение графика зависимости...")
    plt.figure(figsize=(10, 6))
    plt.scatter([r["detected_objects"] for r in results],
                [r["processing_time"] for r in results],
                alpha=0.7, marker='o', s=100, edgecolors='black')

    # Добавляем подписи к точкам (имена файлов)
    for r in results:
        plt.annotate(r["image"],
                     (r["detected_objects"], r["processing_time"]),
                     xytext=(5, 5), textcoords='offset points')

    # Добавляем линию тренда
    if len(results) > 1:
        x = np.array([r["detected_objects"] for r in results])
        y = np.array([r["processing_time"] for r in results])

        # Линейная регрессия
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)

        # Создаем точки для построения линии тренда
        x_line = np.linspace(min(x), max(x), 100)
        plt.plot(x_line, p(x_line), "r--",
                 label=f"Тренд: y={z[0]:.6f}x+{z[1]:.6f}")
        plt.legend()

    plt.title('Зависимость времени обработки от количества объектов')
    plt.xlabel('Количество обнаруженных объектов')
    plt.ylabel('Время обработки (секунды)')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Сохраняем график
    graph_path = args.results_file.rsplit('.', 1)[0] + '_graph.png'
    plt.savefig(graph_path)
    plt.close()

    # Добавляем информацию о графике в отчет
    with open(args.results_file, "a", encoding="utf-8") as f:
        f.write(f"\nГрафик зависимости сохранен в: {graph_path}\n")

    print(f"График сохранен в: {graph_path}")


if __name__ == "__main__":
    main()