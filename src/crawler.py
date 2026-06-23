# src/crawler.py
import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from lxml import html
from playwright.async_api import Browser, Page, async_playwright


@dataclass(frozen=True)
class ProductSnapshot:
    price: Decimal
    installments: str
    shipping: str
    product_name: str  # NOVO
    timestamp: datetime

    @classmethod
    def from_raw(
        cls, price: str, installments: str, shipping: str, product_name: str
    ) -> "ProductSnapshot":
        """Factory method - limpa e normaliza dados brutos."""
        # Se já vem no formato com ponto decimal (ex: "597.91"), usa direto
        # Se vem no formato brasileiro (ex: "1.699,00" ou "1.699"), converte
        clean_price_str = price.strip()

        # Detecta se é formato internacional (ponto como decimal)
        if "." in clean_price_str and "," not in clean_price_str:
            # Formato: "597.91" -> Decimal direto
            clean_price = Decimal(clean_price_str)
        elif "," in clean_price_str:
            # Formato brasileiro: "1.699,00" -> Decimal("1699.00")
            clean_price = Decimal(clean_price_str.replace(".", "").replace(",", "."))
        else:
            # Número inteiro sem decimais: "1699" -> Decimal("1699")
            clean_price = Decimal(clean_price_str)

        return cls(
            price=clean_price,
            installments=installments.strip(),
            shipping=shipping.strip(),
            product_name=product_name.strip(),
            timestamp=datetime.now(),
        )


# Seletores CSS atualizados para o layout atual do Mercado Livre
SELECTORS = {
    "price_fraction": ".andes-money-amount__fraction",
    "price_cents": ".andes-money-amount__cents",
    "installments": "#pricing_price_subtitle",
    "shipping_free": ".ui-pdp-shipping--free .ui-pdp-color--GREEN",
    "shipping_text": ".ui-pdp-shipping--animated .ui-pdp-color--GREEN",
    # Fallback - container principal de preço
    "price_container": ".ui-pdp-price__main-container",
    # Meta tag com preço (quase sempre presente)
    "meta_price": 'meta[itemprop="price"]',
    "product_title": ".ui-pdp-title",  # NOVO
    "product_image": ".ui-pdp-gallery__figure__image",  # NOVO
}


async def create_browser() -> tuple[Browser, Page]:
    """Inicializa navegador com fingerprint realista."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )

    # Context com viewport realista e locale pt-BR
    context = await browser.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        permissions=["geolocation"],
        geolocation={"latitude": -23.5505, "longitude": -46.6333},  # São Paulo
    )

    # Remove flag de automação do webdriver
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt'] });
    """)

    page = await context.new_page()
    return browser, page


def extract_product_name(tree: html.HtmlElement) -> str:
    """Extrai o nome do produto."""
    title = tree.cssselect(SELECTORS["product_title"])
    if title:
        return title[0].text_content().strip()

    # Fallback: meta tag title
    meta_title = tree.cssselect('meta[name="title"]')
    if meta_title:
        content = meta_title[0].get("content", "")
        if content:
            return content

    return "Produto Desconhecido"


# src/crawler.py - função extract_price (reescrita)


def extract_price(tree: html.HtmlElement) -> str:
    """Extrai preço - prioriza meta tag itemprop (mais confiável)."""

    # 1. META TAG - FONTE MAIS CONFIÁVEL (preço completo: 597.91)
    meta_price = tree.cssselect('meta[itemprop="price"]')
    if meta_price:
        content = meta_price[0].get("content", "")
        if content:
            return content  # Já vem no formato correto: "597.91"

    # 2. Classe de fração + centavos (fallback)
    fraction = tree.cssselect(SELECTORS["price_fraction"])
    cents = tree.cssselect(SELECTORS["price_cents"])

    if fraction:
        price_text = fraction[0].text_content().strip()
        if cents:
            price_text += "." + cents[0].text_content().strip()
        return price_text

    # 3. Container principal (último fallback)
    container = tree.cssselect(SELECTORS["price_container"])
    if container:
        full_text = container[0].text_content()
        match = re.search(r"R\$\s*([\d.,]+)", full_text)
        if match:
            return match.group(1).replace(".", "").replace(",", ".")

    return ""


def extract_installments(tree: html.HtmlElement) -> str:
    """Extrai informação de parcelas do ID específico."""
    # Seletor principal: ID pricing_price_subtitle
    installments = tree.cssselect(SELECTORS["installments"])
    if installments:
        text = installments[0].text_content().strip()
        # Ex: "18x R$94,39 sem juros com cartão Mercado Pago"
        # Extrai só "18x R$94,39 sem juros"
        match = re.search(r"(\d+x\s*R\$\s*[\d.,]+\s*sem juros)", text)
        if match:
            return match.group(1)
        # Fallback: qualquer "Nx R$ valor"
        match = re.search(r"(\d+x\s*R\$\s*[\d.,]+)", text)
        if match:
            return match.group(1)
        return text

    return ""


def extract_shipping(tree: html.HtmlElement) -> str:
    """Extrai informação de frete."""
    # Frete grátis
    free_shipping = tree.cssselect(SELECTORS["shipping_free"])
    if free_shipping:
        return free_shipping[0].text_content().strip()

    # Frete com texto
    shipping = tree.cssselect(SELECTORS["shipping_text"])
    if shipping:
        return shipping[0].text_content().strip()

    # Fallback: busca "Frete grátis" ou "Envio" no corpo
    body_text = tree.text_content()
    match = re.search(
        r"(Frete grátis|Envio grátis|Chegará grátis)", body_text, re.IGNORECASE
    )
    if match:
        return match.group(1)

    # Busca valor de frete
    match = re.search(r"(Frete|Envio).*?(R\$\s*[\d.,]+)", body_text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}: {match.group(2)}"

    return ""


async def crawl(url: str) -> tuple[ProductSnapshot, str]:
    """Pipeline principal. Retorna snapshot + URL da imagem."""
    browser = None

    try:
        browser, page = await create_browser()

        print("  🌐 Carregando página...")
        await page.goto(url, wait_until="networkidle", timeout=60000)

        try:
            await page.wait_for_selector(SELECTORS["price_container"], timeout=15000)
        except Exception:
            try:
                await page.wait_for_selector(SELECTORS["meta_price"], timeout=10000)
            except Exception:
                print(
                    "  ⚠️  Elementos de preço não encontrados, tentando mesmo assim..."
                )

        await asyncio.sleep(2)
        content = await page.content()
        tree = html.fromstring(content)

        price = extract_price(tree)
        installments = extract_installments(tree)
        shipping = extract_shipping(tree)
        product_name = extract_product_name(tree)  # NOVO

        # Extrai URL da imagem
        image_url = ""
        img_elem = tree.cssselect(SELECTORS["product_image"])
        if img_elem:
            image_url = img_elem[0].get("src", "")
            # Prefere a versão 2X (maior qualidade)
            data_zoom = img_elem[0].get("data-zoom", "")
            if data_zoom:
                image_url = data_zoom

        print(f"  Produto: '{product_name}'")
        print(f"  Preço bruto: '{price}'")
        print(f"  Parcelas brutas: '{installments}'")
        print(f"  Frete bruto: '{shipping}'")

        if not any([price, installments, shipping]):
            await page.screenshot(path="data/debug_screenshot.png")
            Path("data/debug.html").write_text(content, encoding="utf-8")
            raise ValueError("Não foi possível extrair dados.")

        snapshot = ProductSnapshot.from_raw(price, installments, shipping, product_name)
        return snapshot, image_url

    finally:
        if browser:
            await browser.close()


from pathlib import Path  # Adiciona no topo depois se quiser
