from playwright.async_api import BrowserContext
from core.models import Plan, ParsedIntent, DomAction
from .base import Provider

GMAIL = "https://mail.google.com/mail/u/0/#inbox"

class GmailProvider(Provider):
    name = "gmail"

    async def plan(self, intent: ParsedIntent) -> Plan:
        actions = [
            DomAction(description="Open compose", locator="div[role='button'][gh='cm']", action="click"),
            DomAction(description="Fill To", locator="input[aria-label='To recipients']", action="type", value=intent.recipient),
            DomAction(description="Fill Subject", locator="input[name='subjectbox']", action="fill", value=intent.subject or ""),
            DomAction(description="Fill Body", locator="div[aria-label='Message Body']", action="type", value=intent.message),
            DomAction(description="Send", locator="div[role='button'][data-tooltip*='Send']", action="click"),
        ]
        return Plan(provider=self.name, actions=actions)

    async def execute(self, ctx: BrowserContext, plan: Plan, dry_run: bool = False):
        page = await self.new_page(ctx)

        print("[DEBUG] Navigating to Gmail inbox...")
        await page.goto(GMAIL)
        print("[DEBUG] Checking if Gmail is asking for login...")
        try:
            # Wait for either login input or sidebar
            await page.wait_for_selector(
                "div[role='navigation'], input[type='email'], #identifierId",
                timeout=30000
            )
        except:
            print("[ERROR] Gmail did not respond at all within 30s.")
            return

        # If login is showing, wait up to 5 minutes for sidebar
        if await page.locator("input[type='email'], #identifierId").is_visible():
            print("[INFO] Gmail login detected. Waiting up to 5 minutes for login to complete...")
            try:
                await page.wait_for_selector("div[role='navigation']", timeout=300000)  # 5 min
                print("[DEBUG] Login completed, inbox loaded.")
            except:
                print("[ERROR] Login did not finish within 5 minutes.")
                return
        else:
            print("[DEBUG] Sidebar loaded without login prompt.")
        # Open compose fallback if not visible
        compose_selector = "div[role='button'][gh='cm']"
        compose_button = page.locator(compose_selector).first
        if not await compose_button.is_visible():
            print("[WARN] Compose button not found, trying direct compose URL...")
            await page.goto(GMAIL + "?compose=new")
        else:
            print("[DEBUG] Compose button found.")

        # Run planned actions
        for step_num, a in enumerate(plan.actions, start=1):
            print(f"[DEBUG] Step {step_num}: {a.description} (locator={a.locator})")
            loc = page.locator(a.locator).first
            try:
                await loc.wait_for(state="visible", timeout=20000)
                print(f"[DEBUG] Locator ready: {a.locator}")
                if not dry_run:
                    if a.action == "click":
                        await loc.click()
                        print(f"[DEBUG] Clicked: {a.description}")
                    elif a.action == "fill":
                        await loc.fill(a.value or "")
                        print(f"[DEBUG] Filled with: {a.value}")
                    elif a.action == "type":
                        await loc.click() 
                        await loc.type(a.value or "", delay=100)
                        print(f"[DEBUG] Typed: {a.value}")
            except Exception as e:
                print(f"[ERROR] Failed at step '{a.description}': {e}")

        if dry_run:
            await page.close()
