#!/usr/bin/env python3

# adapted from https://github.com/adambartyzal/labelprint/blob/main/labelprint.py

import datetime
import socket

from PIL import Image, ImageDraw, ImageFont

HOST = "10.10.10.31"
PORT = 9100
text = datetime.date.today().isoformat()

label_height = 64

text_size = 24
text_border_width = 10

label_length = int(2 * text_border_width + ((len(text)) * (text_size) * 0.6))

label = Image.new('1', (label_length, label_height), color = 1)

fnt = ImageFont.truetype('./RobotoMono-Regular.ttf', text_size)
d = ImageDraw.Draw(label)
d.text((text_border_width, 15), text, font=fnt, color = 1)

label = label.rotate(270, expand=1)

image_data = bytearray(label.tobytes())

for i in range(len(image_data)):
  image_data[i] = -image_data[i] + 255 # invert colors

data = b'\x00' * 100
data += b'\x1B\x40' # print start
data += b'\x1B\x69\x4D\x40' # pre-cut
data += b'\x1B\x69\x4B\x08' # end cut
data += b'\x4d\x02' # compression

for line in range(label_length):
    data_start = int(line * (label_height / 8))
    data_end = int(data_start + (label_height / 8) - 1)
    lower_padding = int((16 - label_height / 8) / 2)
    upper_padding = int((16 - label_height / 8) - lower_padding)
    image_part = image_data[data_start:data_end+1] # cut one line of the image
    binary = bin(int(image_part.hex(), 16))[2:].zfill(64) # bytes to binary str
    reversed = int(binary[::-1], 2).to_bytes(len(binary) // 8, byteorder='big') # reverse bit order and convert back to bytes
    data_part = b'\x47\x11\x00\x0F' + b'\x00' * lower_padding + reversed + b'\x00' * upper_padding # line data for printer
    data += data_part
data += b'\x1A' # print end

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(data)
