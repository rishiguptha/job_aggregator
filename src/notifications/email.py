import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import requests
from src.config.settings import settings
from src.config.companies import COMPANY_SLUGS
from src.config.constants import PLATFORM_ICONS
from src.config.sponsors import H1B_SPONSORS
from src.utils.logger import get_logger

log = get_logger(__name__)

def _normalize_company(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = str(name).lower()
    name = re.sub(r'\b(inc\.?|llc|group|corp\.?|corporation|ltd\.?|limited|co\.?|company|services|holdings)\b', '', name)
    return re.sub(r'[^a-z0-9]', '', name)

def send_email(jobs: list[dict]):
    """Send formatted HTML email with job listings."""
    if not jobs:
        return

    primary = [j for j in jobs if j["match_type"] == "primary"]
    bonus = [j for j in jobs if j["match_type"] == "bonus"]
    now_ct = datetime.now(ZoneInfo("America/Chicago"))
    now_str = now_ct.strftime("%b %d, %Y at %I:%M %p") + " CT"
    platforms_hit = sorted(set(j["platform"] for j in jobs))
    total_companies = sum(len(v) for v in COMPANY_SLUGS.values())

    EXP_BADGE = {
        "🎓 New Grad": "background:#dcfce7;color:#166534",
        "📗 0-1 YoE": "background:#dcfce7;color:#166534",
        "📘 1-2 YoE": "background:#dbeafe;color:#1e40af",
        "✅ Open Level": "background:#d1fae5;color:#065f46",
        "🔶 3+ YoE": "background:#fef3c7;color:#92400e",
        "❓ Not Specified": "background:#f3f4f6;color:#6b7280",
    }

    def _card(idx, job, accent):
        icon = PLATFORM_ICONS.get(job["platform"], "")
        exp_val = job.get("experience")
        if exp_val:
            exp_text = f"{exp_val}+ yrs"
        elif exp_val == 0:
            exp_text = "Entry level"
        else:
            exp_text = "Not specified"
        exp_level = job.get("exp_level", "")
        badge_key = exp_level.replace(" (LLM)", "") if exp_level else ""
        s = EXP_BADGE.get(badge_key, "background:#f3f4f6;color:#6b7280")
        exp_pill = (
            f' <span style="display:inline-block;font-size:10px;padding:2px 8px;'
            f'border-radius:10px;{s}">{exp_level}</span>'
        ) if exp_level else ""
        sponsor = _normalize_company(job["company"]) in H1B_SPONSORS
        if sponsor:
            h1b_pill = (
                ' <span style="display:inline-block;font-size:10px;padding:2px 8px;'
                'border-radius:10px;background:#dcfce7;color:#166534">✅ H1B Sponsor</span>'
            )
        else:
            h1b_pill = (
                ' <span style="display:inline-block;font-size:10px;padding:2px 8px;'
                'border-radius:10px;background:#fef9c3;color:#854d0e">⚠️ Sponsorship Unknown</span>'
            )

        stack_pill = ""
        if not job.get("llm_stack_relevant", True):
            stack_pill = (
                ' <span style="display:inline-block;font-size:10px;padding:2px 8px;'
                'border-radius:10px;background:#fee2e2;color:#991b1b">⚡ Stack Mismatch</span>'
            )

        repost_pill = ""
        if job.get("reposted"):
            repost_pill = (
                ' <span style="display:inline-block;font-size:10px;padding:2px 8px;'
                'border-radius:10px;background:#ede9fe;color:#5b21b6">🔁 Reposted</span>'
            )

        posted = (
            f'<p style="margin:0;font-size:11px;color:#b0b0b0">'
            f'Posted {job["posted_at"][:10]}</p>'
        ) if job.get("posted_at") else ""

        return (
            f'<tr><td style="padding:0 24px 12px">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td style="border:1px solid #e5e7eb;border-left:3px solid {accent};'
            f'border-radius:6px;padding:16px 20px">'
            f'<p style="margin:0 0 6px;font-size:15px;font-weight:600;color:#111827">'
            f'#{idx} &mdash; {job["title"]}{repost_pill}</p>'
            f'<p style="margin:0 0 6px;font-size:13px;color:#6b7280">'
            f'{icon} {job["platform"].title()} &middot; '
            f'<span style="color:#374151;font-weight:600">{job["company"]}</span>'
            f' &middot; {job["location"]}</p>'
            f'<p style="margin:0 0 4px;font-size:12px;color:#9ca3af">'
            f'Exp: {exp_text}{exp_pill}{h1b_pill}{stack_pill}</p>'
            f'{posted}'
            f'<p style="margin:12px 0 0">'
            f'<a href="{job["url"]}" style="display:block;text-align:center;'
            f'background:{accent};color:#fff;padding:10px 0;border-radius:6px;'
            f'text-decoration:none;font-size:13px;font-weight:600">Apply Now &rarr;</a></p>'
            f'</td></tr></table></td></tr>'
        )

    parts = []

    parts.append(
        f'<html><head><meta charset="utf-8"></head>'
        f'<body style="margin:0;padding:0;background:#f3f4f6;'
        f"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif\">"
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f3f4f6">'
        f'<tr><td align="center" style="padding:32px 16px">'
        f'<table width="600" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:#fff;border-radius:8px;overflow:hidden">'
        f'<tr><td style="background:linear-gradient(135deg,#111827 0%,#1e293b 100%);'
        f'padding:36px 40px;text-align:center">'
        f'<p style="margin:0;font-size:28px;font-weight:700;color:#fff;letter-spacing:-0.5px">'
        f'&#x1F680; {len(jobs)} New Opportunities</p>'
        f'<p style="margin:8px 0 0;font-size:14px;color:#94a3b8;font-style:italic">'
        f'Fresh roles just dropped &mdash; be one of the first to apply.</p>'
        f'<p style="margin:12px 0 0;font-size:12px;color:#64748b">'
        f'{now_str} &middot; &le;{settings.MAX_EXPERIENCE_YEARS} yrs exp &middot; '
        f'{len(primary)} primary + {len(bonus)} bonus</p>'
        f'</td></tr>'
    )

    # Legend — pill grid
    def _legend_pill(text, style):
        return (
            f'<span style="display:inline-block;font-size:10px;padding:2px 8px;'
            f'border-radius:10px;{style}">{text}</span>'
        )

    LEGEND_ROWS = [
        # (pill_text, pill_style, description)
        ("🎓 New Grad",          "background:#dcfce7;color:#166534", "entry-level, no YoE"),
        ("📗 0-1 YoE",           "background:#dcfce7;color:#166534", "up to 1 yr required"),
        ("📘 1-2 YoE",           "background:#dbeafe;color:#1e40af", "1–2 yrs required"),
        ("✅ Open Level",         "background:#d1fae5;color:#065f46", "AI reviewed, suitable, no explicit years"),
        ("❓ Not Specified",      "background:#f3f4f6;color:#6b7280", "could not determine"),
        ("✅ H1B Sponsor",        "background:#dcfce7;color:#166534", "confirmed H1B sponsoring company"),
        ("⚠️ Sponsorship Unknown","background:#fef9c3;color:#854d0e", "not in sponsors list"),
        ("⚡ Stack Mismatch",     "background:#fee2e2;color:#991b1b", "role uses tech outside your stack"),
        ("🔁 Reposted",          "background:#ede9fe;color:#5b21b6", "seen in a previous email"),
    ]

    legend_items = "".join(
        f'<tr>'
        f'<td style="padding:3px 12px 3px 0;white-space:nowrap">{_legend_pill(text, style)}</td>'
        f'<td style="padding:3px 0;font-size:11px;color:#6b7280">{desc}</td>'
        f'</tr>'
        for text, style, desc in LEGEND_ROWS
    )

    parts.append(
        '<tr><td style="padding:20px 24px 8px">'
        '<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;padding:14px 18px">'
        '<p style="margin:0 0 10px;font-size:10px;font-weight:700;text-transform:uppercase;'
        'letter-spacing:1.2px;color:#9ca3af">Badge Guide</p>'
        f'<table cellpadding="0" cellspacing="0" border="0">{legend_items}</table>'
        '</td></tr></table>'
        '</td></tr>'
    )

    if primary:
        parts.append(
            '<tr><td style="padding:28px 24px 14px">'
            '<p style="margin:0;font-size:11px;font-weight:700;text-transform:uppercase;'
            'letter-spacing:1.5px;color:#2563eb">&#x1F3AF; Top Matches</p></td></tr>'
        )
        for i, job in enumerate(primary, 1):
            parts.append(_card(i, job, "#2563eb"))

    if bonus:
        parts.append(
            '<tr><td style="padding:20px 24px 14px">'
            '<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            '<td style="border-top:1px solid #e5e7eb;padding-top:20px">'
            '<p style="margin:0;font-size:11px;font-weight:700;text-transform:uppercase;'
            'letter-spacing:1.5px;color:#d97706">&#x1F4A1; More Opportunities</p>'
            '</td></tr></table></td></tr>'
        )
        for i, job in enumerate(bonus, len(primary) + 1):
            parts.append(_card(i, job, "#d97706"))

    parts.append(
        f'<tr><td style="padding:24px 24px;border-top:1px solid #e5e7eb;text-align:center">'
        f'<p style="margin:0;font-size:11px;color:#9ca3af">'
        f'Scanned {total_companies} companies across {", ".join(platforms_hit)}</p>'
        f'<p style="margin:4px 0 0;font-size:10px;color:#d1d5db">Job Aggregator v2</p>'
        f'</td></tr></table></td></tr></table></body></html>'
    )

    subject = f"🔔 {len(jobs)} New Jobs (JOB-AGGREGATOR) — {now_ct.strftime('%b %d, %I:%M %p')} CT"
    html_body = "\n".join(parts)

    if settings.EMAIL_BACKEND == "resend":
        _send_via_resend(subject, html_body, primary, bonus)
    else:
        _send_via_smtp(subject, html_body, primary, bonus)


def _send_via_smtp(subject: str, html_body: str, primary: list, bonus: list):
    """Send email via Gmail SMTP (port 465). Works locally and on GitHub Actions."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SENDER_EMAIL
    msg["To"] = ", ".join(settings.RECIPIENT_EMAILS)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, settings.RECIPIENT_EMAILS, msg.as_string())
        log.info(f"✅ Email sent (SMTP): {len(primary)} primary + {len(bonus)} bonus matches")
    except Exception as e:
        import traceback
        log.error(f"❌ Email failed (SMTP): {e}")
        log.error(traceback.format_exc())


def _send_via_resend(subject: str, html_body: str, primary: list, bonus: list):
    """Send email via Resend REST API (port 443). Works on DigitalOcean."""
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.SENDER_EMAIL,
                "to": settings.RECIPIENT_EMAILS,
                "subject": subject,
                "html": html_body,
            },
            timeout=15,
        )
        if resp.status_code in (200, 201):
            log.info(f"✅ Email sent (Resend): {len(primary)} primary + {len(bonus)} bonus matches")
        else:
            log.error(f"❌ Email failed (Resend): {resp.status_code} — {resp.text}")
    except Exception as e:
        import traceback
        log.error(f"❌ Email failed (Resend): {e}")
        log.error(traceback.format_exc())
