# ULAS HiPR Ground Station - Eggtimer Adapter
# KB2040 + 1.69" ST7789 TFT + Eggtimer RX (UART GPS)
#
# Reads NMEA GPS data from Eggtimer RX over UART,
# displays it on the TFT screen, and prints to console.

import board
import busio
import displayio
import time
from fourwire import FourWire

from gps_parser import GPSReader
from gps_screen import GPSScreen

# ── Release any previous display resources ──
displayio.release_displays()

# ── Display setup ──
# KB2040 SPI pins for TFT display
spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
display_bus = FourWire(
    spi,
    command=board.D4,      # TFT_DC   (pin 8 on KB2040)
    chip_select=board.D5,  # TFT_CS   (pin 9 on KB2040)
    reset=board.D10,       # TFT_RST  (pin 26 on KB2040)
)
gps_screen = GPSScreen(display_bus)

# ── UART setup for Eggtimer RX ──
# CHECK YOUR SCHEMATIC: which KB2040 pins connect to the Eggtimer adapter UART?
# D0 = TX (KB2040 transmits), D1 = RX (KB2040 receives from Eggtimer)
uart = busio.UART(
    tx=board.D0,   # RADIO_TX on KB2040 schematic
    rx=board.D1,   # RADIO_RX on KB2040 schematic
    baudrate=9600,
    timeout=0.1,
)

# ── GPS parser ──
gps = GPSReader(uart)

# ── Main loop ──
print("ULAS HiPR Ground Station - Eggtimer")
print("Waiting for GPS data...")
print("-" * 40)

last_print_time = time.monotonic()

while True:
    gps_data = gps.get_data()
    

    # Update screen with every read (labels only change if data changes)
    gps_screen.update(gps_data)
    # print(gps.quasar_connected)
    gps_screen.status_update(gps.quasar_connected)

    # Print to console every second (avoid flooding)
    now = time.monotonic()
    if now - last_print_time >= 1.0:
        last_print_time = now

        if gps_data.has_fix:
            print(
                f"FIX | "
                f"Lat: {gps_data.latitude:.6f} | "
                f"Lon: {gps_data.longitude:.6f} | "
                f"Alt: {gps_data.altitude:.1f}m | "
                f"Sat: {gps_data.satellites} | "
                f"Spd: {gps_data.speed_knots:.1f}kn | "
                f"Time: {gps_data.time}"
            )
        else:
            print(f"NO FIX | Sat: {gps_data.satellites} | Time: {gps_data.time}")
