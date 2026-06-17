# gps_parser.py - NMEA GPS parser ported to CircuitPython
# Original: EggtimerPico_GS (MicroPython)
# Parses $GPRMC, $GPGGA, $GPGSA sentences from Eggtimer RX

import time

class GPSData:
    """Stores parsed GPS data"""
    def __init__(self):
        self.has_fix = False
        self.latitude = 0.0
        self.longitude = 0.0
        self.speed_knots = 0.0
        self.time = ""
        self.date = ""
        self.satellites = 0
        self.altitude = 0.0
        self.hdop = 0.0
        self.pdop = 0.0
        self.vdop = 0.0


class GPSReader:
    """Reads and parses NMEA data from UART - CircuitPython version"""
    def __init__(self, uart):
        self.uart = uart
        self._line_buf = bytearray()
        self.current_data = GPSData()
        self.has_new_data = False
        self._last_quasar_time = 0 

    @property
    def quasar_connected(self):
    # Consider disconnected if no heartbeat in 5 seconds
        return (time.monotonic() - self._last_quasar_time) < 5.0

    def update(self):
        """Check for new GPS data - non-blocking. Returns True if data was updated."""
        self.has_new_data = False

        while self.uart.in_waiting:
            byte = self.uart.read(1)
            if not byte:
                break

            b = byte[0]

            if not self._line_buf and b == ord('!'):
                self._line_buf.append(b)
                continue
            
            if self._line_buf and self._line_buf[0] == ord('!'):
                self._line_buf.append(b)
                try:
                    so_far = self._line_buf.decode("ascii", "ignore")
                    if "QUASAR" in so_far:
                        print("qusar_connected")
                        self._last_quasar_time = time.monotonic()
                        self._line_buf = bytearray()
                        continue
                    elif len(self._line_buf) > 32:
                    # Too long, not a Quasar string, discard
                        self._line_buf = bytearray()
                except Exception:
                    self._line_buf = bytearray()
                continue

        # Throw away everything before the first '$' (NMEA start)
            if not self._line_buf and b != ord('$'):
                continue
            
            self._line_buf.append(b)

            # A complete NMEA sentence ends with '\n' (0x0A)
            if b == ord('\n'):
                raw = bytes(self._line_buf)
                print(raw)
                self._line_buf = bytearray()

                try:
                    sentence = raw.decode("ascii", "ignore").strip()
                    print(sentence)
                except Exception:
                    continue

                # Validate checksum before parsing
                #if not _validate_checksum(sentence):
                #    continue

                updated = False
                if sentence.startswith("$GPRMC") or sentence.startswith("$GNRMC"):
                    _parse_rmc(sentence, self.current_data)
                    updated = True
                elif sentence.startswith("$GPGGA") or sentence.startswith("$GNGGA"):
                    _parse_gga(sentence, self.current_data)
                    updated = True
                elif sentence.startswith("$GPGSA") or sentence.startswith("$GNGSA"):
                    _parse_gsa(sentence, self.current_data)
                    updated = True

                if updated:
                    self.has_new_data = True

        return self.has_new_data

    def get_data(self):
        self.update()
        return self.current_data
    
def _validate_checksum(sentence):
    """Returns True if NMEA checksum is valid or absent"""
    try:
        if '*' not in sentence:
            return True  # No checksum to validate, accept it
        body, checksum_str = sentence[1:].rsplit('*', 1)
        expected = int(checksum_str[:2], 16)
        actual = 0
        for ch in body:
            actual ^= ord(ch)
        return actual == expected
    except Exception:
        return False

def _process_nmea_data(nmea_data):
    """Process a complete NMEA data string"""
    gps_data = GPSData()
    sentences = nmea_data.strip().split("$")

    for sentence in sentences:
        if not sentence:
            continue
        sentence = "$" + sentence.strip()

        if sentence.startswith("$GPRMC"):
            _parse_rmc(sentence, gps_data)
        elif sentence.startswith("$GPGGA"):
            _parse_gga(sentence, gps_data)
        elif sentence.startswith("$GPGSA"):
            _parse_gsa(sentence, gps_data)

    return gps_data


def _parse_rmc(sentence, gps_data):
    """Parse RMC sentence for time, date, location, speed"""
    parts = sentence.split(",")
    if len(parts) < 12:
        return

    gps_data.has_fix = parts[2] == "A"

    # Time
    if parts[1] and len(parts[1]) >= 6:
        try:
            gps_data.time = f"{parts[1][0:2]}:{parts[1][2:4]}:{parts[1][4:6]}"
        except (ValueError, IndexError):
            pass

    # Date
    if parts[9] and len(parts[9]) >= 6:
        try:
            gps_data.date = f"{parts[9][0:2]}/{parts[9][2:4]}/20{parts[9][4:6]}"
        except (ValueError, IndexError):
            pass

    if gps_data.has_fix:
        # Latitude
        if parts[3] and parts[5]:
            try:
                lat_deg = float(parts[3][0:2])
                lat_min = float(parts[3][2:])
                lat_decimal = lat_deg + (lat_min / 60)
                if parts[4] == "S":
                    lat_decimal = -lat_decimal
                gps_data.latitude = lat_decimal

                lon_deg = float(parts[5][0:3])
                lon_min = float(parts[5][3:])
                lon_decimal = lon_deg + (lon_min / 60)
                if parts[6] == "W":
                    lon_decimal = -lon_decimal
                gps_data.longitude = lon_decimal
            except (ValueError, IndexError):
                pass

        # Speed
        if parts[7]:
            try:
                gps_data.speed_knots = float(parts[7])
            except ValueError:
                pass


def _parse_gga(sentence, gps_data):
    """Parse GGA sentence for satellites, altitude, HDOP"""
    parts = sentence.split(",")
    if len(parts) < 15:
        return

    if parts[7]:
        try:
            gps_data.satellites = int(parts[7])
        except ValueError:
            pass

    if parts[8]:
        try:
            gps_data.hdop = float(parts[8])
        except ValueError:
            pass

    if parts[9] and len(parts) > 10 and parts[10] == "M":
        try:
            gps_data.altitude = float(parts[9])
        except ValueError:
            pass


def _parse_gsa(sentence, gps_data):
    """Parse GSA sentence for PDOP, HDOP, VDOP"""
    parts = sentence.split(",")
    if len(parts) < 18:
        return

    if parts[15]:
        try:
            gps_data.pdop = float(parts[15])
        except ValueError:
            pass

    if parts[16]:
        try:
            gps_data.hdop = float(parts[16])
        except ValueError:
            pass

    if parts[17]:
        try:
            gps_data.vdop = float(parts[17].split("*")[0])
        except ValueError:
            pass
