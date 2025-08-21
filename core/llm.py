import os, re, json
from typing import Optional
from pydantic import ValidationError
from openai import OpenAI
from .models import ParsedIntent

_client = None

def _client_lazy():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

_EXTRACT_SYS = (
    "You extract JSON with keys: recipient (email), recipient_name (if guessable), "
    "subject (optional), message (string). "
    "If subject is missing, infer a concise one (<=8 words). "
    "If recipient_name is missing, try to infer it from the email (e.g., dana@example.com → Dana). "
    "Return ONLY JSON."
)
def extract_name_from_email(email: str) -> str:
    local_part = email.split('@')[0]
    name_guess = local_part.split('.')[0]  # e.g., "dana.smith" → "dana"
    return name_guess.capitalize()

def extract_intent(text: str) -> ParsedIntent:
    try:
        c = _client_lazy()
        resp = c.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _EXTRACT_SYS},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        return ParsedIntent(**data)
    except Exception:
        # Safe regex fallback (very simple)
        email = re.search(r"[\w.\-+]+@[\w.\-]+", text)
        msg_match = re.search(r"saying\s+'([^']+)'|saying\s+\"([^\"]+)\"|: (.+)$", text, re.I)
        message = (
            (msg_match.group(1) or msg_match.group(2) or msg_match.group(3)).strip()
            if msg_match else text
        )
        subject = None
        if "subject" in text.lower():
            m = re.search(r"subject\s*[:\-]\s*(.+)$", text, re.I)
            if m: subject = m.group(1).strip()
        if not email:
            raise ValidationError("Could not find recipient email in instruction.")
        return ParsedIntent(recipient=email.group(0), subject=subject, message=message)

_PARAPHRASE_SYS = (
    "Rewrite the message to be professional, clear, positive, and concise."
)

def paraphrase(message: str) -> str:
    try:
        c = _client_lazy()
        resp = c.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _PARAPHRASE_SYS},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return message