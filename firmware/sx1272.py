import time
import digitalio


class SX1272:
    REG_FIFO = 0x00
    REG_OP_MODE = 0x01
    REG_FRF_MSB = 0x06
    REG_PA_CONFIG = 0x09
    REG_LNA = 0x0C
    REG_FIFO_ADDR_PTR = 0x0D
    REG_FIFO_RX_BASE_ADDR = 0x0F
    REG_FIFO_RX_CURRENT_ADDR = 0x10
    REG_IRQ_FLAGS = 0x12
    REG_RX_NB_BYTES = 0x13
    REG_PKT_SNR_VALUE = 0x19
    REG_PKT_RSSI_VALUE = 0x1A
    REG_MODEM_CONFIG_1 = 0x1D
    REG_MODEM_CONFIG_2 = 0x1E
    REG_PREAMBLE_MSB = 0x20
    REG_PAYLOAD_LENGTH = 0x22
    REG_SYNC_WORD = 0x39
    REG_DIO_MAPPING_1 = 0x40
    REG_VERSION = 0x42

    IRQ_RX_DONE = 0x40
    IRQ_PAYLOAD_CRC_ERROR = 0x20
    MODE_SLEEP = 0x00
    MODE_STDBY = 0x01
    MODE_RX_CONTINUOUS = 0x05
    LONG_RANGE_MODE = 0x80
    EXPECTED_VERSION = 0x22

    def __init__(self, spi, cs_pin, reset_pin, rx_switch_pin, tx_switch_pin):
        self.spi = spi
        self.cs = self._output(cs_pin, True)
        self.reset_pin = self._output(reset_pin, False)
        self.rx_switch = self._output(rx_switch_pin, False)
        self.tx_switch = self._output(tx_switch_pin, False)
        self.last_rssi_dbm = None
        self.last_snr_db = None
        self.last_error = None

    @staticmethod
    def _output(pin, value):
        output = digitalio.DigitalInOut(pin)
        output.direction = digitalio.Direction.OUTPUT
        output.value = value
        return output

    def _lock(self):
        while not self.spi.try_lock():
            pass
        self.spi.configure(baudrate=4000000, polarity=0, phase=0)

    def _read_register(self, address):
        tx = bytearray((address & 0x7F, 0))
        rx = bytearray(2)
        self._lock()
        try:
            self.cs.value = False
            self.spi.write_readinto(tx, rx)
        finally:
            self.cs.value = True
            self.spi.unlock()
        return rx[1]

    def _write_register(self, address, value):
        data = bytearray((address | 0x80, value & 0xFF))
        self._lock()
        try:
            self.cs.value = False
            self.spi.write(data)
        finally:
            self.cs.value = True
            self.spi.unlock()

    def _set_mode(self, mode):
        current = self._read_register(self.REG_OP_MODE)
        self._write_register(self.REG_OP_MODE, (current & 0xF8) | self.LONG_RANGE_MODE | mode)

    def _set_switch_rx(self):
        self.tx_switch.value = False
        self.rx_switch.value = True

    def reset(self):
        self.reset_pin.value = True
        time.sleep(0.01)
        self.reset_pin.value = False
        time.sleep(0.01)

    def init(self, frequency_hz=868000000, spreading_factor=7):
        try:
            self.reset()
            self.rx_switch.value = False
            self.tx_switch.value = False
            if self._read_register(self.REG_VERSION) != self.EXPECTED_VERSION:
                raise RuntimeError("SX1272 version mismatch")
            self._write_register(self.REG_OP_MODE, self.LONG_RANGE_MODE | self.MODE_SLEEP)
            time.sleep(0.01)
            self._set_mode(self.MODE_STDBY)
            frf = (frequency_hz << 19) // 32000000
            self._write_register(self.REG_FRF_MSB, (frf >> 16) & 0xFF)
            self._write_register(self.REG_FRF_MSB + 1, (frf >> 8) & 0xFF)
            self._write_register(self.REG_FRF_MSB + 2, frf & 0xFF)
            self._write_register(self.REG_FIFO_RX_BASE_ADDR, 0)
            self._write_register(self.REG_LNA, 0x23)
            self._write_register(self.REG_MODEM_CONFIG_1, (0 << 6) | (1 << 3) | 0x02)
            self._write_register(self.REG_MODEM_CONFIG_2, (spreading_factor << 4) | 0x04)
            self._write_register(self.REG_PREAMBLE_MSB, 0)
            self._write_register(self.REG_PREAMBLE_MSB + 1, 8)
            self._write_register(self.REG_SYNC_WORD, 0x12)
            self._write_register(self.REG_DIO_MAPPING_1, 0)
            self._write_register(self.REG_PAYLOAD_LENGTH, 0)
            self._write_register(self.REG_IRQ_FLAGS, 0xFF)
            self._set_switch_rx()
            self._set_mode(self.MODE_RX_CONTINUOUS)
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = str(exc)
            self.rx_switch.value = False
            self.tx_switch.value = False
            return False

    def _read_fifo(self, length):
        result = bytearray(length)
        self._lock()
        try:
            self.cs.value = False
            self.spi.write(bytearray((self.REG_FIFO,)))
            self.spi.readinto(result)
        finally:
            self.cs.value = True
            self.spi.unlock()
        return bytes(result)

    def receive(self):
        flags = self._read_register(self.REG_IRQ_FLAGS)
        if flags & self.IRQ_PAYLOAD_CRC_ERROR:
            self._write_register(self.REG_IRQ_FLAGS, self.IRQ_RX_DONE | self.IRQ_PAYLOAD_CRC_ERROR)
            self.last_error = "radio CRC"
            return None
        if not flags & self.IRQ_RX_DONE:
            return None

        length = self._read_register(self.REG_RX_NB_BYTES)
        address = self._read_register(self.REG_FIFO_RX_CURRENT_ADDR)
        self._write_register(self.REG_FIFO_ADDR_PTR, address)
        packet = self._read_fifo(length)
        self._write_register(self.REG_IRQ_FLAGS, self.IRQ_RX_DONE)
        self.last_rssi_dbm = self._read_register(self.REG_PKT_RSSI_VALUE) - 139
        raw_snr = self._read_register(self.REG_PKT_SNR_VALUE)
        if raw_snr & 0x80:
            raw_snr -= 256
        self.last_snr_db = raw_snr / 4.0
        self.last_error = None
        return packet
