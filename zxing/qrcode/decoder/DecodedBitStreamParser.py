#/*
# * Copyright 2007 ZXing authors
# *
# * Licensed under the Apache License, Version 2.0 (the "License")
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *      http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# */
#
###package com.google.zxing.qrcode.decoder
#
###import com.google.zxing.ReaderException
from zxing.ReaderException import ReaderException
###import com.google.zxing.common.BitSource
from zxing.common.BitSource import BitSource
###import com.google.zxing.common.CharacterSetECI
from zxing.common.CharacterSetECI import CharacterSetECI
###import com.google.zxing.common.DecoderResult
from zxing.common.DecoderResult import DecoderResult
#
###import java.io.UnsupportedEncodingException
###import java.util.Vector
import sys
#
#/**
# * <p>QR Codes can encode text as bits in one of several modes, and can use multiple modes
# * in one QR Code. This class decodes the bits back into text.</p>
# *
# * <p>See ISO 18004:2006, 6.4.3 - 6.4.7</p>
# *
# * @author Sean Owen
# */
class DecodedBitStreamParser:

#    /**
#     * See ISO 18004:2006, 6.4.4 Table 5
#     */
    ALPHANUMERIC_CHARS = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B',
        'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
        'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        ' ', '$', '%', '*', '+', '-', '.', '/', ':'
        ]
    SHIFT_JIS = "SJIS"
    EUC_JP = "EUC_JP"
    UTF8 = "UTF8"
    ISO88591 = "ISO8859_1"

    platformDefault = sys.getfilesystemencoding()
    ASSUME_SHIFT_JIS = SHIFT_JIS.lower()==platformDefault.lower() or EUC_JP.lower()==platformDefault.lower()

    def __init__(self):
        pass

    def decode(self, byts, version):
        bits = BitSource(byts)
        result = ''
        ###CharacterSetECI currentCharacterSetECI = None
        fc1InEffect = False
        ###Vector byteSegments = new Vector(1)
        ###Mode mode
        while True:
            # While still another segment to read...
            if (bits.available() < 4):
                # OK, assume we're done. Really, a TERMINATOR mode should have been recorded here
                mode = Mode.TERMINATOR
            else:
                try:
                    mode = Mode.forBits(bits.readBits(4)); # mode is encoded by 4 bits
                except IllegalArgumentException as iae:
                    raise ReaderException.getInstance()
            if (not mode.equals(Mode.TERMINATOR)):
                if (mode.equals(Mode.FNC1_FIRST_POSITION) or mode.equals(Mode.FNC1_SECOND_POSITION)):
                    # We do little with FNC1 except alter the parsed result a bit according to the spec
                    fc1InEffect = True
                elif (mode.equals(Mode.STRUCTURED_APPEND)):
                    # not really supported; all we do is ignore it
                    # Read next 8 bits (symbol sequence #) and 8 bits (parity data), then continue
                    bits.readBits(16)
                elif (mode.equals(Mode.ECI)):
                    # Count doesn't apply to ECI
                    value = parseECIValue(bits)
                    currentCharacterSetECI = CharacterSetECI.getCharacterSetECIByValue(value)
                    if (currentCharacterSetECI == None):
                        raise ReaderException.getInstance()
                else:
                    # How many characters will follow, encoded in this mode?
                    count = bits.readBits(mode.getCharacterCountBits(version))
                    if (mode.equals(Mode.NUMERIC)):
                        decodeNumericSegment(bits, result, count)
                    elif (mode.equals(Mode.ALPHANUMERIC)):
                        decodeAlphanumericSegment(bits, result, count, fc1InEffect)
                    elif (mode.equals(Mode.BYTE)):
                        decodeByteSegment(bits, result, count, currentCharacterSetECI, byteSegments)
                    elif (mode.equals(Mode.KANJI)):
                        decodeKanjiSegment(bits, result, count)
                    else:
                        raise ReaderException.getInstance()
            if (mode.equals(Mode.TERMINATOR)):
                break

        return DecoderResult(byts, str(result), None if byteSegments.isEmpty() else byteSegments)

    def decodeKanjiSegment(bits, result, count):
        # Each character will require 2 bytes. Read the characters as 2-byte pairs
        # and decode as Shift_JIS afterwards
        buffer = bytearray(2 * count)
        offset = 0
        while (count > 0):
            # Each 13 bits encodes a 2-byte character
            twoBytes = bits.readBits(13)
            assembledTwoBytes = ((twoBytes / 0x0C0) << 8) | (twoBytes % 0x0C0)
            if (assembledTwoBytes < 0x01F00):
                # In the 0x8140 to 0x9FFC range
                assembledTwoBytes += 0x08140
            else:
                # In the 0xE040 to 0xEBBF range
                assembledTwoBytes += 0x0C140
            buffer[offset] = (assembledTwoBytes >> 8)
            buffer[offset + 1] = assembledTwoBytes
            offset += 2
            count-=1
        # Shift_JIS may not be supported in some environments:
        try:
            result.append(buffer.decode(SHIFT_JIS))
        except UnsupportedEncodingException as uee:
            raise ReaderException.getInstance()

    def decodeByteSegment(bits, result, count, currentCharacterSetECI,
            byteSegments):
        readBytes = bytearray[count]
        if (count << 3 > bits.available()):
            raise ReaderException.getInstance()
        for i in range(count):
            readBytes[i] = bits.readBits(8)
        if (currentCharacterSetECI == None):
            # The spec isn't clear on this mode; see
            # section 6.4.5: t does not say which encoding to assuming
            # upon decoding. I have seen ISO-8859-1 used as well as
            # Shift_JIS -- without anything like an ECI designator to
            # give a hint.
            encoding = guessEncoding(readBytes)
        else:
            encoding = currentCharacterSetECI.getEncodingName()
        try:
            result.append(readBytes.decode(encoding))
        except UnsupportedEncodingException as uce:
            raise ReaderException.getInstance()
        byteSegments.addElement(readBytes)

    def decodeAlphanumericSegment(bits, result, count, fc1InEffect):
        # Read two characters at a time
        start = result.length()
        while (count > 1):
            nextTwoCharsBits = bits.readBits(11)
            result.append(ALPHANUMERIC_CHARS[int(nextTwoCharsBits / 45)])
            result.append(ALPHANUMERIC_CHARS[nextTwoCharsBits % 45])
            count -= 2
        if (count == 1):
            # special case: one character left
            result.append(ALPHANUMERIC_CHARS[bits.readBits(6)])
        # See section 6.4.8.1, 6.4.8.2
        if (fc1InEffect):
            # We need to massage the result a bit if in an FNC1 mode:
            #for (int i = start; i < result.length(); i++) {
            for i in range(start, result.length()):
                if (result.charAt(i) == '%'):
                    if (i < result.length() - 1 and result.charAt(i + 1) == '%'):
                        # %% is rendered as %
                        result.deleteCharAt(i + 1)
                    else:
                        # In alpha mode, % should be converted to FNC1 separator 0x1D
                        result.setCharAt(i, chr(0x1D))

    def decodeNumericSegment(bits, result, count):
        # Read three digits at a time
        while (count >= 3):
            # Each 10 bits encodes three digits
            threeDigitsBits = bits.readBits(10)
            if (threeDigitsBits >= 1000):
                raise ReaderException.getInstance()
            result.append(ALPHANUMERIC_CHARS[int(threeDigitsBits / 100)])
            result.append(ALPHANUMERIC_CHARS[int(threeDigitsBits / 10) % 10])
            result.append(ALPHANUMERIC_CHARS[threeDigitsBits % 10])
            count -= 3
        if (count == 2):
            # Two digits left over to read, encoded in 7 bits
            twoDigitsBits = bits.readBits(7)
            if (twoDigitsBits >= 100):
                raise ReaderException.getInstance()
            result.append(ALPHANUMERIC_CHARS[int(twoDigitsBits / 10)])
            result.append(ALPHANUMERIC_CHARS[twoDigitsBits % 10])
        elif (count == 1):
            # One digit left over to read
            digitBits = bits.readBits(4)
            if (digitBits >= 10):
                raise ReaderException.getInstance()
            result.append(ALPHANUMERIC_CHARS[digitBits])

    def guessEncoding(byts):
        if (ASSUME_SHIFT_JIS):
            return SHIFT_JIS
        # Does it start with the UTF-8 byte order mark? then guess it's UTF-8
        if (len(byts) > 3 and byts[0] == 0xEF and byts[1] == 0xBB and byts[2] == 0xBF):
            return UTF8
        # For now, merely tries to distinguish ISO-8859-1, UTF-8 and Shift_JIS,
        # which should be by far the most common encodings. ISO-8859-1
        # should not have bytes in the 0x80 - 0x9F range, while Shift_JIS
        # uses this as a first byte of a two-byte character. If we see this
        # followed by a valid second byte in Shift_JIS, assume it is Shift_JIS.
        # If we see something else in that second byte, we'll make the risky guess
        # that it's UTF-8.
        length = len(byts)
        canBeISO88591 = True
        canBeShiftJIS = True
        sawDoubleByteStart = False
        maybeSingleByteKatakanaCount = 0
        sawLatin1Supplement = False
        lastWasPossibleDoubleByteStart = False
        ###for (int i = 0; i < length and (canBeISO88591 or canBeShiftJIS); i++) {
        for i in range(length and (canBeISO88591 or canBeShiftJIS)):
            value = byts[i] & 0xFF
            if (value == 0xC2 or value == 0xC3 and i < length - 1):
                # This is really a poor hack. The slightly more exotic characters people might want to put in
                # a QR Code, by which I mean the Latin-1 supplement characters (e.g. u-umlaut) have encodings
                # that start with 0xC2 followed by [0xA0,0xBF], or start with 0xC3 followed by [0x80,0xBF].
                nextValue = byts[i + 1] & 0xFF
                if (nextValue <= 0xBF and ((value == 0xC2 and nextValue >= 0xA0) or (value == 0xC3 and nextValue >= 0x80))):
                    sawLatin1Supplement = True
            if (value >= 0x7F and value <= 0x9F):
                canBeISO88591 = False
            if (value >= 0xA1 and value <= 0xDF):
                # count the number of characters that might be a Shift_JIS single-byte Katakana character
                if (not lastWasPossibleDoubleByteStart):
                    maybeSingleByteKatakanaCount+=1
            if (not lastWasPossibleDoubleByteStart and ((value >= 0xF0 and value <= 0xFF) or value == 0x80 or value == 0xA0)):
                canBeShiftJIS = False
            if (((value >= 0x81 and value <= 0x9F) or (value >= 0xE0 and value <= 0xEF)) and i < length - 1):
                # These start double-byte characters in Shift_JIS. Let's see if it's followed by a valid
                # second byte.
                sawDoubleByteStart = True
                if (lastWasPossibleDoubleByteStart):
                    # If we just checked this and the last byte for being a valid double-byte
                    # char, don't check starting on this byte. If this and the last byte
                    # formed a valid pair, then this shouldn't be checked to see if it starts
                    # a double byte pair of course.
                    lastWasPossibleDoubleByteStart = False
                else:
                    # ... otherwise do check to see if this plus the next byte form a valid
                    # double byte pair encoding a character.
                    lastWasPossibleDoubleByteStart = True
                    nextValue = byts[i + 1] & 0xFF
                    if (nextValue < 0x40 or nextValue > 0xFC):
                        canBeShiftJIS = False
                    # There is some conflicting information out there about which bytes can follow which in
                    # double-byte Shift_JIS characters. The rule above seems to be the one that matches practice.
            else:
                lastWasPossibleDoubleByteStart = False
        # Distinguishing Shift_JIS and ISO-8859-1 can be a little tough. The crude heuristic is:
        # - If we saw
        #   - at least one byte that starts a double-byte value (bytes that are rare in ISO-8859-1), or
        #   - over 5% of bytes that could be single-byte Katakana (also rare in ISO-8859-1),
        # - and, saw no sequences that are invalid in Shift_JIS, then we conclude Shift_JIS
        if (canBeShiftJIS and (sawDoubleByteStart or 20 * maybeSingleByteKatakanaCount > length)):
            return SHIFT_JIS
        # Otherwise, we default to ISO-8859-1 unless we know it can't be
        if ((not sawLatin1Supplement) and canBeISO88591):
            return ISO88591
        # Otherwise, we take a wild guess with UTF-8
        return UTF8

    def parseECIValue(bits):
        firstByte = bits.readBits(8)
        if ((firstByte & 0x80) == 0):
            # just one byte
            return firstByte & 0x7F
        elif ((firstByte & 0xC0) == 0x80):
            # two bytes
            secondByte = bits.readBits(8)
            return ((firstByte & 0x3F) << 8) | secondByte
        elif ((firstByte & 0xE0) == 0xC0):
            # three bytes
            secondThirdBytes = bits.readBits(16)
            return ((firstByte & 0x1F) << 16) | secondThirdBytes
        raise TypeError("Bad ECI bits starting with byte " + firstByte)
