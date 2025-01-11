"""
    A fork of Szymon Jakubiak's library, written for the Raspberry Pi Pico running MicroPython.
    I highly recommend downloading a copy of the SPS30 datasheet from Sensirion's website if
    you wish to use/understand this library.

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

"""

import struct, time

class SPS30:
    def __init__(self, selectUART):
        self.uart = machine.UART(selectUART, 115200, parity=None, stop=1, timeout=2)
        #The RPi Pico has two UART interfaces, 0 and 1.

        self.led = machine.Pin(25, machine.Pin.OUT)
        #Uses the build-in LED to indicate activity.

    def send(self, txCommand, txParam):
        txParamLength = len(txParam).to_bytes(1,"big")

        buildFrame = b'\x00'

        buildFrame += txCommand + txParamLength + txParam
        #At this point, the frame is partially built. It has the address (always 0x00), the SHDLC command (txCommand),
        #the command parameter length (txParamLength), and the command parameter (txParam).

        sumOfAllBytes = 0

        for i in buildFrame:
            sumOfAllBytes += i

        calculatedChecksum = (sumOfAllBytes & 0b11111111) ^ 0b11111111
        #Per the datasheet, the checksum is built before byte-stuffing. All bytes in the frame are added together.
        #The least significant byte of the result is inverted, yielding the checksum.

        buildFrame += calculatedChecksum.to_bytes(1,"big")

        buildFrame = buildFrame.replace(b'\x7D', b'\x7D\x5D')

        buildFrame = buildFrame.replace(b'\x7E', b'\x7D\x5E')

        buildFrame = buildFrame.replace(b'\x11', b'\x7D\x31')
        
        buildFrame = buildFrame.replace(b'\x13', b'\x7D\x33')
        #Byte-stuffing (essentially escape codes). Prevents special bytes appearing legitimately within the frame data.

        buildFrame  = b'\x7E' + buildFrame + b'\x7E'
        #Add the start/stop bytes at either end of the frame. The frame is now complete.

        self.uart.write(buildFrame)

    def read(self):

        inputBytes = self.uart.read()

        if inputBytes == None:
            return [None, None]
        #If nothing is read from the UART buffer, return None.

        inputBytes = inputBytes[1:-1]
        #Trim the start/stop bytes.

        inputBytes = inputBytes.replace(b'\x7D\x5E', b'\x7E')
        
        inputBytes = inputBytes.replace(b'\x7D\x31', b'\x11')

        inputBytes = inputBytes.replace(b'\x7D\x33', b'\x13')

        inputBytes = inputBytes.replace(b'\x7D\x5D', b'\x7D')
        #Reverse byte-stuffing, as above.

        allegedChecksum = inputBytes[-1]

        sumOfAllBytes = 0

        for i in inputBytes[0:-1]:
            sumOfAllBytes += i

        calcuatedChecksum = (sumOfAllBytes & 0b11111111) ^ 0b11111111

        if allegedChecksum != calcuatedChecksum:
            return [None, None]
        #Verifies our own checksum calculation against the value provided by the SPS30. Returns None if mismatch.

        stateByte = inputBytes[2]

        lengthByte = inputBytes[3]

        if lengthByte != 0:
            rxData = inputBytes[4:-1]
        else:
            rxData = 0
        #If lengthByte is zero, the SPS30 returned an empty frame.

        return [rxData, stateByte]

    def start(self):
        self.self.led.toggle()
    
        self.uart.read()
        #Flush buffer.

        self.send(b'\x00', b'\x01\x03')

        time.sleep(0.030)
        #Per the datasheet, most SHDLC commands have a maximum response time of 20ms. To be sure, we're waiting 30ms.

        returnData = self.read()
        #The SPS30 will only return an empty frame for this command, but the state byte is worth getting.

        self.led.toggle()

        return returnData[1]

    def stop(self):
        self.led.toggle()

        self.uart.read()

        self.send(b'\x01', b'')

        time.sleep(0.030)

        returnData = self.read()

        self.led.toggle()

        return returnData[1]

    def read_values(self):
        self.led.toggle()

        self.uart.read()

        self.send(b'\x03', b'')

        time.sleep(0.030)

        returnData = self.read()

        try:
            values = struct.unpack(">ffffffffff", returnData[0])

        except:

            values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        #Unpack returned bytes into an array of floating point numbers.

        self.led.toggle()

        return [values, returnData[1]]

    def sleep(self):
        self.led.toggle()
        
        self.uart.read()

        self.send(b'\x10', b'')

        time.sleep(0.030)

        returnData = self.read()

        self.led.toggle()

        return returnData[1]

    def wake(self):
        self.led.toggle()

        self.uart.read()

        self.send(b'\x11', b'')

        self.uart.read()

        time.sleep(0.030)

        self.send(b'\x11', b'')
        #Per the datasheet, sending this command twice within 100ms will wake-up the UART interface.

        returnData = self.read()

        self.led.toggle()

        return returnData[1]

    def trigger_fan_clean(self):
        self.led.toggle()

        self.uart.read()

        self.send(b'\x56', b'')

        time.sleep(0.030)

        returnData = self.read()

        self.led.toggle()

        return returnData[1]

    def read_cleaning_interval(self):
        #This doesn't work yet.

        self.led.toggle()

        self.uart.read()

        self.send(b'\x80',b'\x00')

        time.sleep(0.030)

        returnData = self.read()

        self.led.toggle()

        return [returnData[0], returnData[1]]
    
    def device_info(self, requestedInfo):
        self.led.toggle()

        self.uart.read()

        if requestedInfo == "productType":
            self.send(b'\xD0', b'\x00')
        
        elif requestedInfo == "serialNumber":
            self.send(b'\xD0', b'\x03')

        time.sleep(0.030)

        returnData = self.read()
        
        values = returnData[0]

        values = values[0:-1].decode('ascii')

        self.led.toggle()

        return [values, returnData[1]]

    def read_version(self):
        self.led.toggle()

        self.uart.read()

        self.send(b'\xD1',b'')

        time.sleep(0.030)

        returnData = self.read()

        versionsPreSplit = returnData[0]

        firmwareVer = str(versionsPreSplit[0]) + "." + str(versionsPreSplit[1])

        hardwareRev = str(versionsPreSplit[3])

        SHDLCVer = str(versionsPreSplit[5]) + "." + str(versionsPreSplit[6])

        self.led.toggle()

        return [[firmwareVer, hardwareRev, SHDLCVer], returnData[1]]

    def read_register(self, toClear):
        self.led.toggle()
        
        self.uart.read()

        if toClear == True:
            self.send(b'\xD2',b'\x01')

        else:
            self.send(b'\xD2',b'\x00')

        time.sleep(0.030)

        returnData = self.read()

        registerData = returnData[0]

        registerData = struct.unpack("bbbb", registerData)

        self.led.toggle()

        return [registerData, returnData[1]]

    def reset(self):
        self.led.toggle()
        
        self.uart.read()

        self.send(b'\xD3', b'')

        time.sleep(0.030)

        returnData = self.read()

        self.led.toggle()

        return returnData[1]
