from src.infrastructure.utils.logger import Logger

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
import datetime

class VerifyUnknownObjectsUseCase:
    def __init__(self, catalog_service):
        self.service_name = "VerifyUnknownObjectsUseCase"
        self.catalog = catalog_service
        self.logger = Logger()

    def execute(self, image_path, pixel_coordinates, wcs, match_radius_arcsec=5):
        try:
            self.logger.info(self.service_name, f"Проверка {len(pixel_coordinates)} объектов")

            observation_time = None
            try:
                if hasattr(wcs, "observation_date") and wcs.observation_date is not None:
                    observation_time = Time(wcs.observation_date, format='isot')

                if hasattr(wcs, "to_header"):
                    header = wcs.to_header()
                    if 'DATE-OBS' in header:
                        observation_time = Time(header['DATE-OBS'], format='isot')
                    if 'DATE' in header:
                        observation_time = Time(header['DATE'], format='isot')

            except Exception as e:
                self.logger.warning(self.service_name, f"Ошибка при определении времени наблюдения: {e}")

            sky_coords_list = []
            for x_pixel, y_pixel in pixel_coordinates:
                try:
                    ra, dec = wcs.all_pix2world([[x_pixel, y_pixel]], 0)[0]
                    sky_coords_list.append({
                        "pixel_x": x_pixel,
                        "pixel_y": y_pixel,
                        "ra": ra,
                        "dec": dec
                    })
                except Exception as e:
                    self.logger.warning(self.service_name,
                                        f"Ошибка преобразования координат ({x_pixel},{y_pixel}): {e}")

            # Проверка наличия объектов для анализа
            if not sky_coords_list:
                return {"unknown_objects": [], "error": "Нет объектов для проверки"}

            # Находим центр и радиус поиска
            ras = [obj["ra"] for obj in sky_coords_list]
            decs = [obj["dec"] for obj in sky_coords_list]
            center_ra = sum(ras) / len(ras)
            center_dec = sum(decs) / len(decs)

            # Находим максимальное угловое расстояние между объектами
            max_separation = 0
            for ra, dec in zip(ras, decs):
                sep = ((ra - center_ra) ** 2 + (dec - center_dec) ** 2) ** 0.5
                max_separation = max(max_separation, sep)

            # Добавляем запас к радиусу поиска
            search_radius = max_separation + 0.05  # в градусах

            # Запрашиваем объекты из каталогов
            catalog_results = self.catalog.query_region(
                center_ra, center_dec,
                radius_deg=search_radius,
                observation_time=observation_time  # Передаем только если оно определено достоверно
            )

            # Проверяем каждый объект
            unknown_objects = []
            known_objects = []

            for obj in sky_coords_list:
                is_known = False
                ra, dec = obj["ra"], obj["dec"]

                # Ищем ближайший объект в каталогах
                for (cat_ra, cat_dec), catalog_entries in catalog_results.items():
                    # Вычисляем расстояние в угловых секундах
                    dist_deg = ((ra - cat_ra) ** 2 + (dec - cat_dec) ** 2) ** 0.5
                    dist_arcsec = dist_deg * 3600

                    if dist_arcsec <= match_radius_arcsec:
                        is_known = True
                        obj["catalog_match"] = catalog_entries
                        obj["separation_arcsec"] = dist_arcsec
                        known_objects.append(obj)
                        break

                if not is_known:
                    unknown_objects.append(obj)

            # Выводим результаты
            print(f"\n=== РЕЗУЛЬТАТЫ АНАЛИЗА ОБЪЕКТОВ ===")
            print(f"Всего объектов: {len(sky_coords_list)}")
            print(f"Известные объекты: {len(known_objects)}")
            print(f"Неизвестные объекты: {len(unknown_objects)}")

            if unknown_objects:
                print("\n=== НЕИЗВЕСТНЫЕ ОБЪЕКТЫ ===")
                for i, obj in enumerate(unknown_objects, 1):
                    print(f"{i}. Пиксели: ({obj['pixel_x']:.2f}, {obj['pixel_y']:.2f}), "
                          f"RA={obj['ra']:.6f}°, DEC={obj['dec']:.6f}°")

            return {
                "unknown_objects": unknown_objects,
                "known_objects": known_objects,
                "total_count": len(sky_coords_list),
                "unknown_count": len(unknown_objects)
            }

        except Exception as e:
            self.logger.error(self.service_name, f"Ошибка в проверке объектов: {str(e)}")
            return {"error": str(e)}