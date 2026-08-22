#Khithlainhtet
import os
import aiohttp
import textwrap
import io
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from Newmusic import config
from Newmusic.helpers import Track

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Thumbnail:
    def __init__(self): 
        self.size = (1280, 720)
        self.session: aiohttp.ClientSession | None = None
        self.API_URL = "" 
        
        title_font_path = os.path.join(BASE_DIR, "..", "helpers", "Raleway-Bold.ttf")
        info_font_path = os.path.join(BASE_DIR, "..", "helpers", "Inter-Light.ttf")

        try:
            self.font_title = ImageFont.truetype(title_font_path, 45)
            self.font_info = ImageFont.truetype(info_font_path, 30)
            self.font_small = ImageFont.truetype(info_font_path, 35) 
            self.font_time = ImageFont.truetype(info_font_path, 24)
            self.font_credit = ImageFont.truetype(info_font_path, 28)
        except:
            self.font_title = self.font_info = self.font_small = self.font_time = self.font_credit = ImageFont.load_default()

    async def start(self) -> None:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def get_image(self, image_url: str):
        if not self.session: await self.start()
        url = f"{self.API_URL}{image_url}" if self.API_URL else image_url
        try:
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
        except:
            return None
        return None

    async def generate(self, song: Track) -> str:
        try:
            os.makedirs("cache", exist_ok=True)
            output = f"cache/{song.id}.png"
            
            if os.path.exists(output):
                return output

            raw_cover = await self.get_image(song.thumbnail)
            if not raw_cover:
                raw_cover = Image.new("RGBA", (500, 500), (40, 40, 40, 255))

            # 1. Background
            bg = ImageOps.fit(raw_cover, self.size, method=Image.Resampling.BOX)
            bg = bg.filter(ImageFilter.GaussianBlur(20)) 
            bg = ImageEnhance.Brightness(bg).enhance(0.5) 
            draw = ImageDraw.Draw(bg)

            # 2. Album Cover with White Border
            c_size = 520
            c_inner = c_size - 12
            cx, cy = 100, (self.size[1] - c_size) // 2
            
            border_bg = Image.new("RGBA", (c_size, c_size), "white")
            b_mask = Image.new("L", (c_size, c_size), 0)
            ImageDraw.Draw(b_mask).rounded_rectangle((0, 0, c_size, c_size), 40, fill=255)
            border_bg.putalpha(b_mask)
            
            cover_img = ImageOps.fit(raw_cover, (c_inner, c_inner), method=Image.Resampling.LANCZOS)
            c_mask = Image.new("L", (c_inner, c_inner), 0)
            ImageDraw.Draw(c_mask).rounded_rectangle((0, 0, c_inner, c_inner), 35, fill=255)
            cover_img.putalpha(c_mask)
            
            border_bg.paste(cover_img, (6, 6), cover_img)
            bg.paste(border_bg, (cx, cy), border_bg)

            # 3. Contact Text
            contact = "If you want to create your own music bot, please contact "
            draw.text((self.size[0]//2, 45), contact, font=self.font_small, fill="white", anchor="ma")

            
            tx_start = 660 
            
            draw.text((tx_start, 160), "Now Playing", font=self.font_info, fill=(255, 200, 50))
            
            # width=18 ထားလိုက်ခြင်းဖြင့် စာကြောင်းတိုတိုနှင့် အောက်ဆင်းသွားပါမည်
            lines = textwrap.wrap(song.title, width=18)
            curr_y = 215
            for line in lines[:3]: # စာကြောင်း ၃ ကြောင်းအထိ ပြမည်
                draw.text((tx_start, curr_y), line, font=self.font_title, fill="white")
                curr_y += 65

            # 5. Progress Bar
            bar_y = 480
            bar_w = 500
            draw.rounded_rectangle((tx_start, bar_y, tx_start + bar_w, bar_y + 8), 4, fill=(100, 100, 100, 150))
            draw.rounded_rectangle((tx_start, bar_y, tx_start + (bar_w * 0.45), bar_y + 8), 4, fill=(255, 200, 50))

            # 6. Time Info
            draw.text((tx_start, bar_y + 20), "0:03", font=self.font_time, fill="white")
            draw.text((tx_start + bar_w, bar_y + 20), "4:33", font=self.font_time, fill="white", anchor="ra")

            # 7. Playback Symbols
            ctrl_y = 580
            draw.text((tx_start + 100, ctrl_y), "«", font=self.font_title, fill="white", anchor="ma")
            draw.text((tx_start + 250, ctrl_y), "II", font=self.font_title, fill="white", anchor="ma")
            draw.text((tx_start + 400, ctrl_y), "»", font=self.font_title, fill="white", anchor="ma")

            # 8. Bottom Credit
            draw.text((self.size[0]//2, self.size[1] - 45), "DEV", font=self.font_credit, fill=(255, 255, 255, 180), anchor="ma")

            bg.save(output, "PNG")
            return output

        except Exception as e:
            print(f"Error: {e}")
            return config.DEFAULT_THUMB
