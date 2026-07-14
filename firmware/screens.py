import displayio
import terminalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789


class GPS_Screen:
    def __init__(self, bus):
        self.screen = ST7789(
            bus,
            width=240,
            height=280,
            colstart=0,
            rowstart=20,
            bgr=True,
            invert=True,
        )
        self.display_group = displayio.Group()
        self.screen.root_group = self.display_group
        font = terminalio.FONT
        self.white = 0xFFFFFF
        self.red = 0xFF4040
        self.green = 0x45E06F
        self.amber = 0xFFCC33
        self.cyan = 0x51C8FF

        self.title_label = self._label(font, "OGMA GROUND", 12, 16, self.white, 2)
        self.link_label = self._label(font, "LoRa: starting", 12, 48, self.amber, 2)
        self.signal_label = self._label(font, "RSSI: --  SNR: --", 12, 74, self.white)
        self.packet_label = self._label(font, "Packets: 0  Bad: 0", 12, 92, self.white)

        self.fix_label = self._label(font, "GPS: no fix", 12, 124, self.red, 2)
        self.sat_label = self._label(font, "Satellites: 0", 12, 150, self.white)
        self.lat_label = self._label(font, "Lat: --", 12, 174, self.white)
        self.lon_label = self._label(font, "Lon: --", 12, 194, self.white)
        self.alt_label = self._label(font, "Altitude: --", 12, 214, self.white)
        self.age_label = self._label(font, "Last packet: --", 12, 242, self.cyan)

    def _label(self, font, text, x, y, colour, scale=1):
        item = label.Label(font, text=text, color=colour, scale=scale)
        item.x = x
        item.y = y
        self.display_group.append(item)
        return item

    @staticmethod
    def _set_text(item, text):
        if item.text != text:
            item.text = text

    def update(self, data):
        if data.fix:
            self._set_text(self.fix_label, "GPS: FIX")
            self.fix_label.color = self.green
            self._set_text(self.lat_label, "Lat: {:.7f}".format(data.lat))
            self._set_text(self.lon_label, "Lon: {:.7f}".format(data.lon))
            self._set_text(self.alt_label, "Altitude: {:.1f} m".format(data.alt))
        else:
            self._set_text(self.fix_label, "GPS: no fix")
            self.fix_label.color = self.red
            self._set_text(self.lat_label, "Lat: --")
            self._set_text(self.lon_label, "Lon: --")
            self._set_text(self.alt_label, "Altitude: --")
        self._set_text(self.sat_label, "Satellites: {}".format(data.sat))

    def update_link(self, radio_ready, packet_count, bad_count, rssi, snr, age_s):
        if not radio_ready:
            link_text = "LoRa: fault"
            link_colour = self.red
        elif age_s is None:
            link_text = "LoRa: waiting"
            link_colour = self.amber
        elif age_s <= 3.0:
            link_text = "LoRa: linked"
            link_colour = self.green
        else:
            link_text = "LoRa: stale"
            link_colour = self.red

        self._set_text(self.link_label, link_text)
        self.link_label.color = link_colour
        self._set_text(
            self.signal_label,
            "RSSI: {}  SNR: {}".format(
                "--" if rssi is None else "{} dBm".format(rssi),
                "--" if snr is None else "{:.1f} dB".format(snr),
            ),
        )
        self._set_text(
            self.packet_label,
            "Packets: {}  Bad: {}".format(packet_count, bad_count),
        )
        self._set_text(
            self.age_label,
            "Last packet: --" if age_s is None else "Last packet: {:.1f} s".format(age_s),
        )
