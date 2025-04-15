from infrastructure.adapters.astrometry_net_adapter import AstrometryNetAdapter
from infrastructure.adapters.celestial_catalog_adapter import CelestialCatalogAdapter
from infrastructure.adapters.sep_detection_adapter import SepDetectionAdapter
from application.use_cases.find_unknown_objects import FindUnknownObjectsUseCase
from presentation.controllers.analysis_controller import AnalysisController
from presentation.views.analysis_view import AnalysisView
from infrastructure.utils.logger import LoggerFactory


def main():
    # Создание logger
    logger = LoggerFactory.create_logger()

    # Настройка зависимостей
    api_key = "YOUR_API_KEY"
    astrometry_service = AstrometryNetAdapter(api_key)
    detection_service = SepDetectionAdapter()
    catalog_service = CelestialCatalogAdapter()

    # Настройка Use Case
    find_unknown_objects_use_case = FindUnknownObjectsUseCase(
        astrometry_service, detection_service, catalog_service
    )

    # Настройка контроллера
    controller = AnalysisController(find_unknown_objects_use_case)

    # Настройка GUI
    view = AnalysisView(controller)
    view.run()


if __name__ == "__main__":
    main()