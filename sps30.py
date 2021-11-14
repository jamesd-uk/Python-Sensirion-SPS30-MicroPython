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
"""if buildCommand[-1] == 126 and buildCommand[0] == 126:"""

import struct, time

class SPS30:
    def __init__(self, selectUART):
        self.uart = machine.UART(selectUART, 115200, parity=None, stop=1, timeout=2)
    
    def start(self):
        self.uart.read()

        self.send(b'\x00', b'\x01\x03')

        time.sleep(0.030)

        returnData = self.read()

        return returnData[1]
        
    def stop(self):
        self.uart.read()

        self.send(b'\x01', b'')

        time.sleep(0.030)

        returnData = self.read()

        return returnData[1]

    def send(self, txCommand, txParam):      
        txParamLength = len(txParam).to_bytes(1,"big")

        buildCommand = b'\x00'

        buildCommand += txCommand + txParamLength + txParam

        sumOfAllBytes = 0

        for i in buildCommand:
            sumOfAllBytes += i

        calculatedChecksum = (sumOfAllBytes & 0b11111111) ^ 0b11111111

        buildCommand += calculatedChecksum.to_bytes(1,"big")

        if b'\x7E' in buildCommand:
            buildCommand = buildCommand.replace(b'\x7E', b'\x7D\x5E')

        if b'\x7D' in buildCommand:
            buildCommand = buildCommand.replace(b'\x7D', b'\x7D\x5D')

        if b'\x11' in buildCommand:
            buildCommand = buildCommand.replace(b'\x11', b'\x7D\x31')
        
        if b'\x13' in buildCommand:
            buildCommand = buildCommand.replace(b'\x13', b'\x7D\x33')

        buildCommand  = b'\x7E' + buildCommand + b'\x7E'

        self.uart.write(buildCommand)

    def read(self):
        inputBytes = self.uart.read()

        if inputBytes == None:
            return [None, None]

        inputBytes = inputBytes[1:-1]

        if b'\x7D\x5E' in inputBytes:
            inputBytes = inputBytes.replace(b'\x7D\x5E', b'\x7E')

        if b'\x7D\x5D' in inputBytes:
            inputBytes = inputBytes.replace(b'\x7D\x5D', b'\x7D')

        if b'\x7D\x31' in inputBytes:
            inputBytes = inputBytes.replace(b'\x7D\x31', b'\x11')
        
        if b'\x7D\x33' in inputBytes:
            inputBytes = inputBytes.replace(b'\x7D\x33', b'\x13')

        allegedChecksum = inputBytes[-1]

        sumOfAllBytes = 0

        for i in inputBytes[0:-1]:
            sumOfAllBytes += i

        calcuatedChecksum = (sumOfAllBytes & 0b11111111) ^ 0b11111111

        if allegedChecksum != calcuatedChecksum:
            return [None, None]

        stateByte = inputBytes[2]

        lengthByte = inputBytes[3]

        if lengthByte != 0:
            rxData = inputBytes[4:-1]
        else:
            rxData = 0

        return [rxData, stateByte]

    def get_values(self):
        self.uart.read()

        self.send(b'\x03', b'')

        time.sleep(0.030)

        returnData = self.read()

        if returnData[0] == None:
            values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        else:
            values = struct.unpack(">ffffffffff", returnData[0])

        return [values, returnData[1]]

    
    def device_info(self, requestedInfo):
        self.uart.read()

        if requestedInfo == "productType":
            self.send(b'\xD0', b'\x00')
        
        elif requestedInfo == "serialNumber":
            self.send(b'\xD0', b'\x03')

        time.sleep(0.030)

        returnData = self.read()
        
        values = returnData[0]

        values = values[0:-1].decode('ascii')

        return [values, returnData[1]]

    def trigger_fan_clean(self):
        self.uart.read()

        self.send(b'\x56', b'')

        time.sleep(0.030)

        returnData = self.read()

        return returnData[1]

    def sleep(self):
        self.uart.read()

        self.send(b'\x10', b'')

        time.sleep(0.030)

        returnData = self.read()

        return returnData[1]

    def soft_reset(self):
        self.uart.read()

        self.send(b'\xD3', b'')

        time.sleep(0.030)

        returnData = self.read()

        return returnData[1]

    def wake(self):
        self.uart.read()

        self.send(b'\x11', b'')

        time.sleep(0.030)

        self.send(b'\x11', b'')

        returnData = self.read()

        return returnData[1]

    def read_version(self):
        self.uart.read()

        self.send(b'\xD1',b'')

        time.sleep(0.030)

        returnData = self.read()

        versionsPreSplit = returnData[0]

        firmwareVer = str(versionsPreSplit[0]) + "." + str(versionsPreSplit[1])

        hardwareRev = str(versionsPreSplit[3])

        SHDLCVer = str(versionsPreSplit[5]) + "." + str(versionsPreSplit[6])

        return [[firmwareVer, hardwareRev, SHDLCVer], returnData[1]]