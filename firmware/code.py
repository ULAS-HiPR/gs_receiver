import board
import displayio
import terminalio
from adafruit_display_text import label
from fourwire import FourWire
import time
import busio
import digitalio

from adafruit_st7789 import ST7789
from gps_data import GPS_Data
from screens import GPS_Screen, Radio_Screen



displayio.release_displays()


spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
tft_cs = board.D5
tft_dc = board.D3
tft_rst = board.D4

small_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst)

gps_screen = GPS_Screen(small_bus)


last_data = time.time()
last_gps_data = GPS_Data()
last_gps_time = time.time()
rssi = None
gps_screen.update(last_gps_data)


while True:
    packet = "fake data"

    if packet is None:
        rssi = None
    else:
        last_data = time.time()

        data = str(packet, "utf-8")
        gps_data = GPS_Data(data.split(","))
        
        gps_screen.update(gps_data)

        last_gps_time = gps_data.fix_time

    time.sleep(0.5)


