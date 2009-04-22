
# Copyright 2007 ZXing authors
# 
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#package com.google.zxing.common

#/**
# * <p>This provides an easy abstraction to read bits at a time from a sequence of bytes, where the
# * number of bits read is not often a multiple of 8.</p>
# *
# * <p>This class is not thread-safe.</p>
# *
# * @author Sean Owen
# */
class BitSource:


#    /**
#     * @param bytes bytes from which this will read bits. Bits will be read from the first byte first.
#     * Bits are read within a byte from most-significant to least-significant bit.
#     */
    def __init__(self, byts):
        self.byts = byts
        self.byteOffset = 0
        self.bitOffset = 0

#    /**
#     * @param numBits number of bits to read
#     * @return int representing the bits read. The bits will appear as the least-significant
#     *         bits of the int
#     * @throws IllegalArgumentException if numBits isn't in [1,32]
#     */
    def readBits(self, numBits):
        if (numBits < 1 or numBits > 32):
            raise IllegalArgumentException()

        result = 0

        # First, read remainder from current byte
        if (self.bitOffset > 0):
            bitsLeft = 8 - self.bitOffset
            toRead = numBits if numBits < bitsLeft else bitsLeft
            bitsToNotRead = bitsLeft - toRead
            mask = (0xFF >> (8 - toRead)) << bitsToNotRead
            result = (ord(self.byts[self.byteOffset]) & mask) >> bitsToNotRead
            numBits -= toRead
            self.bitOffset += toRead
            if (self.bitOffset == 8):
                self.bitOffset = 0
                self.byteOffset+=1

        # Next read whole bytes
        if (numBits > 0):
            while (numBits >= 8):
                result = (result << 8) | (ord(self.byts[self.byteOffset]) & 0xFF)
                self.byteOffset+=1
                numBits -= 8

            # Finally read a partial byte
            if (numBits > 0):
                bitsToNotRead = 8 - numBits
                mask = (0xFF >> bitsToNotRead) << bitsToNotRead
                result = (result << numBits) | ((ord(self.byts[self.byteOffset]) & mask) >> bitsToNotRead)
                self.bitOffset += numBits

        return result

#    /**
#     * @return number of bits that can be read successfully
#     */
    def available(self):
        return 8 * (len(self.byts) - self.byteOffset) - self.bitOffset
