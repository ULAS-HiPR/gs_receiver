import struct


MAGIC = b"OG"
VERSION = 1
TYPE_CAN_BUNDLE = 1
TYPE_GPS = 2
TYPE_TEST = 0x7F
HEADER_SIZE = 12
CRC_SIZE = 2
CAN_RECORD_SIZE = 11


def crc16_ccitt(data):
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def decode_packet(packet):
    if not isinstance(packet, (bytes, bytearray)) or len(packet) < HEADER_SIZE + CRC_SIZE:
        raise ValueError("packet too short")
    if bytes(packet[0:2]) != MAGIC:
        raise ValueError("bad magic")
    if packet[2] != VERSION:
        raise ValueError("unsupported version")

    received_crc = struct.unpack("<H", bytes(packet[-2:]))[0]
    calculated_crc = crc16_ccitt(packet[:-2])
    if received_crc != calculated_crc:
        raise ValueError("bad CRC")

    packet_type = packet[3]
    sequence = struct.unpack("<H", bytes(packet[4:6]))[0]
    uptime_ms = struct.unpack("<I", bytes(packet[6:10]))[0]
    record_count = packet[10]
    flags = packet[11]
    payload = packet[HEADER_SIZE:-CRC_SIZE]
    result = {
        "type": packet_type,
        "sequence": sequence,
        "uptime_ms": uptime_ms,
        "flags": flags,
    }

    if packet_type == TYPE_CAN_BUNDLE:
        if record_count == 0 or len(payload) != record_count * CAN_RECORD_SIZE:
            raise ValueError("bad CAN bundle length")
        records = []
        for index in range(record_count):
            offset = index * CAN_RECORD_SIZE
            can_id = struct.unpack("<H", bytes(payload[offset : offset + 2]))[0]
            dlc = payload[offset + 2]
            if can_id > 0x7FF or dlc > 8:
                raise ValueError("bad CAN record")
            records.append({
                "id": can_id,
                "dlc": dlc,
                "data": bytes(payload[offset + 3 : offset + 11]),
            })
        result["records"] = records
        return result

    if packet_type == TYPE_GPS:
        if record_count != 1 or len(payload) != 14:
            raise ValueError("bad GPS packet length")
        lat, lon, altitude_dm, velocity_dm_s, satellites, valid = struct.unpack("<iihhBB", bytes(payload))
        result.update({
            "latitude_deg": lat / 10000000.0,
            "longitude_deg": lon / 10000000.0,
            "altitude_m": altitude_dm / 10.0,
            "velocity_m_s": velocity_dm_s / 10.0,
            "satellites": satellites,
            "fix": bool(valid),
        })
        return result

    if packet_type == TYPE_TEST:
        if len(payload) != 4:
            raise ValueError("bad test packet length")
        result["counter"] = struct.unpack("<I", bytes(payload))[0]
        return result

    raise ValueError("unknown packet type")
