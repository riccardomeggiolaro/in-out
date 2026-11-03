from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Response
from PIL import Image, ImageDraw, ImageFont


ASSETS_DIR = Path(__file__).parent / "camera_simulator_assets"
BASE_PICTURE = ASSETS_DIR / "weighbridge_truck.jpg"


class CameraSimulatorRouter:
	"""
	Fotocamera finta per i test: a ogni chiamata restituisce la stessa foto
	reale di un camion sulla pesa, con sopra la banda con data e ora, come
	lo snapshot di una fotocamera IP.

	Si usa al posto dell'URL "picture" di una fotocamera vera nella
	configurazione della pesa, per esempio:
		http://10.0.5.86/api/camera-simulator/picture
	L'endpoint è pubblico (vedi public_endpoints.py) perché il server lo
	chiama come farebbe con una fotocamera, senza token.
	"""

	def __init__(self):
		self.router = APIRouter()
		self.router.add_api_route('/picture', self.Picture, methods=['GET'])
		self._base = None

	async def Picture(self, label: str = "SIMULATORE FOTOCAMERA"):
		image = self._draw(datetime.now(), label[:40])
		buffer = BytesIO()
		image.save(buffer, format="JPEG", quality=88)
		return Response(
			content=buffer.getvalue(),
			media_type="image/jpeg",
			headers={"Cache-Control": "no-store"}
		)

	def _base_picture(self) -> Image.Image:
		if self._base is None:
			self._base = Image.open(BASE_PICTURE).convert("RGB")
		return self._base.copy()

	def _font(self, size: int):
		for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf"):
			try:
				return ImageFont.truetype(name, size)
			except OSError:
				continue
		return ImageFont.load_default()

	def _draw(self, now: datetime, label: str) -> Image.Image:
		img = self._base_picture()
		w, h = img.size
		d = ImageDraw.Draw(img)

		# Banda in alto come nelle fotocamere IP: etichetta a sinistra, data e ora a destra
		band = max(26, h // 16)
		font = self._font(int(band * 0.6))
		d.rectangle([0, 0, w, band], fill=(0, 0, 0))
		d.text((10, band * 0.18), label, fill=(255, 255, 255), font=font)
		ts = now.strftime("%d/%m/%Y %H:%M:%S")
		d.text((w - d.textlength(ts, font=font) - 10, band * 0.18), ts, fill=(255, 220, 80), font=font)
		return img
