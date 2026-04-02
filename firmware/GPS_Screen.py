from screen import Screen
import terminalio
from adafruit_display_text import label

class GPS_Screen(Screen):
    def __init__(self, bus):
        super().__init__(bus)
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