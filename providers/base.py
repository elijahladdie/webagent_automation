from abc import ABC, abstractmethod
from typing import Optional
from core.models import Plan, ParsedIntent, DomAction
from playwright.async_api import BrowserContext, async_playwright, Page
import os

class Provider(ABC):
    name: str
    storage_state: Optional[str] = None  # Optional path to persist login

    @abstractmethod
    async def plan(self, intent: ParsedIntent) -> Plan:
        ...

    @abstractmethod
    async def execute(self, ctx: BrowserContext, plan: Plan, dry_run: bool = False):
        ...

    # async
    async def new_page(self, ctx: BrowserContext) -> Page:
        """
        Open a new page using the shared browser context.
        """
        page = await ctx.new_page()
        await page.set_viewport_size({"width": 1360, "height": 900})
        # Basic anti-detection
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return page