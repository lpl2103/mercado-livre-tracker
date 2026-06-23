# src/scheduler.py
import asyncio
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.crawler import crawl
from src.notifier import PriceNotifier
from src.storage import JSONStorage


class TrackerScheduler:
    def __init__(
        self,
        urls: list[str],
        interval_minutes: int = 30,
        storage_path: Path = Path("data/products.json"),
        email_config: Optional[dict] = None,
    ):
        self.urls = urls
        self.interval = interval_minutes * 60
        self.storage = JSONStorage(storage_path)
        self.notifier = PriceNotifier(email_config=email_config)
        self._shutdown = False

    @classmethod
    def from_file(
        cls,
        filepath: Path = Path("products.txt"),
        interval_minutes: int = 30,
        storage_path: Path = Path("data/products.json"),
        email_config: Optional[dict] = None,
    ) -> "TrackerScheduler":
        """Factory method: carrega URLs de um arquivo txt."""
        urls = load_urls_from_file(filepath)

        if not urls:
            raise ValueError(f"Nenhuma URL encontrada em {filepath}")

        print(f"📄 {len(urls)} produto(s) carregados de {filepath}")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")

        return cls(urls, interval_minutes, storage_path, email_config)

    async def run(self) -> None:
        print(f"\n🚀 Iniciando tracker para {len(self.urls)} produto(s)")
        print(f"⏱️  Intervalo entre ciclos: {self.interval // 60} minutos")
        print("📌 Pressione Ctrl+C para parar\n")

        try:
            while not self._shutdown:
                cycle_start = datetime.now()
                print(f"{'=' * 60}")
                print(f"[{cycle_start:%Y-%m-%d %H:%M:%S}] Iniciando ciclo de coleta...")
                print(f"{'=' * 60}")

                success_count = 0
                error_count = 0

                for i, url in enumerate(self.urls, 1):
                    try:
                        print(f"\n[{i}/{len(self.urls)}] Coletando: {url[:80]}...")

                        snapshot, image_url = await crawl(url)
                        previous = self.storage.get_last()
                        self.storage.save(snapshot, image_url)

                        current_dict = {
                            "price": str(snapshot.price),
                            "installments": snapshot.installments,
                            "shipping": snapshot.shipping,
                        }
                        self.notifier.check_and_notify(current_dict, previous)

                        print(f"  ✅ {snapshot.product_name}")
                        print(
                            f"     R$ {snapshot.price} | {snapshot.installments} | {snapshot.shipping}"
                        )
                        success_count += 1

                    except Exception as e:
                        print(f"  ❌ Erro: {e}")
                        error_count += 1

                    # Pequeno delay entre produtos (evita rate limiting)
                    if i < len(self.urls):
                        await asyncio.sleep(3)

                cycle_end = datetime.now()
                duration = (cycle_end - cycle_start).total_seconds()

                print(f"\n{'=' * 60}")
                print(f"✅ Ciclo concluído em {duration:.0f}s")
                print(f"   Sucessos: {success_count}/{len(self.urls)}")
                if error_count > 0:
                    print(f"   Erros: {error_count}/{len(self.urls)}")

                next_cycle = cycle_end.timestamp() + self.interval
                next_time = datetime.fromtimestamp(next_cycle)
                print(f"⏳ Próximo ciclo: {next_time:%H:%M:%S}")
                print(f"{'=' * 60}\n")

                await asyncio.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Ctrl+C recebido. Finalizando tracker...")
        finally:
            print("✅ Tracker finalizado. Até mais!")


# src/scheduler.py - load_urls_from_file (versão blindada)


def load_urls_from_file(filepath: Path) -> list[str]:
    """Carrega URLs de um arquivo txt."""
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    urls = []
    # Lê como bytes e decodifica manualmente (mata qualquer BOM)
    raw_bytes = filepath.read_bytes()

    # Remove BOM UTF-8, UTF-16 LE, UTF-16 BE
    if raw_bytes.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
        raw_bytes = raw_bytes[3:]
    elif raw_bytes.startswith(b"\xff\xfe"):  # UTF-16 LE BOM
        raw_bytes = raw_bytes[2:]
    elif raw_bytes.startswith(b"\xfe\xff"):  # UTF-16 BE BOM
        raw_bytes = raw_bytes[2:]

    content = raw_bytes.decode("utf-8")

    for line in content.splitlines():
        line = line.strip()
        # Remove qualquer caractere invisível restante
        line = (
            line.replace("\ufeff", "")
            .replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\u200d", "")
        )

        if line and not line.startswith("#") and line.startswith("http"):
            urls.append(line)

    return urls


def main():
    warnings.filterwarnings("ignore", category=ResourceWarning)

    # Opção 1: URLs hardcoded (mantido por compatibilidade)
    # scheduler = TrackerScheduler(
    #     urls=["https://www.mercadolivre.com.br/..."],
    #     interval_minutes=30,
    # )

    # Opção 2: Carrega do arquivo products.txt (RECOMENDADO)
    scheduler = TrackerScheduler.from_file(
        filepath=Path("products.txt"),
        interval_minutes=30,
    )

    try:
        asyncio.run(scheduler.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
