import threading
from src.infrastructure.utils.logger import Logger


class ProcessingController:
    def __init__(self):
        self.logger = Logger()
        self.logger.info("ProcessingController initialized")

    def run_parallel_processing(self, context, astrometry_processor, sextractor_processor, comparison_processor):
        self.logger.info("Starting parallel processing")

        astrometry_context = context.copy()
        sextractor_context = context.copy()

        astrometry_thread = threading.Thread(
            target=self._run_processor,
            args=(astrometry_processor, context),
            daemon=True
        )

        sextractor_thread = threading.Thread(
            target=self._run_processor,
            args=(sextractor_processor, context),
            daemon=True
        )

        astrometry_thread.start()
        sextractor_thread.start()

        astrometry_thread.join()
        sextractor_thread.join()

        for key in sextractor_context:
            if key not in context:
                context[key] = sextractor_context[key]

        for key in astrometry_context:
            if key not in context:
                context[key] = astrometry_context[key]

        self.logger.info("Both processes complete, running comparison")
        comparison_processor.handle(context)

        return context

    def _run_processor(self, processor, context):
        try:
            processor.handle(context)
        except Exception as e:
            self.logger.error(f"Error in processor {processor.__class__.__name__}: {str(e)}")
