class SelectImageUseCase:
    def __init__(self, file_selection_service):
        self.file_selection_service = file_selection_service

    def execute(self):
        return self.file_selection_service.select_image()