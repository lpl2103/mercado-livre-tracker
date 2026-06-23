import asyncio

from playwright.async_api import async_playwright


async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://www.mercadolivre.com.br/caixa-de-som-bluetooth-jbl-xtreme-5-preta/up/MLBU4052365012",
            wait_until="networkidle",
            timeout=60000,
        )

        # Scrolla pra baixo pra ativar lazy loading
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(3)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(2)

        # Salva o HTML completo
        html = await page.content()
        with open("data/debug_full.html", "w", encoding="utf-8") as f:
            f.write(html)

        # Procura qualquer texto com 'x R$'
        elements = await page.query_selector_all("*")
        found = False
        for el in elements:
            try:
                text = await el.text_content()
                if "x R$" in text and len(text.strip()) < 100:
                    tag = await el.evaluate("el => el.tagName")
                    class_name = await el.evaluate("el => el.className")
                    html_snippet = await el.evaluate(
                        "el => el.outerHTML.substring(0, 300)"
                    )
                    print(f'Tag: <{tag}> | Class: "{class_name}"')
                    print(f"  Texto: {text.strip()}")
                    print(f"  HTML: {html_snippet}")
                    print()
                    found = True
            except:
                pass

        if not found:
            print("❌ Nenhum elemento com 'x R$' encontrado!")
            print("Procurando por 'parcela' ou 'vezes'...")
            for el in elements:
                try:
                    text = await el.text_content()
                    if any(
                        termo in text.lower()
                        for termo in ["parcela", "vezes", "sem juros"]
                    ):
                        if len(text.strip()) < 200:
                            tag = await el.evaluate("el => el.tagName")
                            class_name = await el.evaluate("el => el.className")
                            print(f'Tag: <{tag}> | Class: "{class_name}"')
                            print(f"  Texto: {text.strip()[:200]}")
                            print()
                except:
                    pass

        await browser.close()


asyncio.run(debug())
