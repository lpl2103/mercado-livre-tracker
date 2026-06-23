# src/storage.py
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.crawler import ProductSnapshot


class JSONStorage:
    """Repository pattern - abstrai persistência, fácil trocar por SQLite depois."""

    def __init__(self, filepath: Path = Path("data/products.json")):
        self.filepath = filepath
        self.filepath.parent.mkdir(exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Cria arquivo com array vazio se não existir."""
        if not self.filepath.exists():
            self.filepath.write_text("[]")

    def save(self, snapshot: ProductSnapshot, image_url: str = "") -> None:
        """Salva snapshot com metadados do produto."""
        data = self._load_all()
        data.append(
            {
                "product_name": snapshot.product_name,
                "image_url": image_url,
                "price": str(snapshot.price),
                "installments": snapshot.installments,
                "shipping": snapshot.shipping,
                "timestamp": snapshot.timestamp.isoformat(),
            }
        )
        self.filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def get_last(self) -> Optional[dict]:
        """Busca snapshot anterior para comparação de preços."""
        data = self._load_all()
        return data[-1] if data else None

    def _load_all(self) -> list[dict]:
        try:
            content = self.filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = self.filepath.read_text(encoding="cp1252")
        return json.loads(content)
