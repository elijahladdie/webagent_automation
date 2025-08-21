# Email Automation Agent (Playwright + LLM)

Automate a single goal — **send an email** — across **Gmail Web** and **Outlook Web** using a unified interface, LLM reasoning, and Playwright browser automation.

## ✅ Features

* Accepts **natural‑language** instruction, e.g.:

  ```bash
  python agent.py "send email to joe@example.com saying 'Hello from my automation system'"
  ```
* Uses an **LLM (OpenAI)** to:

  * Extract recipient, subject (optional), and message
  * Paraphrase the message to be more professional & positive
  * (Optional) Pick a provider if `--provider auto`
* Automates UI in a **real browser** with **Playwright**
* Works with **two providers** (Gmail Web, Outlook Web) via a **unified Provider interface**
* **Manual or persistent login** (no credentials stored in code)
* Structured **logging** to JSONL
* **Dry‑run** mode to preview steps without sending

## 🧱 Project Structure

```
.
├─ agent.py                # Entry point (CLI & orchestration)
├─ core/
│  ├─ models.py            # Pydantic models for instruction/plan/actions
│  ├─ llm.py               # Extraction + paraphrase (OpenAI) with safe fallbacks
│  ├─ browser.py           # Playwright helpers & context management
│  └─ logger.py            # JSONL structured logging
├─ providers/
│  ├─ base.py              # Provider protocol
│  ├─ gmail.py             # Gmail implementation
│  └─ outlook.py           # Outlook implementation
├─ .env.example            # Env vars template
├─ requirements.txt
└─ README.md               # (this file)
```


## ⚙️ Setup

1. **Python & dependencies**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

2. **Environment variables**

Create a `.env` (copy from `.env.example`):

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# Optional: to persist login sessions per provider
USER_DATA_DIR=.user-data
```

3. **First-time login** (manual, one-time per provider)

* The agent will launch a real browser.
* It pauses for you to log in (or it reuses a persistent profile if `USER_DATA_DIR` is set).
* After successful login, the session is reused next time.

## 🚀 Usage

### Simple (auto provider)

```bash
python agent.py "send email to alice@example.com about the meeting at 2pm"
```

### Explicit provider

```bash
python agent.py "Send email to bob@example.com saying 'Hello!'" --provider gmail
python agent.py "Send email to bob@example.com saying 'Hello!'" --provider outlook
```

### Dry run (no send)

```bash
python agent.py "email charlie@example.com: project update" --dry-run
```

### Subject override

```bash
python agent.py "send email to dana@example.com saying 'quick note'" --subject "Follow-up on our chat"
```


## 🔐 Authentication Notes

* This demo **does not store credentials**.
* Use the browser window to login once; the persistent profile keeps you signed in (if `USER_DATA_DIR` is set).
* For CI or fully headless setups, integrate org SSO or cookies vault (out of scope for this prototype).

## 🧠 Reasoning Flow (LLM + Planner)

1. **Parse instruction** → `{recipient, subject?, message}`
2. **Paraphrase message** → polite, concise, positive
3. **Provider select** → `--provider` flag or `auto`
4. **Plan DOM steps** (provider-specific adapter)
5. **Execute steps** via Playwright
6. **Log** every step + final status to `runs.jsonl`

## 🔍 Notes on Selectors & Stability

* **Gmail**

  * Compose: `#inbox?compose=new` or `a[href*='#compose']`
  * To: `textarea[name='to']`
  * Subject: `input[name='subjectbox']`
  * Body: `div[aria-label='Message Body']`
  * Send: `div[role='button'][data-tooltip*='Send']`
* **Outlook Web**

  * New mail: `button[aria-label='New mail']`
  * To: `div[aria-label='To'] input` (people picker accepts typing + Enter)
  * Subject: `input[aria-label='Add a subject']`
  * Body: `div[aria-label='Message body']`
  * Send: `button[aria-label='Send']`

> Real UIs evolve. Keep adapters versioned; prefer `aria-*` and role-based selectors.

## 📄 .env.example

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
USER_DATA_DIR=.user-data
```