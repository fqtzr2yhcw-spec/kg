"""Contact sheet: four massing views with a title and notes."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
d, out, title, notes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split("|")
views = [("hero", "Front three-quarter"), ("front", "Front"), ("rear", "Rear three-quarter"), ("aerial", "Aerial")]
ims = [Image.open(os.path.join(d, v + ".png")).convert("RGB") for v, _ in views]
W, H = 1000, int(ims[0].height * 1000 / ims[0].width)
F = "/usr/share/fonts/truetype/dejavu/"
ft = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 40)
fs = ImageFont.truetype(F + "DejaVuSans.ttf", 24)
fl = ImageFont.truetype(F + "DejaVuSans-Bold.ttf", 22)
head = 80 + 34 * len(notes) + 20
sheet = Image.new("RGB", (2 * W + 30, head + 2 * H + 20), "white")
dr = ImageDraw.Draw(sheet)
dr.text((20, 18), title, font=ft, fill="#222")
for i, n in enumerate(notes):
    dr.text((24, 80 + 34 * i), "• " + n, font=fs, fill="#333")
for i, (im, (v, lab)) in enumerate(zip(ims, views)):
    x, y = 10 + (i % 2) * (W + 10), head + (i // 2) * (H + 0)
    sheet.paste(im.resize((W, H)), (x, y))
    dr.text((x + 14, y + 10), lab, font=fl, fill="#222")
sheet.save(out)
print(out, sheet.size)
