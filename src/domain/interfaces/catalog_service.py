from abc import ABC, abstractmethod

class ICatalogService(ABC):
    @abstractmethod
    def query_region(self, center_ra, center_dec, radius_deg):
        pass