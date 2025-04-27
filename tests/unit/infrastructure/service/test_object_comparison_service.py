import pytest
from unittest.mock import Mock, patch
import numpy as np
from src.infrastructure.service.object_comparison_service import ObjectComparisonService


class TestObjectComparisonService:
    def setup_method(self):
        self.service = ObjectComparisonService()
        self.detected_objects = [(100, 100), (200, 200), (300, 300)]
        self.reference_objects = [(105, 102), (400, 400)]

    def test_initialization(self):
        """Тест корректной инициализации сервиса"""
        assert self.service.service_name == "ObjectComparisonService"
        assert hasattr(self.service, "logger")

    def test_find_unique_objects_with_matches(self):
        """Тест поиска уникальных объектов при наличии совпадений"""
        # Первый объект из detected должен совпасть с первым из reference (расстояние ~5.4)
        unique_objects = self.service.find_unique_objects(
            self.detected_objects, self.reference_objects, match_threshold=10
        )

        # Должны остаться только два объекта, которые не имеют совпадений
        assert len(unique_objects) == 2
        assert (200, 200) in unique_objects
        assert (300, 300) in unique_objects
        assert (100, 100) not in unique_objects

    def test_find_unique_objects_no_matches(self):
        """Тест поиска уникальных объектов при отсутствии совпадений"""
        # Использовать маленький порог, чтобы ни один объект не совпал
        unique_objects = self.service.find_unique_objects(
            self.detected_objects, self.reference_objects, match_threshold=5
        )

        # Должны остаться все исходные объекты
        assert len(unique_objects) == 3
        assert set(unique_objects) == set(self.detected_objects)

    def test_empty_reference_objects(self):
        """Тест поведения при пустом списке эталонных объектов"""
        unique_objects = self.service.find_unique_objects(
            self.detected_objects, [], match_threshold=10
        )

        # Все объекты должны быть возвращены как уникальные
        assert len(unique_objects) == 3
        assert set(unique_objects) == set(self.detected_objects)

    def test_empty_detected_objects(self):
        """Тест поведения при пустом списке обнаруженных объектов"""
        unique_objects = self.service.find_unique_objects(
            [], self.reference_objects, match_threshold=10
        )

        # Результат должен быть пустым списком
        assert len(unique_objects) == 0
        assert unique_objects == []

    def test_threshold_edge_cases(self):
        """Тест поведения на границе порога совпадения"""
        detected = [(100, 100)]

        # Объекты на расстоянии ровно 10 пикселей
        reference_at_threshold = [(110, 100)]

        # Точно на пороге - не должен считаться совпадением
        unique_objects = self.service.find_unique_objects(
            detected, reference_at_threshold, match_threshold=10
        )
        assert len(unique_objects) == 1

        # Чуть больше порога - должен считаться совпадением
        unique_objects = self.service.find_unique_objects(
            detected, reference_at_threshold, match_threshold=10.1
        )
        assert len(unique_objects) == 0

    def test_multiple_reference_matches(self):
        """Тест с несколькими эталонными объектами, близкими к одному обнаруженному"""
        detected = [(100, 100)]
        reference = [(105, 105), (95, 95), (105, 95)]  # Все в пределах порога от detected

        unique_objects = self.service.find_unique_objects(
            detected, reference, match_threshold=10
        )

        # Объект должен отсутствовать, так как он совпал хотя бы с одним эталонным
        assert len(unique_objects) == 0

    def test_numpy_array_inputs(self):
        """Тест работы с входными данными в формате numpy arrays"""
        detected_np = np.array(self.detected_objects)
        reference_np = np.array(self.reference_objects)

        unique_objects = self.service.find_unique_objects(
            detected_np, reference_np, match_threshold=10
        )

        assert len(unique_objects) == 2
        # Проверка должна учитывать, что результат может быть NumPy-массивом или списком кортежей
        for obj in [(200, 200), (300, 300)]:
            assert obj in unique_objects or np.any(np.all(np.array(obj) == unique_objects, axis=1))