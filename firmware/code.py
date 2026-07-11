import json
import time

import board
import busio
import displayio
from fourwire import FourWire

from gps_data import GPS_Data
from screens import GPS_Screen
from sx1272 import SX1272
from telemetry_protocol import TYPE_CAN_BUNDLE, TYPE_GPS, TYPE_TEST, decode_packet


displayio.release_displays()

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
tft_bus = FourWire(spi, command=board.D4, chip_select=board.D5, reset=board.D10)
gps_screen = GPS_Screen(tft_bus)
gps_screen.update(GPS_Data())

radio = SX1272(
    spi,
    cs_pin=board.D9,
    reset_pin=board.D2,
    rx_switch_pin=board.A0,
    tx_switch_pin=board.A1,
)

radio_ready = radio.init()
last_init_attempt = time.monotonic()
bad_packet_count = 0

print("#OGMA groundstation protocol=1 radio={}".format("ready" if radio_ready else "retrying"))


def emit_packet(decoded):
    if decoded["type"] == TYPE_CAN_BUNDLE:
        for record in decoded["records"]:
            payload = record["data"][: record["dlc"]]
            print("{:03X}#{}".format(record["id"], payload.hex().upper()))
        return

    if decoded["type"] == TYPE_GPS:
        record = {
            "lat": decoded["latitude_deg"],
            "lon": decoded["longitude_deg"],
            "sat": decoded["satellites"],
            "alt": decoded["altitude_m"],
            "velocity_m_s": decoded["velocity_m_s"],
            "fix_time": decoded["uptime_ms"] // 1000,
            "fix": decoded["fix"],
            "rssi": radio.last_rssi_dbm,
            "snr": radio.last_snr_db,
            "sequence": decoded["sequence"],
        }
        print(json.dumps(record))
        gps_record = GPS_Data((
            record["lat"], record["lon"], record["sat"],
            record["alt"], record["fix_time"],
        ))
        gps_record.fix = record["fix"]
        gps_screen.update(gps_record)
        return

    if decoded["type"] == TYPE_TEST:
        print("#OGMA test sequence={} counter={} rssi={}".format(
            decoded["sequence"], decoded["counter"], radio.last_rssi_dbm
        ))


while True:
    now = time.monotonic()
    if not radio_ready and now - last_init_attempt >= 2.0:
        last_init_attempt = now
        radio_ready = radio.init()
        print("#OGMA radio={}".format("ready" if radio_ready else "retrying"))

    if radio_ready:
        try:
            packet = radio.receive()
            if packet is not None:
                emit_packet(decode_packet(packet))
        except Exception as exc:
            bad_packet_count += 1
            radio_ready = False
            print("#OGMA bad_packet={} error={}".format(bad_packet_count, exc))

    time.sleep(0.01)
