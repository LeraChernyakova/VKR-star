from src.application.use_cases.detect_objects_use_case import DetectObjectsUseCase
from src.infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter
from src.infrastructure.adapters.celestial_catalog_adapter import CelestialCatalogAdapter
from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter
from src.infrastructure.service.file_dialog_service import FileDialogService
from src.infrastructure.service.parallel_processing_service import ParallelProcessingService
from src.infrastructure.utils.logger import Logger

from src.application.use_cases.select_image_use_case import SelectImageUseCase
from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase
from src.application.use_cases.verify_unknown_objects_use_case import VerifyUnknownObjectsUseCase
from src.application.use_cases.process_image_use_case import ProcessImageUseCase

from src.presentation.controllers.analysis_controller import AnalysisController
from src.presentation.views.astrometry_app import AstrometryApp

import tkinter as tk

def main():
    logger = Logger()
    logger.info("main","Запуск приложения")

    api_key = "lyjwakywqahzzjvj"
    astrometry_service = AstrometryNetAdapter(api_key)
    catalog_service = CelestialCatalogAdapter()
    detection_service = SepDetectionAdapter()
    file_selection_service = FileDialogService()
    parallel_service = ParallelProcessingService()

    select_image_use_case = SelectImageUseCase(file_selection_service)
    calibrate_image_use_case = CalibrateImageUseCase(astrometry_service)
    detect_objects_use_case = DetectObjectsUseCase(detection_service)
    verify_objects_use_case = VerifyUnknownObjectsUseCase(catalog_service)
    process_image_use_case = ProcessImageUseCase(parallel_service)

    controller = AnalysisController(
        select_image_use_case,
        calibrate_image_use_case,
        detect_objects_use_case,
        verify_objects_use_case,
        process_image_use_case
    )

    root = tk.Tk()
    AstrometryApp(root, controller)
    root.mainloop()

if __name__ == "__main__":
    main()