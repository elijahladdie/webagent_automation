from playwright.async_api import BrowserContext
from core.models import Plan, ParsedIntent, DomAction
from .base import Provider

OUTLOOK = "https://outlook.live.com/mail/0/"

class OutlookProvider(Provider):
    name = "outlook"

    async def plan(self, intent: ParsedIntent) -> Plan:
        actions = [
            DomAction(description="Open compose", locator="button[aria-label*='New mail']", action="click"),
            # DomAction(description="Click To", locator="button[aria-roledescription*='Add recipients']", action="click"),
            DomAction(description="Fill To",locator="div[role='textbox'][aria-label='To']",action="type",value=intent.recipient),
            DomAction(description="Fill Subject", locator="input[placeholder='Add a subject']", action="fill", value=intent.subject or ""),
            DomAction(description="Fill Body", locator="div[aria-label='Message body']", action="type", value=intent.message),
            DomAction(description="Send", locator="button[title*='Send']", action="click"),
        ]
        return Plan(provider=self.name, actions=actions)

    async def execute(self, ctx: BrowserContext, plan: Plan, dry_run: bool = False):
        page = await self.new_page(ctx)

        print("[DEBUG] Navigating to Outlook...")
        await page.goto(OUTLOOK)

        # print("[DEBUG] Waiting for Outlook mailbox to load...")
        # try:
        #     await page.wait_for_selector("div[role='navigation']", timeout=30000)
        #     print("[DEBUG] Mailbox loaded.")
        # except:
        #     print("[ERROR] Outlook did not fully load. Capturing snapshot...")
         
        print("[DEBUG] Checking if Outlook requires login...")
        try:
            # Wait for either login input or mailbox sidebar
            await page.wait_for_selector(
                "div[role='navigation'], input[type='email'], #i0116",
                timeout=30000
            )
        except:
            print("[ERROR] Outlook did not respond within 30s.")
            return

        # If login input detected, wait up to 5 minutes for mailbox
        if await page.locator("input[type='email'], #i0116").is_visible():
            print("[INFO] Outlook login detected. Waiting up to 5 minutes for login to complete...")
            try:
                await page.wait_for_selector("div[role='navigation']", timeout=300000)  # 5 minutes
                print("[DEBUG] Login completed, mailbox loaded.")
            except:
                print("[ERROR] Login did not finish within 5 minutes.")
                return
        else:
            print("[DEBUG] Mailbox loaded without login prompt.")
        # Fallback: Ensure compose button is visible
        compose_selector = "button[aria-label*='New mail']"
        compose_button = page.locator(compose_selector).first
        if not await compose_button.is_visible():
            print("[WARN] Compose button not found, trying to refresh...")
            await page.reload()
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
                        await loc.click()  # focus
                        await loc.type(a.value or "", delay=80)
                        try:
                            await page.keyboard.press("Enter")
                        except:
                            print("[WARN] Could not press Enter after typing.")
            except Exception as e:
                print(f"[ERROR] Failed at step '{a.description}': {e}")

        if dry_run:
            await page.close()
            print("[DEBUG] Dry run complete, page closed.")
