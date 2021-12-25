import machine
import time


# Based on https://github.com/drakxtwo/vl53l1x_pico
# Copyright (c) 2021 Lee Halls
# MIT License
class VL53L1X:
    default_configuration = bytes([
        0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x02, 0x08,
        0x00, 0x08, 0x10, 0x01, 0x01, 0x00, 0x00, 0x00,
        0x00, 0xff, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x20, 0x0b, 0x00, 0x00, 0x02, 0x0a, 0x21,
        0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0xc8,
        0x00, 0x00, 0x38, 0xff, 0x01, 0x00, 0x08, 0x00,
        0x00, 0x01, 0xdb, 0x0f, 0x01, 0xf1, 0x0d, 0x01,
        0x68, 0x00, 0x80, 0x08, 0xb8, 0x00, 0x00, 0x00,
        0x00, 0x0f, 0x89, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x01, 0x0f, 0x0d, 0x0e, 0x0e, 0x00,
        0x00, 0x02, 0xc7, 0xff, 0x9B, 0x00, 0x00, 0x00,
        0x01, 0x01, 0x40
    ])

    def __init__(self, i2c, address=0x29):
        self.i2c = i2c
        self.address = address
        self.reset()
        machine.lightsleep(1)
        if self.read_model_id() != 0xEACC:
            raise RuntimeError('Failed to find expected ID register values. Check wiring!')
        self.i2c.writeto_mem(self.address, 0x2D, self.default_configuration, addrsize=16)
        self.write_reg_16bit(0x001E, self.read_reg_16bit(0x0022) * 4)
        machine.lightsleep(200)

    def write_reg(self, reg, value):
        return self.i2c.writeto_mem(self.address, reg, bytes([value]), addrsize=16)

    def write_reg_16bit(self, reg, value):
        return self.i2c.writeto_mem(self.address, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]), addrsize=16)

    def read_reg_16bit(self, reg):
        data = self.i2c.readfrom_mem(self.address, reg, 2, addrsize=16)
        return (data[0] << 8) + data[1]

    def read_model_id(self):
        return self.read_reg_16bit(0x010F)

    def reset(self):
        self.write_reg(0x0000, 0x00)
        machine.lightsleep(100)
        self.write_reg(0x0000, 0x01)

    def read(self):
        data = self.i2c.readfrom_mem(self.address, 0x0089, 17, addrsize=16)
        final_crosstalk_corrected_range_mm_sd0 = (data[13] << 8) + data[14]
        return final_crosstalk_corrected_range_mm_sd0


class AQM1602:
    """
    Based on https://akizukidenshi.com/catalog/g/gP-08779/
    """

    DEFAULT_ADDRESS = 0x3E

    def __init__(self, i2c_bus, address=DEFAULT_ADDRESS):
        self.i2c = i2c_bus
        self.address = address
        time.sleep_ms(100)
        self.write_cmd(0x38)
        time.sleep_ms(20)
        self.write_cmd(0x39)
        time.sleep_ms(20)
        self.write_cmd(0x14)
        time.sleep_ms(20)
        self.write_cmd(0x73)
        time.sleep_ms(20)
        self.write_cmd(0x56)
        time.sleep_ms(20)
        self.write_cmd(0x6C)
        time.sleep_ms(20)
        self.write_cmd(0x38)
        time.sleep_ms(20)
        self.write_cmd(0x01)
        time.sleep_ms(20)
        self.write_cmd(0x0C)
        time.sleep_ms(20)

    def write_data(self, data):
        self.i2c.writeto_mem(self.address, 0x40, bytes([data & 0xFF]), addrsize=8)
        time.sleep_ms(1)

    def write_cmd(self, cmd):
        self.i2c.writeto_mem(self.address, 0x00, bytes([cmd & 0xFF]), addrsize=8)
        time.sleep_ms(1)

    def print(self, line_no, lin):
        buf = bytearray(lin)
        if len(buf) <= 0:
            return
        if len(buf) > 16:
            buf = buf[0:16]
        if line_no == 0:
            self.write_cmd(0x01)
            self.write_cmd(0x80)
        else:
            self.write_cmd(0x02)
            self.write_cmd(0xC0)
        for idx in range(0, len(buf)):
            self.write_data(buf[idx])


if __name__ == "__main__":
    # I2C #0: VL53L1X
    i2c0 = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=100000)
    distance = VL53L1X(i2c0)
    print("i2c0 scan result:", i2c0.scan())

    # I2C #1: LCD
    i2c1 = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), freq=100000)
    print("i2c1 scan result:", i2c1.scan())
    lcd = AQM1602(i2c1)
    lcd.print(0, "VL54L1X for Nano")
    lcd.print(1, "READY")

    while True:
        print("range: mm ", distance.read())
        lcd.print(0, str(distance.read()) + "mm")
        lcd.print(1, "")
        time.sleep_ms(500)
