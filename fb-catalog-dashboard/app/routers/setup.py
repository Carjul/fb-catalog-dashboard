from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse

from .. import meta_api
from ..database import MongoSession, get_db
from ..models import AppSettings
from ..config import FB_ACCESS_TOKEN

router = APIRouter()


def _get_settings(db: MongoSession) -> AppSettings:
    s = db.query(AppSettings).first()
    if not s:
        s = AppSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("/setup")
def setup_page(request: Request, db: MongoSession = Depends(get_db)):
    s = _get_settings(db)
    accounts, pages, businesses, pixels = [], [], [], []
    errors = []

    if FB_ACCESS_TOKEN:
        try:
            accounts = meta_api.list_ad_accounts()
        except Exception as e:
            errors.append(f"Ad accounts: {e}")
        try:
            pages = meta_api.list_pages()
        except Exception as e:
            errors.append(f"Páginas: {e}")
        try:
            businesses = meta_api.list_businesses()
        except Exception as e:
            errors.append(f"Business Managers: {e}")
        if s.default_ad_account_id:
            try:
                pixels = meta_api.list_pixels(s.default_ad_account_id)
            except Exception as e:
                errors.append(f"Pixeles: {e}")

    return request.app.state.templates.TemplateResponse(request, "setup.html", {
        "request": request, "settings": s,
        "accounts": accounts, "pages": pages,
        "businesses": businesses, "pixels": pixels,
        "error": " | ".join(errors) if errors else None,
        "token_set": bool(FB_ACCESS_TOKEN),
    })


@router.post("/setup")
def setup_save(
    db: MongoSession = Depends(get_db),
    business_id: str = Form(""),
    ad_account_id: str = Form(""),
    page_id: str = Form(""),
    pixel_id: str = Form(""),
    telegram_bot_token: str = Form(""),
    telegram_chat_id: str = Form(""),
    slack_webhook_url: str = Form(""),
    notify_on_approval: str = Form(""),
    notify_on_conversion: str = Form(""),
):
    s = _get_settings(db)
    s.default_business_id = business_id or None
    s.default_ad_account_id = ad_account_id or None
    s.default_page_id = page_id or None
    s.default_pixel_id = pixel_id or None
    s.telegram_bot_token = telegram_bot_token or None
    s.telegram_chat_id = telegram_chat_id or None
    s.slack_webhook_url = slack_webhook_url or None
    s.notify_on_approval = (notify_on_approval == "yes")
    s.notify_on_conversion = (notify_on_conversion == "yes")
    if FB_ACCESS_TOKEN:
        s.fb_token_last4 = FB_ACCESS_TOKEN[-4:]
    db.commit()
    return RedirectResponse("/setup?saved=1", status_code=303)


@router.post("/setup/test-notification")
def test_notification():
    from .. import notifier
    res = notifier.send_test("Test desde FB Catalog Dashboard — si ves esto, las notificaciones funcionan.")
    return RedirectResponse(f"/setup?test_telegram={int(res['telegram'])}&test_slack={int(res['slack'])}", status_code=303)
