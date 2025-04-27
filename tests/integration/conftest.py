import pytest
import os
import shutil

@pytest.fixture(scope="session")
def test_fixtures_path():
    return os.path.join(os.path.dirname(__file__), "..", "fixtures")

@pytest.fixture
def test_image(test_fixtures_path):
    # Проверка наличия тестового изображения
    image_path = os.path.join(test_fixtures_path, "test_star_field.jpg")
    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found: {image_path}")
    return image_path