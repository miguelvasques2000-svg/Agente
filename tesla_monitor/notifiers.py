"""Canais de notificação: Telegram e WhatsApp (via CallMeBot)."""
import logging

import requests

logger = logging.getLogger(__name__)


class Notifier:
    name = "base"

    def send(self, text: str):
        raise NotImplementedError


class TelegramNotifier(Notifier):
    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token or not chat_id:
            raise ValueError("Telegram requer bot_token e chat_id configurados")
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, text: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        resp = requests.post(
            url,
            data={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": "false",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


class CallMeBotWhatsAppNotifier(Notifier):
    """Usa o serviço gratuito CallMeBot (https://www.callmebot.com/blog/free-api-whatsapp-messages/)
    para enviar mensagens de WhatsApp para um número pessoal, sem precisar de conta Twilio/Meta Business.
    """

    name = "whatsapp_callmebot"

    def __init__(self, phone: str, apikey: str):
        if not phone or not apikey:
            raise ValueError("WhatsApp (CallMeBot) requer phone e apikey configurados")
        self.phone = phone
        self.apikey = apikey

    def send(self, text: str):
        url = "https://api.callmebot.com/whatsapp.php"
        resp = requests.get(
            url,
            params={"phone": self.phone, "text": text, "apikey": self.apikey},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.text


def build_notifiers(cfg: dict) -> list:
    notifiers = []
    notify_cfg = (cfg or {}).get("notify", {}) or {}

    tg = notify_cfg.get("telegram", {}) or {}
    if tg.get("enabled"):
        try:
            notifiers.append(TelegramNotifier(tg.get("bot_token"), tg.get("chat_id")))
        except ValueError as exc:
            logger.error("Telegram mal configurado: %s", exc)

    wa = notify_cfg.get("whatsapp_callmebot", {}) or {}
    if wa.get("enabled"):
        try:
            notifiers.append(CallMeBotWhatsAppNotifier(wa.get("phone"), wa.get("apikey")))
        except ValueError as exc:
            logger.error("WhatsApp mal configurado: %s", exc)

    if not notifiers:
        logger.warning("Nenhum canal de notificação está ativo em config.yaml")

    return notifiers
