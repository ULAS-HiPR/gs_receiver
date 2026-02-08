import displayio
import terminalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789

class GPS_Screen:
    def __init__(self, bus):
        self.screen = ST7789(bus, width=240, height=280, colstart=0, rowstart=20, bgr=True,invert=True)
        self.display_group = displayio.Group()
        self.screen.root_group = self.display_group
        font = terminalio.FONT
        colour = 0xFFFFFF
        self.red = 0xFF0000
        self.green = 0x00FF00
        
        self.lat_label = label.Label(font, text="Lat: \n         ", color=colour, scale=2)
        self.lon_label = label.Label(font, text="Lon: \n         ", color=colour, scale=2)
        self.sat_label = label.Label(font, text="Sat:         ", color=colour, scale=2)
        self.alt_label = label.Label(font, text="Alt:         ", color=colour, scale=2)
        self.fix_label = label.Label(font, text="Fix:         ", color=colour, scale=2)

        self.lat_label.x = 20
        self.lat_label.y = 30
        self.lon_label.x = 20
        self.lon_label.y = 90
        self.alt_label.x = 20
        self.alt_label.y = 150
        self.fix_label.x = 20
        self.fix_label.y = 180
        self.sat_label.x = 20
        self.sat_label.y = 210
        

        self.display_group.append(self.lat_label)
        self.display_group.append(self.lon_label)
        self.display_group.append(self.sat_label)
        self.display_group.append(self.alt_label)
        self.display_group.append(self.fix_label)

    def update(self, data):
        if data.fix:
            self.lat_label.text = f"Lat: \n {data.lat}" 
            self.lon_label.text = f"Lon: \n {data.lon}" 
            self.sat_label.text = f"Sat: {data.sat}" 
            self.alt_label.text = f"Alt: {data.alt}m" 
            self.fix_label.color = self.green
        else:
            self.fix_label.color = self.red
            
        self.fix_label.text = f"Fix: {data.fix}"


class Radio_Screen:
    def __init__(self, bus):
        self.screen = ST7789(bus, width=320, height=172, colstart=34, rotation=270)
        self.display_group = displayio.Group()
        self.screen.root_group = self.display_group
        font = terminalio.FONT
        colour = 0xFFFFFF
        self.red = 0xFF0000
        self.green = 0x00FF00
        
        self.rad_label = label.Label(font, text="Last Radio:         ", color=colour, scale=2)
        self.rssi_label = label.Label(font, text="RSSI:         ", color=colour, scale=2)
        self.gps_label = label.Label(font, text="Last GPS Fix:         ", color=colour, scale=2)
        self.con_label = label.Label(font, text="No Connection", color=self.red, scale=2)
        
        self.rad_label.x = 25
        self.rad_label.y = 20
        self.rssi_label.x = 25
        self.rssi_label.y = 50
        self.gps_label.x = 25
        self.gps_label.y = 80
        self.con_label.x = 25
        self.con_label.y = 110
        
        self.display_group.append(self.rad_label)
        self.display_group.append(self.rssi_label)
        self.display_group.append(self.gps_label)
        self.display_group.append(self.con_label)

    def update(self, rad_time, gps_time, rssi=None):
        self.rad_label.text = f"Last Radio: {rad_time}s" 
        self.gps_label.text = f"Last GPS Fix: {gps_time}s" 

        if rssi:
            self.rssi_label.text = f"RSSI: {rssi}db" 
            self.con_label.text = "Connection"
            self.con_label.color = self.green
        else:
            self.rssi_label.text = f"RSSI: :(" 
            self.con_label.text = "No Connection"
            self.con_label.color = self.red
