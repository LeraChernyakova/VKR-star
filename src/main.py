import os
import tkinter as tk

from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter
from src.infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter
from src.infrastructure.adapters.celestial_catalog_adapter import CelestialCatalogAdapter

from src.infrastructure.service.file_dialog_service import FileDialogService
from src.infrastructure.service.object_comparison_service import ObjectComparisonService
from src.infrastructure.service.parallel_processing_service import ParallelProcessingService

from src.application.use_cases.select_image_use_case import SelectImageUseCase
from src.application.use_cases.process_image_use_case import ProcessImageUseCase
from src.application.use_cases.detect_objects_use_case import DetectObjectsUseCase
from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase
from src.application.use_cases.verify_unknown_objects_use_case import VerifyUnknownObjectsUseCase

from src.presentation.views.astrometry_app import AstrometryApp
from src.presentation.controllers.analysis_controller import AnalysisController


def cleanup_directories():
    processing_dir = r"F:\ETU\VKR\repo\VKR-star\images\processing"
    if os.path.exists(processing_dir):
        for file in os.listdir(processing_dir):
            file_path = os.path.join(processing_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Ошибка при удалении {file_path}: {e}")

    test_image_dir = r"F:\ETU\VKR\repo\VKR-star\images\test-image"
    if os.path.exists(test_image_dir):
        for file in os.listdir(test_image_dir):
            if "_filtered" in file or "_highlighted" in file:
                file_path = os.path.join(test_image_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Ошибка при удалении {file_path}: {e}")

def main():
    cleanup_directories()
    api_key = "lyjwakywqahzzjvj"
    astrometry_service = AstrometryNetAdapter(api_key)
    detection_service = SepDetectionAdapter()
    file_selection_service = FileDialogService()
    catalog_service = CelestialCatalogAdapter()
    comparison_service = ObjectComparisonService()

    select_image_use_case = SelectImageUseCase(file_selection_service)
    calibrate_image_use_case = CalibrateImageUseCase(astrometry_service)
    detect_objects_use_case = DetectObjectsUseCase(detection_service)

    parallel_service = ParallelProcessingService(calibrate_image_use_case, detect_objects_use_case)

    verify_unknown_objects_use_case = VerifyUnknownObjectsUseCase(catalog_service, comparison_service)

    process_image_use_case = ProcessImageUseCase(parallel_service, verify_unknown_objects_use_case)

    controller = AnalysisController(select_image_use_case, process_image_use_case)

    root = tk.Tk()
    AstrometryApp(root, controller)
    root.mainloop()

if __name__ == "__main__":
    main()