class GPS_Data:
    def __init__(self, data=None):
        if data is None:
            data = (0, 0, 0, 0, 0)
        try:
            self.fix_time = int(data[4])
            self.lat = float(data[0])
            self.lon = float(data[1])
            self.sat = int(data[2])
            self.alt = float(data[3])
        
            if (self.lat != 0) or (self.lon != 0):
                self.fix = True
            else:
                self.fix = False
        except (IndexError, TypeError, ValueError):
            self.fix_time = 0
            self.lat = 0
            self.lon = 0
            self.sat = 0
            self.alt = 0
            self.fix = False
