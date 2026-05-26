from aiogram import Router

from handlers.subscription_gate import router as subscription_gate_router
from handlers.admin_dashboard import router as admin_dashboard_router
from handlers.admin import router as admin_router
from handlers.application import router as application_router
from handlers.payout import router as payout_router
from handlers.progress import router as progress_router
from handlers.menu import router as menu_router
from handlers.offers import router as offers_router
from handlers.onboarding import router as onboarding_router
from handlers.profile import router as profile_router
from handlers.start import router as start_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(subscription_gate_router)
    root.include_router(start_router)
    root.include_router(onboarding_router)
    root.include_router(menu_router)
    root.include_router(offers_router)
    root.include_router(profile_router)
    root.include_router(application_router)
    root.include_router(progress_router)
    root.include_router(payout_router)
    root.include_router(admin_dashboard_router)
    root.include_router(admin_router)
    return root
