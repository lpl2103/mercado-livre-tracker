# src/notifier.py
import smtplib
from decimal import Decimal
from email.message import EmailMessage
from typing import Optional

# Fallback silencioso se win10toast não estiver disponível
try:
    from win10toast import ToastNotifier

    WINDOWS_TOAST_AVAILABLE = True
except ImportError:
    WINDOWS_TOAST_AVAILABLE = False


class PriceNotifier:
    """Observer simplificado - reage a mudanças de preço/parcelas."""

    def __init__(
        self, email_config: Optional[dict] = None, windows_notification: bool = True
    ):
        self.email_config = email_config
        self.windows_notification = windows_notification
        self.toaster = (
            ToastNotifier()
            if WINDOWS_TOAST_AVAILABLE and windows_notification
            else None
        )

    def check_and_notify(self, current: dict, previous: Optional[dict]) -> None:
        """Compara snapshots e dispara alertas se houver melhoria."""
        if previous is None:
            return  # Primeira execução, sem base de comparação

        curr_price = Decimal(current["price"])
        prev_price = Decimal(previous["price"])

        message_parts = []

        if curr_price < prev_price:
            message_parts.append(
                f"💰 Preço caiu! De R$ {prev_price} para R$ {curr_price}"
            )

        # Extrai número de parcelas da string
        curr_installments = self._parse_installments_count(current["installments"])
        prev_installments = self._parse_installments_count(previous["installments"])

        if curr_installments > prev_installments:
            message_parts.append(
                f"📊 Parcelas aumentaram de {prev_installments}x para {curr_installments}x"
            )

        if message_parts:
            self._send_alert("\n".join(message_parts))

    def _parse_installments_count(self, text: str) -> int:
        """Extrai número de parcelas da string '12x R$ 100,00' -> 12."""
        import re

        match = re.match(r"(\d+)x", text.strip())
        return int(match.group(1)) if match else 0

    def _send_alert(self, message: str) -> None:
        """Dispara notificações assíncronas - email + Windows toast."""
        if self.toaster:
            self.toaster.show_toast(
                "Mercado Livre Tracker",
                message,
                duration=10,
                threaded=True,  # Não bloqueia o scheduler
            )

        if self.email_config:
            self._send_email(message)

    def _send_email(self, body: str) -> None:
        """SMTP com TLS - sem libs externas, zero dependências extras."""
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = "Alerta de Preço - Mercado Livre"
        msg["From"] = self.email_config["from"]
        msg["To"] = self.email_config["to"]

        with smtplib.SMTP(
            self.email_config["smtp_server"], self.email_config["smtp_port"]
        ) as server:
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            server.send_message(msg)
