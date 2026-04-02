from Screen import Screen
import terminalio
from adafruit_display_text import label

class Radio_Screen(Screen):
    def __init__(self, bus):
        super().__init__(bus)
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
