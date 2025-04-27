import pytest
from unittest.mock import Mock, patch
import threading
import time
from src.infrastructure.service.parallel_processing_service import ParallelProcessingService
from src.domain.interfaces.processor import IProcessor


class TestParallelProcessingService:
    def setup_method(self):
        self.service = ParallelProcessingService()
        self.test_data = {"key": "value"}

    def test_initialization(self):
        assert self.service.service_name == "ParallelProcessingService"
        assert hasattr(self.service, "logger")

    def test_execute_parallel_tasks_success(self):
        processor1 = Mock()
        processor1.process.return_value = {"result1": "data1"}

        processor2 = Mock()
        processor2.process.return_value = {"result2": "data2"}

        processors = {
            "processor1": processor1,
            "processor2": processor2
        }

        results = self.service.execute_parallel_tasks(self.test_data, processors)

        assert "processor1" in results
        assert "processor2" in results
        assert results["processor1"] == {"result1": "data1"}
        assert results["processor2"] == {"result2": "data2"}

        processor1.process.assert_called_once()
        processor2.process.assert_called_once()

    def test_execute_parallel_tasks_with_error(self):
        processor_success = Mock()
        processor_success.process.return_value = {"result": "success"}

        processor_error = Mock()
        processor_error.process.side_effect = Exception("Test error")

        processors = {
            "success": processor_success,
            "error": processor_error
        }

        results = self.service.execute_parallel_tasks(self.test_data, processors)

        assert "success" in results
        assert "error" in results
        assert results["success"] == {"result": "success"}
        assert "error" in results["error"]
        assert isinstance(results["error"], dict)

    def test_execute_parallel_tasks_with_delayed_processors(self):

        class SlowProcessor:
            def __init__(self, delay, result):
                self.delay = delay
                self.result = result

            def process(self, data):
                time.sleep(self.delay)
                return self.result

        fast_processor = SlowProcessor(0.1, {"fast": "result"})
        slow_processor = SlowProcessor(0.5, {"slow": "result"})

        processors = {
            "fast": fast_processor,
            "slow": slow_processor
        }

        start_time = time.time()
        results = self.service.execute_parallel_tasks(self.test_data, processors)
        execution_time = time.time() - start_time

        assert "fast" in results
        assert "slow" in results
        assert results["fast"] == {"fast": "result"}
        assert results["slow"] == {"slow": "result"}

        assert execution_time < 0.7

    def test_data_modification_isolation(self):
        def modify_data1(data):
            data["modified_by"] = "processor1"
            return {"processed": True}

        def modify_data2(data):
            data["modified_by"] = "processor2"
            return {"processed": True}

        processor1 = Mock()
        processor1.process.side_effect = modify_data1

        processor2 = Mock()
        processor2.process.side_effect = modify_data2

        processors = {
            "processor1": processor1,
            "processor2": processor2
        }

        original_data = {"original": "value"}
        results = self.service.execute_parallel_tasks(original_data, processors)

        assert original_data == {"original": "value"}
        assert "modified_by" not in original_data

        assert "processor1" in results
        assert "processor2" in results

    def test_empty_processors_dict(self):
        results = self.service.execute_parallel_tasks(self.test_data, {})
        assert results == {}

    @patch('threading.Thread')
    def test_thread_creation_and_execution(self, mock_thread):
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        processor1 = Mock()
        processor1.process.return_value = {"result1": "data1"}

        processor2 = Mock()
        processor2.process.return_value = {"result2": "data2"}

        processors = {
            "processor1": processor1,
            "processor2": processor2
        }

        self.service.execute_parallel_tasks(self.test_data, processors)

        assert mock_thread.call_count == 2
        assert mock_thread_instance.start.call_count == 2
        assert mock_thread_instance.join.call_count == 2