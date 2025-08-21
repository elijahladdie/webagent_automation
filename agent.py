import asyncio, os
import typer
from dotenv import load_dotenv
from rich import print
from core.models import Instruction
from core.llm import extract_intent, paraphrase
from core.browser import browser_context
from core.logger import log_json
from providers.gmail import GmailProvider
from providers.outlook import OutlookProvider

app = typer.Typer(add_completion=False)

PROVIDERS = {
    "gmail": GmailProvider(),
    "outlook": OutlookProvider(),
}

def choose_provider(name: str):
    name = (name or "auto").lower()
    if name in PROVIDERS:
        return PROVIDERS[name]

    return PROVIDERS["gmail"]

@app.command()
def run(
    instruction: str = typer.Argument(..., help="Natural language goal"),
    provider: str = typer.Option("auto", help="gmail|outlook|auto"),
    subject: str = typer.Option(None, help="Override subject"),
    dry_run: bool = typer.Option(False, help="Plan only; don't click/send"),
):
    """Execute a single goal-oriented task: send an email across multiple web UIs."""
    load_dotenv()
    ins = Instruction(raw=instruction, provider=provider or "auto", subject_override=subject)
    # 1) Parse & paraphrase
    parsed = extract_intent(ins.raw)
    # If subject override is provided, use it
    if ins.subject_override:
        parsed.subject = ins.subject_override
    # If no subject extracted, fallback to default
    if not parsed.subject:
        parsed.subject = "Quick note"
    # get recipient name from email if not provided
    if not getattr(parsed, "recipient_name", None):
        local_part = parsed.recipient.split("@")[0]
        guessed_name = local_part.split(".")[0].capitalize()
        parsed.recipient_name = guessed_name
    # Paraphrase the message 
    polished = paraphrase(parsed.message)
    # 2) Provider
    prov = choose_provider(ins.provider)
    # 3) Plan
    plan = asyncio.run(prov.plan(parsed)) if asyncio.get_event_loop().is_running() else asyncio.run(async_plan(prov, parsed))
    # 4) Execute
    status, err = "planned", None
    try:
        asyncio.run(execute_with_browser(prov.name, prov, plan, dry_run))
        status = "executed" if not dry_run else "planned"
        print(f"[bold green]Success[/bold green]: Provider={prov.name} DryRun={dry_run}")
    except Exception as e:
        status, err = "failed", str(e)
        print(f"[bold red]Failed[/bold red]: {e}")
    # 5) Log
    log_json({
        "provider": prov.name,
        "raw_instruction": ins.raw,
        "parsed": parsed.model_dump(),
        "paraphrased_message": polished,
        "subject": parsed.subject,
        "status": status,
        "error": err,
    })

def _update_intent(parsed, polished):
    parsed.message = polished.replace("[Recipient's Name]", parsed.recipient_name).replace("[Your Name]", 'Elijah')
    return parsed

async def async_plan(prov, parsed):
    parsed = _update_intent(parsed, paraphrase(parsed.message))
    return await prov.plan(parsed)

async def execute_with_browser(name, prov, plan, dry_run):
    from core.models import Plan as PlanType
    assert isinstance(plan, PlanType)
    async with browser_context(name) as ctx:
        await prov.execute(ctx, plan, dry_run)

if __name__ == "__main__":
    app()