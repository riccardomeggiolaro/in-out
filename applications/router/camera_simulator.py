from datetime import datetime
from io import BytesIO
import random

from fastapi import APIRouter, Response
from PIL import Image, ImageDraw, ImageFont


class CameraSimulatorRouter:
	"""
	Fotocamera finta per i test: a ogni chiamata restituisce una nuova
	immagine PNG con data e ora, come lo snapshot di una fotocamera IP.

	Si usa al posto dell'URL "picture" di una fotocamera vera nella
	configurazione della pesa, per esempio:
		http://127.0.0.1/api/camera-simulator/picture
	L'endpoint è pubblico (vedi public_endpoints.py) perché il server lo
	chiama come farebbe con una fotocamera, senza token.
	"""

	WIDTH = 960
	HEIGHT = 540

	def __init__(self):
		self.router = APIRouter()
		self.router.add_api_route('/picture', self.Picture, methods=['GET'])

	async def Picture(self, label: str = "SIMULATORE FOTOCAMERA"):
		now = datetime.now()
		image = self._draw(now, label[:40])
		buffer = BytesIO()
		image.save(buffer, format="PNG")
		return Response(
			content=buffer.getvalue(),
			media_type="image/png",
			headers={"Cache-Control": "no-store"}
		)

	def _font(self, size: int):
		for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf"):
			try:
				return ImageFont.truetype(name, size)
			except OSError:
				continue
		return ImageFont.load_default()

	def _draw(self, now: datetime, label: str) -> Image.Image:
		w, h = self.WIDTH, self.HEIGHT
		img = Image.new("RGB", (w, h), (120, 160, 200))
		d = ImageDraw.Draw(img)

		# Cielo e piazzale
		d.rectangle([0, 0, w, int(h * 0.45)], fill=(150, 190, 225))
		d.rectangle([0, int(h * 0.45), w, h], fill=(110, 110, 115))
		# Pesa (piattaforma)
		d.polygon([(120, 430), (840, 430), (780, 330), (180, 330)], fill=(80, 120, 80))
		for i in range(1, 6):
			y = 330 + i * 17
			d.line([(180 - i * 10, y), (780 + i * 10, y)], fill=(60, 95, 60), width=2)

		# Camion con colore casuale, così ogni scatto è diverso
		color = random.choice([(70, 100, 170), (170, 100, 70), (70, 150, 110), (140, 90, 160), (180, 160, 60)])
		offset = random.randint(-60, 60)
		x0 = 250 + offset
		d.rectangle([x0, 200, x0 + 330, 340], fill=color)                       # cassone
		d.rectangle([x0 + 330, 240, x0 + 440, 340], fill=tuple(int(c * 0.8) for c in color))  # cabina
		d.rectangle([x0 + 355, 255, x0 + 425, 290], fill=(200, 225, 245))       # parabrezza
		for wx in (x0 + 50, x0 + 120, x0 + 270, x0 + 390):
			d.ellipse([wx - 28, 315, wx + 28, 371], fill=(30, 30, 30))
			d.ellipse([wx - 12, 331, wx + 12, 355], fill=(120, 120, 120))
		# Targa finta
		plate = "SIM" + str(random.randint(100, 999))
		d.rectangle([x0 + 360, 298, x0 + 448, 324], fill=(245, 245, 245), outline=(30, 30, 30))
		d.text((x0 + 366, 302), plate, fill=(20, 20, 20), font=self._font(16))

		# Banda informativa come nelle fotocamere IP
		d.rectangle([0, 0, w, 44], fill=(0, 0, 0))
		d.text((14, 10), label, fill=(255, 255, 255), font=self._font(22))
		ts = now.strftime("%d/%m/%Y %H:%M:%S")
		ts_font = self._font(22)
		tw = d.textlength(ts, font=ts_font)
		d.text((w - tw - 14, 10), ts, fill=(255, 220, 80), font=ts_font)
		return img
