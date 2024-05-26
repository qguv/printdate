#!/usr/bin/env python3

# adapted from https://github.com/adambartyzal/labelprint/blob/main/labelprint.py

import datetime
import socket
import struct
import math

import packbits
from PIL import Image, ImageDraw, ImageFont

HOST = "10.10.10.31"
PORT = 9100
text = datetime.date.today().isoformat()
label_height = 64

def encode_raster_transfer(data):
    """ Encode 1 bit per pixel image data for transfer over serial to the printer """
    buf = bytearray()

    # Send in chunks of 1 line (128px @ 1bpp = 16 bytes)
    # This mirrors the official app from Brother. Other values haven't been tested.
    chunk_size = math.ceil(label_height / 8)

    for i in range(0, len(data), chunk_size):
        print("chunk", i)
        chunk = data[i : i + chunk_size]

        # Encode as tiff
        packed_chunk = packbits.encode(chunk)

        # Write header
        buf.extend(TRANSFER_COMMAND)

        # Write number of bytes to transfer (n1 + n2*256)
        length = len(packed_chunk)
        buf.extend(unsigned_char.pack( int(length % 256) ))
        buf.extend(unsigned_char.pack( int(length / 256) ))

        # Write data
        buf.extend(packed_chunk)

    return buf

TRANSFER_COMMAND = b"\x47"
unsigned_char = struct.Struct('B')

text_size = 24
text_border_width = 10

label_length = int(2 * text_border_width + len(text) * text_size * 0.6)

label = Image.new('1', (label_length, label_height), color = 1)

fnt = ImageFont.truetype('./RobotoMono-Regular.ttf', text_size)
d = ImageDraw.Draw(label)
d.text((text_border_width, 15), text, font=fnt, color = 1)

label = label.rotate(270, expand=1)

image_data = bytearray(label.tobytes())

label.save('image.jpg')  # DEBUG
with open('image_data', 'w') as f:  # DEBUG
    f.buffer.write(image_data)  # DEBUG

# invert colors
for i in range(len(image_data)):
  image_data[i] = 255 - image_data[i]

data = b'\x00' * 100
data += b'\x1B\x40'  # print start
data += b'\x1B\x69\x4D\x40'  # pre-cut
data += b'\x1B\x69\x4B\x08'  # end cut
data += b'\x4d\x02'  # TIFF compression

data += encode_raster_transfer(data)

data += b'\x1A'  # print end
data += b'\x1b\x40'  # reinitialize

with open('sent', 'w') as f:  # DEBUG
    f.buffer.write(data)  # DEBUG

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(data)
