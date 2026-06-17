# gps_screen.py - GPS telemetry display for Eggtimer adapter

from screen import Screen
import terminalio
from adafruit_display_text import label


class GPSScreen(Screen):
    def __init__(self, bus):
        super().__init__(bus)
        font = terminalio.FONT
        white = 0xFFFFFF
        self.red = 0xFF0000
        self.green = 0x00FF00

        # Title
        self.title_label = label.Label(font, text="ULAS HiPR GS", color=0x00AAFF, scale=2)
        self.title_label.x = 30
        self.title_label.y = 15

        # Fix status
        self.fix_label = label.Label(font, text="Fix: No", color=self.red, scale=2)
        self.fix_label.x = 10
        self.fix_label.y = 50

        # Satellites
        self.sat_label = label.Label(font, text="Sat: 0", color=white, scale=2)
        self.sat_label.x = 10
        self.sat_label.y = 80

        # Latitude
        self.lat_label = label.Label(font, text="Lat: --", color=white, scale=2)
        self.lat_label.x = 10
        self.lat_label.y = 110

        # Longitude
        self.lon_label = label.Label(font, text="Lon: --", color=white, scale=2)
        self.lon_label.x = 10
        self.lon_label.y = 140

        # Altitude
        self.alt_label = label.Label(font, text="Alt: --", color=white, scale=2)
        self.alt_label.x = 10
        self.alt_label.y = 170

        # Speed
        self.spd_label = label.Label(font, text="Spd: --", color=white, scale=2)
        self.spd_label.x = 10
        self.spd_label.y = 200

        # Time
        self.time_label = label.Label(font, text="T: --", color=0x888888, scale=1)
        self.time_label.x = 10
        self.time_label.y = 235

        # Status / last update
        self.status_label = label.Label(font, text="Waiting...", color=0xFFFF00, scale=1)
        self.status_label.x = 10
        self.status_label.y = 260

        # Add all labels to display group
        self.display_group.append(self.title_label)
        self.display_group.append(self.fix_label)
        self.display_group.append(self.sat_label)
        self.display_group.append(self.lat_label)
        self.display_group.append(self.lon_label)
        self.display_group.append(self.alt_label)
        self.display_group.append(self.spd_label)
        self.display_group.append(self.time_label)
        self.display_group.append(self.status_label)

    def update(self, gps_data):
        """Update all labels with new GPS data"""
        # Fix status
        if gps_data.has_fix:
            self.fix_label.text = "Fix: Yes"
            self.fix_label.color = self.green
        else:
            self.fix_label.text = "Fix: No"
            self.fix_label.color = self.red

        # Satellites
        self.sat_label.text = f"Sat: {gps_data.satellites}"

        # Only update position fields if we have a fix
        if gps_data.has_fix:
            self.lat_label.text = f"Lat: {gps_data.latitude:.6f}"
            self.lon_label.text = f"Lon: {gps_data.longitude:.6f}"
            self.alt_label.text = f"Alt: {gps_data.altitude:.1f}m"
            self.spd_label.text = f"Spd: {gps_data.speed_knots:.1f}kn"
            #self.status_label.text = "Receiving data"
            #self.status_label.color = self.green

        # Time (always update if available)
        if gps_data.time:
            self.time_label.text = f"T: {gps_data.time} {gps_data.date}"
            
    def status_update(self, quasar_status):
        if quasar_status:
            self.status_label.text = "Connected"
            self.status_label.color = self.green
        else:
            self.status_label.text = "Disconnected"
            self.status_label.color = self.red

