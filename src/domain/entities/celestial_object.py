class CelestialObject:
    def __init__(self, pixel_x, pixel_y, ra=None, dec=None, flux=None, source_type=None):
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.ra = ra
        self.dec = dec
        self.flux = flux
        self.source_type = source_type