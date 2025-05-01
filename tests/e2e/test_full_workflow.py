import pytest
import os
import shutil
from unittest.mock import patch
import vcr

from src.infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter
from src.infrastructure.adapters.celestial_catalog_adapter import CelestialCatalogAdapter
from src.infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter
from src.infrastructure.service.file_dialog_service import FileDialogService
from src.infrastructure.service.parallel_processing_service import ParallelProcessingService
from src.infrastructure.service.object_comparison_service import ObjectComparisonService
from src.application.use_cases.select_image_use_case import SelectImageUseCase
from src.application.use_cases.calibrate_image_use_case import CalibrateImageUseCase
from src.application.use_cases.detect_objects_use_case import DetectObjectsUseCase
from src.application.use_cases.verify_unknown_objects_use_case import VerifyUnknownObjectsUseCase
from src.application.use_cases.process_image_use_case import ProcessImageUseCase
from src.presentation.controllers.analysis_controller import AnalysisController

my_vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/vcr_cassettes',
    record_mode='once',
    decode_compressed_response=True
)


class TestFullWorkflowE2E:

    @pytest.fixture
    def setup_system(self):
        # Используем VCR для записи взаимодействия с внешними API
        with my_vcr.use_cassette('e2e_full_workflow.yaml'):
            # Инициализируем реальные компоненты
            api_key = "lyjwakywqahzzjvj"
            astrometry_service = AstrometryNetAdapter(api_key)
            catalog_service = CelestialCatalogAdapter()
            detection_service = SepDetectionAdapter()

            # Для файлового диалога используем мок
            file_dialog_service = FileDialogService()

            # Инициализируем остальные сервисы
            parallel_service = ParallelProcessingService()
            comparison_service = ObjectComparisonService()

            # Создаем use cases
            select_image_use_case = SelectImageUseCase(file_dialog_service)
            calibrate_image_use_case = CalibrateImageUseCase(astrometry_service)
            detect_use_case = DetectObjectsUseCase(detection_service)
            verify_use_case = VerifyUnknownObjectsUseCase(catalog_service)
            process_use_case = ProcessImageUseCase(parallel_service, comparison_service)

            # Создаем контроллер
            controller = AnalysisController(
                select_image_use_case,
                calibrate_image_use_case,
                detect_use_case,
                verify_use_case,
                process_use_case
            )

            return {
                "controller": controller,
                "file_dialog_service": file_dialog_service
            }

    @my_vcr.use_cassette('e2e_full_workflow.yaml')
    def test_full_workflow(self, setup_system, test_image):
        """
        Тест полного процесса обработки изображения от начала до конца
        """
        controller = setup_system["controller"]
        file_service = setup_system["file_dialog_service"]

        # Подменяем выбор файла, чтобы не открывать диалоговое окно
        with patch.object(file_service, 'select_image', return_value=test_image):
            # 1. Выбор изображения
            image_path = controller.select_image()
            assert image_path == test_image

            # 2. Анализ изображения
            result = controller.analyze_image(image_path)

            # 3. Проверка результатов
            assert result is not None
            assert "visualization_path" in result
            assert "truly_unknown_coords" in result
            assert os.path.exists(result["visualization_path"])

            # 4. Проверка совместимости данных
            assert isinstance(result["truly_unknown_coords"], list)

            # 5. Удаляем временные файлы
            if os.path.exists(result["visualization_path"]):
                os.remove(result["visualization_path"])