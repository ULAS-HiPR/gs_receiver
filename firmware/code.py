import json
import time

import board
import busio
import displayio
import usb_cdc
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
packet_count = 0
last_packet_time = None
last_display_update = 0.0
usb_streaming = False

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
        if not usb_streaming:
            gps_screen.update(gps_record)
        return

    if decoded["type"] == TYPE_TEST:
        print("#OGMA test sequence={} counter={} rssi={}".format(
            decoded["sequence"], decoded["counter"], radio.last_rssi_dbm
        ))


while True:
    now = time.monotonic()
    streaming_now = usb_cdc.console is not None and usb_cdc.console.connected
    if streaming_now != usb_streaming:
        usb_streaming = streaming_now
        gps_screen.screen.auto_refresh = not usb_streaming

    if not radio_ready and now - last_init_attempt >= 2.0:
        last_init_attempt = now
        radio_ready = radio.init()
        print("#OGMA radio={}".format("ready" if radio_ready else "retrying"))

    if radio_ready:
        try:
            packet = radio.receive()
            if packet is not None:
                decoded = decode_packet(packet)
                decoded_records = (
                    len(decoded.get("records", ()))
                    if decoded["type"] == TYPE_CAN_BUNDLE
                    else 1
                )
                print("#OGMA packet sequence={} type={} records={} rssi={} snr={}".format(
                    decoded["sequence"], decoded["type"], decoded_records,
                    radio.last_rssi_dbm, radio.last_snr_db,
                ))
                emit_packet(decoded)
                packet_count += 1
                last_packet_time = now
        except Exception as exc:
            bad_packet_count += 1
            radio_ready = False
            print("#OGMA bad_packet={} error={}".format(bad_packet_count, exc))

    if not usb_streaming and now - last_display_update >= 0.5:
        last_display_update = now
        packet_age = None if last_packet_time is None else now - last_packet_time
        gps_screen.update_link(
            radio_ready,
            packet_count,
            bad_packet_count,
            radio.last_rssi_dbm,
            radio.last_snr_db,
            packet_age,
        )

    time.sleep(0.001)
