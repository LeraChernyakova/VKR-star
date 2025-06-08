from abc import ABC, abstractmethod


class ICatalogService(ABC):
    @abstractmethod
    def find_object_match(self, ra, dec, radius_arcsec, early_exit):
        pass