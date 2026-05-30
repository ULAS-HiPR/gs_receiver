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
        self.message_buffer = ""
        self.last_data_time = time.monotonic()
        self.timeout_s = 0.5  # 500ms timeout between message parts
        self.current_data = GPSData()
        self.has_new_data = False

    def update(self):
        """Check for new GPS data - non-blocking"""
        self.has_new_data = False
        now = time.monotonic()

        # Check if timeout occurred with data in buffer
        if (now - self.last_data_time) > self.timeout_s and self.message_buffer:
            self._process_buffer()
            self.has_new_data = True

        # Check if new data is available
        # CircuitPython uses in_waiting instead of any()
        bytes_available = self.uart.in_waiting
        if bytes_available > 0:
            try:
                raw = self.uart.read(bytes_available)
                if raw:
                    data = raw.decode("utf-8")

                    if not self.message_buffer or (now - self.last_data_time) <= self.timeout_s:
                        self.message_buffer += data
                    else:
                        self._process_buffer()
                        self.message_buffer = data
                        self.has_new_data = True

                    self.last_data_time = now
            except Exception as e:
                print(f"GPS read error: {e}")

        return self.has_new_data

    def get_data(self):
        """Update and return current GPS data"""
        self.update()
        return self.current_data

    def _process_buffer(self):
        """Parse all NMEA sentences in the buffer"""
        if not self.message_buffer:
            return
        self.current_data = _process_nmea_data(self.message_buffer)
        self.message_buffer = ""


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
