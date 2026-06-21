# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont
IMG = r"C:\dev\contest\제출본\img"
BF = r"C:\Windows\Fonts\malgunbd.ttf"
files = ["01_login","02_consent","03_topic_elder","04_survey_choice","05_survey_voice",
         "06_ai_response","07_crisis","08_youth_home","09_stats","10_essay",
         "11_welfare_topic","12_prompt_format","13_deliverable_gen","14_youth_survey",
         "15_welfare_dashboard","16_survey_analytics","17_settings_apikey",
         "18_admin_members","19_refine_chat","20_image_result"]
cols, cw, ch, lh, pad = 4, 280, 200, 26, 14
rows = (len(files) + cols - 1) // cols
W = cols * (cw + pad) + pad
H = rows * (ch + lh + pad) + pad
sheet = Image.new("RGB", (W, H), "#FFFFFF")
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype(BF, 15)
for i, fn in enumerate(files):
    r, c = divmod(i, cols)
    x = pad + c * (cw + pad)
    y = pad + r * (ch + lh + pad)
    im = Image.open(os.path.join(IMG, fn + ".png"))
    im.thumbnail((cw, ch), Image.LANCZOS)
    ox = x + (cw - im.width) // 2
    sheet.paste(im, (ox, y))
    d.rectangle([ox, y, ox + im.width, y + im.height], outline="#DDD")
    d.text((x, y + ch + 4), fn, font=font, fill="#333")
sheet.save(r"C:\dev\contest\제출본\_전체화면_컨택트시트.png")
print("contact sheet saved", sheet.size)
