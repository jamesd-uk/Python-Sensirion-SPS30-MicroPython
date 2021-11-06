"""
    Library to read data from Sensirion SPS30 particulate matter sensor

    by
    Szymon Jakubiak
    Twitter: @SzymonJakubiak
    LinkedIn: https://pl.linkedin.com/in/szymon-jakubiak

    MIT License

    Copyright (c) 2018 Szymon Jakubiak
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    Units for measurements:
        PM1, PM2.5, PM4 and PM10 are in ug/m^3, number concentrations are in #/cm^3
"""
import struct

class SPS30:
    def __init__(self, selectUART):

        self.uart = machine.UART(selectUART, 115200, parity=None, stop=1, timeout=2)
    
    def start(self):

        self.uart.write(b'\x7E\x00\x00\x02\x01\x03\xF9\x7E')
        
    def stop(self):

        self.uart.write(b'\x7E\x00\x01\x00\xFE\x7E')
    
    def read_values(self):

        self.uart.read()

        self.uart.write(b'\x7E\x00\x03\x00\xFC\x7E')

        raw = self.reverse_byte_stuffing(self.uart.read())

        rawData = raw[5:-2]
        
        try:

            data = struct.unpack(">ffffffffff", rawData)

        except struct.error:

            data = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        return data
    
    def read_serial_number(self):

        self.uart.read()

        self.uart.write(b'\x7E\x00\xD0\x01\x03\x2B\x7E')

        raw = self.reverse_byte_stuffing(self.uart.read())
        
        serial_number = raw[5:-3].decode('ascii')

        return serial_number

    def trigger_fan_clean(self):

        self.uart.read()

        self.uart.write(b'\x7E\x00\x56\x00\xA9\x7E')

        return

    def sleep(self):

        self.uart.read()

        self.uart.write(b'\x7E\x00\x10\x00\xEF\x7E')

        return

    def wake(self):

        self.uart.read()

        self.uart.write(b'\xFF')

        self.uart.write(b'\x7E\x00\x11\x00\xEE\x7E')

        raw = self.reverse_byte_stuffing(self.uart.read())

        return raw
    

    def read_firmware_version(self):

        self.uart.read()

        self.uart.write(b'\x7E\x00\xD1\x00\x2E\x7E')

        raw = self.reverse_byte_stuffing(self.uart.read())

        data = raw[5:-2]

        data = struct.unpack(">bbbbbbb", data)

        firmware_version = str(data[0]) + "." + str(data[1])

        return firmware_version

    def reverse_byte_stuffing(self, raw):

        if b'\x7D\x5E' in raw:

            raw = raw.replace(b'\x7D\x5E', b'\x7E')

        if b'\x7D\x5D' in raw:

            raw = raw.replace(b'\x7D\x5D', b'\x7D')

        if b'\x7D\x31' in raw:

            raw = raw.replace(b'\x7D\x31', b'\x11')

        if b'\x7D\x33' in raw:
            
            raw = raw.replace(b'\x7D\x33', b'\x13')

        return raw