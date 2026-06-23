# src/dashboard.py - substitui completamente

import json
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path


class DashboardGenerator:
    def __init__(self, data_path: Path = Path("data/products.json")):
        self.data_path = data_path

    def load_data(self) -> list[dict]:
        if not self.data_path.exists():
            return []
        try:
            content = self.data_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = self.data_path.read_text(encoding="cp1252")
        return json.loads(content)

    def get_products(self, data: list[dict]) -> list[dict]:
        """Agrupa dados por produto e retorna lista de produtos únicos."""
        products = {}
        for entry in data:
            name = entry.get("product_name", "Desconhecido")
            if name not in products:
                products[name] = {
                    "name": name,
                    "image_url": entry.get("image_url", ""),
                    "count": 0,
                    "last_price": entry["price"],
                    "last_date": entry["timestamp"],
                }
            products[name]["count"] += 1
            products[name]["last_price"] = entry["price"]
            products[name]["last_date"] = entry["timestamp"]

        return list(products.values())

    def filter_by_product(self, data: list[dict], product_name: str) -> list[dict]:
        return [d for d in data if d.get("product_name", "") == product_name]

    def _parse_installments_count(self, text: str) -> int:
        match = re.match(r"(\d+)x", text.strip())
        return int(match.group(1)) if match else 0

    def _prepare_chart_data(self, data: list[dict]) -> dict:
        timestamps = []
        prices = []
        installments = []

        for entry in data:
            timestamps.append(entry["timestamp"])
            prices.append(float(entry["price"]))
            installments.append(self._parse_installments_count(entry["installments"]))

        return {
            "timestamps": timestamps,
            "prices": prices,
            "installments": installments,
        }

    def _calculate_stats(self, data: list[dict]) -> dict:
        if not data:
            return {}

        prices = [Decimal(d["price"]) for d in data]
        current = data[-1]
        first = data[0]

        price_change = prices[-1] - prices[0]
        price_change_pct = (
            (price_change / prices[0] * 100) if prices[0] else Decimal("0")
        )

        min_price = min(prices)
        min_price_entry = min(data, key=lambda d: Decimal(d["price"]))

        max_installments = max(
            data, key=lambda d: self._parse_installments_count(d["installments"])
        )

        def brl(value):
            return (
                f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        return {
            "product_name": current.get("product_name", "Desconhecido"),
            "image_url": current.get("image_url", ""),
            "first_price": float(prices[0]),
            "current_price": float(prices[-1]),
            "min_price": float(min_price),
            "min_price_date": min_price_entry["timestamp"],
            "price_change": float(price_change),
            "price_change_pct": float(round(price_change_pct, 2)),
            "total_snapshots": len(data),
            "first_date": first["timestamp"],
            "last_date": current["timestamp"],
            "current_installments": current["installments"],
            "current_shipping": current["shipping"],
            "max_installments": max_installments["installments"],
            "max_installments_date": max_installments["timestamp"],
            "current_price_fmt": brl(float(prices[-1])),
            "price_change_fmt": brl(abs(float(price_change))),
            "min_price_fmt": brl(float(min_price)),
        }

    def generate(self, output_path: Path = Path("data/dashboard.html")) -> Path:
        all_data = self.load_data()

        if not all_data:
            raise ValueError("Nenhum dado encontrado. Execute o scheduler primeiro.")

        products = self.get_products(all_data)

        # Produto padrão: o mais recente
        default_product = max(products, key=lambda p: p["last_date"])
        default_name = default_product["name"]

        # Prepara dados de todos os produtos para o JavaScript
        products_json = json.dumps(products, ensure_ascii=False)

        # Dados do produto padrão
        product_data = self.filter_by_product(all_data, default_name)
        chart_data = self._prepare_chart_data(product_data)
        stats = self._calculate_stats(product_data)

        html = self._build_html(
            chart_data, stats, products_json, default_name, all_data
        )
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _build_html(
        self,
        chart_data: dict,
        stats: dict,
        products_json: str,
        default_name: str,
        all_data: list[dict],
    ) -> str:
        timestamps_json = json.dumps(chart_data["timestamps"])
        prices_json = json.dumps(chart_data["prices"])
        installments_json = json.dumps(chart_data["installments"])
        all_data_json = json.dumps(all_data, ensure_ascii=False)

        if stats["price_change"] > 0:
            trend_icon, trend_class = "📈", "up"
        elif stats["price_change"] < 0:
            trend_icon, trend_class = "📉", "down"
        else:
            trend_icon, trend_class = "➡️", "neutral"

        html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercado Livre - Price Tracker</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg: #f5f5f5;
            --card-bg: #ffffff;
            --text: #333333;
            --text-secondary: #666666;
            --border: #e0e0e0;
            --accent: #00a650;
            --accent-down: #e74c3c;
            --accent-up: #e74c3c;
            --shadow: 0 2px 8px rgba(0,0,0,0.1);
            --chart-grid: rgba(0,0,0,0.05);
        }

        [data-theme="dark"] {
            --bg: #1a1a2e;
            --card-bg: #16213e;
            --text: #e0e0e0;
            --text-secondary: #a0a0a0;
            --border: #2a2a4a;
            --accent: #00c853;
            --accent-down: #ff5252;
            --accent-up: #ff5252;
            --shadow: 0 2px 8px rgba(0,0,0,0.3);
            --chart-grid: rgba(255,255,255,0.05);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            transition: background 0.3s, color 0.3s;
            min-height: 100vh;
        }

        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
        }

        h1 { font-size: 1.8rem; font-weight: 700; }

        .header-controls {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        .product-select {
            background: var(--card-bg);
            border: 2px solid var(--border);
            color: var(--text);
            padding: 10px 16px;
            border-radius: 25px;
            font-size: 0.95rem;
            cursor: pointer;
            min-width: 250px;
            box-shadow: var(--shadow);
        }

        .theme-toggle {
            background: var(--card-bg);
            border: 2px solid var(--border);
            color: var(--text);
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.95rem;
            box-shadow: var(--shadow);
            white-space: nowrap;
        }

        .theme-toggle:hover, .product-select:hover { transform: translateY(-2px); }

        .product-info {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            margin-bottom: 24px;
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .product-image {
            width: 120px;
            height: 120px;
            object-fit: contain;
            border-radius: 8px;
            background: #f0f0f0;
            flex-shrink: 0;
        }

        .product-details h2 {
            font-size: 1.3rem;
            margin-bottom: 8px;
        }

        .product-details p {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        @media (max-width: 600px) {
            .product-info { flex-direction: column; text-align: center; }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            transition: transform 0.2s;
        }

        .stat-card:hover { transform: translateY(-2px); }

        .stat-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-value { font-size: 1.8rem; font-weight: 700; }
        .stat-value.down { color: var(--accent-down); }
        .stat-value.up { color: var(--accent-up); }
        .stat-value.neutral { color: var(--accent); }

        .stat-sub { font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px; }

        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }

        @media (max-width: 768px) {
            .charts-grid { grid-template-columns: 1fr; }
        }

        .chart-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }

        .chart-card h3 { margin-bottom: 16px; font-size: 1.1rem; color: var(--text-secondary); }
        .chart-container { position: relative; width: 100%; height: 300px; }

        .history-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }

        .history-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }

        .history-table th, .history-table td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .history-table th {
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
        }

        .history-table tbody tr:hover { background: var(--chart-grid); }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-free { background: #00a65020; color: #00a650; }

        footer { text-align: center; color: var(--text-secondary); font-size: 0.8rem; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Mercado Livre Price Tracker</h1>
            <div class="header-controls">
                <select class="product-select" id="productSelect" onchange="switchProduct()">
                </select>
                <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">
                    🌙 Modo Escuro
                </button>
            </div>
        </header>

        <div class="product-info" id="productInfo">
            <img class="product-image" id="productImage" src="" alt="Produto" onerror="this.style.display='none'">
            <div class="product-details">
                <h2 id="productName">{{product_name}}</h2>
                <p>Período: {{first_date}} até {{last_date}} • {{total_snapshots}} coletas</p>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Preço Atual</div>
                <div class="stat-value">{{current_price_fmt}}</div>
                <div class="stat-sub">{{current_shipping}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Variação Total</div>
                <div class="stat-value {{trend_class}}">{{trend_icon}} {{price_change_fmt}}</div>
                <div class="stat-sub">{{price_change_pct_signal}}% desde o início</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Melhor Preço</div>
                <div class="stat-value" style="color: var(--accent)">{{min_price_fmt}}</div>
                <div class="stat-sub">em {{min_price_date_short}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Parcelas Atuais</div>
                <div class="stat-value">{{current_installments}}</div>
                <div class="stat-sub">Máx: {{max_installments}} ({{max_installments_date_short}})</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <h3>📈 Evolução do Preço</h3>
                <div class="chart-container"><canvas id="priceChart"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>📊 Quantidade de Parcelas</h3>
                <div class="chart-container"><canvas id="installmentsChart"></canvas></div>
            </div>
        </div>

        <div class="history-card">
            <h3>📋 Histórico de Coletas</h3>
            <div style="overflow-x: auto;">
                <table class="history-table">
                    <thead>
                        <tr><th>Data/Hora</th><th>Preço</th><th>Parcelas</th><th>Frete</th></tr>
                    </thead>
                    <tbody id="historyBody"></tbody>
                </table>
            </div>
        </div>

        <footer>Última atualização: {{last_date}}</footer>
    </div>

    <script>
        var allData = {{all_data_json}};
        var products = {{products_json}};
        var currentProduct = "{{default_product}}";

        // Dados iniciais
        var timestamps = {{timestamps_json}};
        var prices = {{prices_json}};
        var installments = {{installments_json}};

        function getProductData(productName) {
            return allData.filter(function(d) { return d.product_name === productName; });
        }

        function parseInstallments(text) {
            var match = text.match(/(\\d+)x/);
            return match ? parseInt(match[1]) : 0;
        }

        function formatBRL(value) {
            return 'R$ ' + value.toFixed(2).replace('.', ',');
        }

        function updateAllData(productName) {
            var data = getProductData(productName);
            if (data.length === 0) return;

            timestamps = data.map(function(d) { return d.timestamp; });
            prices = data.map(function(d) { return parseFloat(d.price); });
            installments = data.map(function(d) { return parseInstallments(d.installments); });

            var current = data[data.length - 1];
            var first = data[0];
            var minPrice = Math.min.apply(null, prices);
            var minEntry = data.reduce(function(min, d) {
                return parseFloat(d.price) < parseFloat(min.price) ? d : min;
            });
            var maxInstallments = Math.max.apply(null, installments);
            var maxInstEntry = data.reduce(function(max, d) {
                return parseInstallments(d.installments) > parseInstallments(max.installments) ? d : max;
            });

            var priceChange = prices[prices.length - 1] - prices[0];
            var priceChangePct = prices[0] !== 0 ? (priceChange / prices[0] * 100) : 0;

            // Atualiza info do produto
            document.getElementById('productName').textContent = productName;
            document.getElementById('productImage').src = current.image_url || '';

            // Atualiza cards
            var cards = document.querySelectorAll('.stat-card');
            var trendIcon = priceChange > 0 ? '📈' : priceChange < 0 ? '📉' : '➡️';
            var trendClass = priceChange > 0 ? 'up' : priceChange < 0 ? 'down' : 'neutral';

            // Reconstroi os cards (simplificado - rebuild da section)
            var statsHTML =
                '<div class="stat-card">' +
                    '<div class="stat-label">Preço Atual</div>' +
                    '<div class="stat-value">' + formatBRL(prices[prices.length-1]) + '</div>' +
                    '<div class="stat-sub">' + (current.shipping || '') + '</div>' +
                '</div>' +
                '<div class="stat-card">' +
                    '<div class="stat-label">Variação Total</div>' +
                    '<div class="stat-value ' + trendClass + '">' + trendIcon + ' ' + formatBRL(Math.abs(priceChange)) + '</div>' +
                    '<div class="stat-sub">' + (priceChangePct >= 0 ? '+' : '') + priceChangePct.toFixed(1) + '% desde o início</div>' +
                '</div>' +
                '<div class="stat-card">' +
                    '<div class="stat-label">Melhor Preço</div>' +
                    '<div class="stat-value" style="color: var(--accent)">' + formatBRL(minPrice) + '</div>' +
                    '<div class="stat-sub">em ' + minEntry.timestamp.substring(0, 10) + '</div>' +
                '</div>' +
                '<div class="stat-card">' +
                    '<div class="stat-label">Parcelas Atuais</div>' +
                    '<div class="stat-value">' + (current.installments || '') + '</div>' +
                    '<div class="stat-sub">Máx: ' + (maxInstEntry.installments || '') + ' (' + maxInstEntry.timestamp.substring(0,10) + ')</div>' +
                '</div>';

            document.querySelector('.stats-grid').innerHTML = statsHTML;

            // Atualiza período no header
            document.querySelector('.product-details p').textContent =
                'Período: ' + first.timestamp.substring(0,10) + ' até ' + current.timestamp.substring(0,10) + ' • ' + data.length + ' coletas';

            createCharts();
            buildHistoryTable(data);
        }

        function switchProduct() {
            var select = document.getElementById('productSelect');
            currentProduct = select.value;
            updateAllData(currentProduct);
        }

        function populateProductDropdown() {
            var select = document.getElementById('productSelect');
            select.innerHTML = '';

            // Ordena por data mais recente
            products.sort(function(a, b) { return b.last_date.localeCompare(a.last_date); });

            products.forEach(function(p) {
                var option = document.createElement('option');
                option.value = p.name;
                option.textContent = p.name + ' (' + p.count + ' coletas)';
                if (p.name === currentProduct) option.selected = true;
                select.appendChild(option);
            });
        }

        var labels, priceChart, installmentsChart;

        function getChartColors() {
            var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            return {
                gridColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
                textColor: isDark ? '#a0a0a0' : '#666666',
                priceLine: isDark ? '#00c853' : '#00a650',
                priceFill: isDark ? 'rgba(0,200,83,0.1)' : 'rgba(0,166,80,0.08)',
                installmentsLine: isDark ? '#448aff' : '#2962ff',
                installmentsFill: isDark ? 'rgba(68,138,255,0.1)' : 'rgba(41,98,255,0.08)',
            };
        }

        function createCharts() {
            labels = timestamps.map(function(t) {
                var d = new Date(t);
                return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) +
                       ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
            });

            var colors = getChartColors();
            var ctx1 = document.getElementById('priceChart').getContext('2d');
            var ctx2 = document.getElementById('installmentsChart').getContext('2d');

            if (priceChart) priceChart.destroy();
            if (installmentsChart) installmentsChart.destroy();

            priceChart = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Preço',
                        data: prices,
                        borderColor: colors.priceLine,
                        backgroundColor: colors.priceFill,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: colors.priceLine,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: function(ctx) { return 'R$ ' + ctx.parsed.y.toFixed(2); } } }
                    },
                    scales: {
                        x: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor, maxTicksLimit: 10 } },
                        y: {
                            grid: { color: colors.gridColor },
                            ticks: { color: colors.textColor, callback: function(v) { return 'R$ ' + v.toFixed(0); } }
                        }
                    }
                }
            });

            installmentsChart = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Parcelas',
                        data: installments,
                        backgroundColor: colors.installmentsFill,
                        borderColor: colors.installmentsLine,
                        borderWidth: 2,
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: function(ctx) { return ctx.parsed.y + 'x'; } } }
                    },
                    scales: {
                        x: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor, maxTicksLimit: 10 } },
                        y: {
                            grid: { color: colors.gridColor },
                            ticks: { color: colors.textColor, callback: function(v) { return v + 'x'; }, stepSize: 1 },
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        function buildHistoryTable(data) {
            var tbody = document.getElementById('historyBody');
            var rows = '';

            for (var i = data.length - 1; i >= 0; i--) {
                var d = data[i];
                var date = new Date(d.timestamp);
                var dateStr = date.toLocaleDateString('pt-BR') + ' ' +
                              date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
                var price = parseFloat(d.price).toFixed(2).replace('.', ',');
                var shippingHtml = d.shipping && d.shipping.toLowerCase().indexOf('grátis') >= 0 ?
                    '<span class="badge badge-free">Grátis</span>' : (d.shipping || '');

                rows += '<tr>' +
                    '<td>' + dateStr + '</td>' +
                    '<td><strong>R$ ' + price + '</strong></td>' +
                    '<td>' + (d.installments || '') + '</td>' +
                    '<td>' + shippingHtml + '</td>' +
                '</tr>';
            }

            tbody.innerHTML = rows;
        }

        function toggleTheme() {
            var html = document.documentElement;
            var btn = document.getElementById('themeBtn');
            var isDark = html.getAttribute('data-theme') === 'dark';

            if (isDark) {
                html.removeAttribute('data-theme');
                btn.innerHTML = '🌙 Modo Escuro';
                localStorage.setItem('theme', 'light');
            } else {
                html.setAttribute('data-theme', 'dark');
                btn.innerHTML = '☀️ Modo Claro';
                localStorage.setItem('theme', 'dark');
            }

            createCharts();
        }

        function init() {
            var savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
                document.getElementById('themeBtn').innerHTML = '☀️ Modo Claro';
            }

            populateProductDropdown();

            // Dados iniciais do produto padrão
            var initialData = getProductData(currentProduct);
            if (initialData.length > 0) {
                document.getElementById('productImage').src = initialData[initialData.length-1].image_url || '';
            }

            createCharts();
            buildHistoryTable(initialData);
        }

        init();
    </script>
</body>
</html>"""

        replacements = {
            "{{product_name}}": stats.get("product_name", ""),
            "{{first_date}}": stats.get("first_date", "")[:10]
            if stats.get("first_date")
            else "",
            "{{last_date}}": stats.get("last_date", "")[:10]
            if stats.get("last_date")
            else "",
            "{{total_snapshots}}": str(stats.get("total_snapshots", 0)),
            "{{current_price_fmt}}": stats.get("current_price_fmt", ""),
            "{{current_shipping}}": stats.get("current_shipping", ""),
            "{{trend_class}}": trend_class,
            "{{trend_icon}}": trend_icon,
            "{{price_change_fmt}}": stats.get("price_change_fmt", ""),
            "{{price_change_pct_signal}}": f"{stats.get('price_change_pct', 0):+.1f}",
            "{{min_price_fmt}}": stats.get("min_price_fmt", ""),
            "{{min_price_date_short}}": stats.get("min_price_date", "")[:10]
            if stats.get("min_price_date")
            else "",
            "{{current_installments}}": stats.get("current_installments", ""),
            "{{max_installments}}": stats.get("max_installments", ""),
            "{{max_installments_date_short}}": stats.get("max_installments_date", "")[
                :10
            ]
            if stats.get("max_installments_date")
            else "",
            "{{timestamps_json}}": timestamps_json,
            "{{prices_json}}": prices_json,
            "{{installments_json}}": installments_json,
            "{{products_json}}": products_json,
            "{{all_data_json}}": all_data_json,
            "{{default_product}}": default_name,
        }

        for placeholder, value in replacements.items():
            html_template = html_template.replace(placeholder, value)

        return html_template


def generate_dashboard(
    data_path: str = "data/products.json", output_path: str = "data/dashboard.html"
):
    generator = DashboardGenerator(Path(data_path))
    result = generator.generate(Path(output_path))
    print(f"✅ Dashboard gerado: {result}")
    return result


if __name__ == "__main__":
    generate_dashboard()
