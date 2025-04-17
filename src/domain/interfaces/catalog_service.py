from abc import ABC, abstractmethod

class ICatalogService(ABC):
    @abstractmethod
    def query_by_coordinates(self, ra, dec, radius_arcsec):
        pass