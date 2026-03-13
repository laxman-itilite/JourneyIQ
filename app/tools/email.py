"""Send support email to Itilite support when connect_to_human is triggered."""

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SUPPORT_EMAIL, SUPPORT_CC

logger = logging.getLogger(__name__)

_HEADER_IMG = "https://d2n81k4sk1bpk1.cloudfront.net/itilite-images/email_header_banner.png"


def _build_history_html(messages: list, user_id: str = "") -> str:
    rows = []
    user_label = user_id or "User"
    for msg in messages:
        if msg.role == "user":
            bg, label, color = "#f0f0f0", user_label, "#333333"
        else:
            bg, label, color = "#fff4f0", "Assistant", "#ec5d25"
        text = msg.content.replace("\n", "<br>")
        rows.append(
            f'<tr><td style="padding:8px 12px;background:{bg};'
            f'border-bottom:1px solid #e8e8e8;'
            f'font-family:Roboto,Helvetica,Arial,sans-serif;font-size:13px;color:#333">'
            f'<strong style="color:{color}">{label}</strong><br>{text}</td></tr>'
        )
    return "".join(rows)


def _build_history_plain(messages: list) -> str:
    lines = []
    for msg in messages:
        label = "User" if msg.role == "user" else "Assistant"
        lines.append(f"[{label}]: {msg.content}")
    return "\n".join(lines)


def _build_html(user_id: str, summary: str, messages: list | None = None, request_type: str = "support") -> str:
    is_modification = request_type == "modification"
    heading = "Modification Request" if is_modification else "Support Request"
    intro = (
        "A traveller has submitted a modification request via the JourneyIQ chat assistant. "
        "Please review and process at your earliest convenience."
        if is_modification else
        "A traveller has requested human assistance via the JourneyIQ chat assistant "
        "and has been redirected to you."
    )
    summary_label = "Modification Details" if is_modification else "Conversation Summary"
    summary_html = (summary or "No summary provided.").replace("\n", "<br>")
    if messages:
        history_section = (
            '<p style="margin:0 0 6px 0;font-weight:bold;color:#ec5d25">Chat History</p>'
            '<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"'
            ' style="border:1px solid #e8e8e8;margin-bottom:20px"><tbody>'
            + _build_history_html(messages, user_id)
            + "</tbody></table>"
        )
    else:
        history_section = ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{heading} - ITILITE</title>
</head>
<body>
  <center style="width:100%;background-color:#eeeeee">
    <div style="width:660px;margin:0 auto;border:1px solid #eeeeee">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin:auto">
        <tbody>

          <!-- Header banner -->
          <tr>
            <td style="background-color:#ffffff;text-align:center;padding:0">
              <img src="{_HEADER_IMG}" width="100%" height="auto" alt="ITILITE"
                   style="display:block;height:auto;background:#dddddd;
                          font-family:Roboto,Helvetica,Arial,sans-serif;
                          font-size:12px;line-height:15px;color:#4e4e4e">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="background-color:#ffffff;padding:20px 15px 10px 15px;
                       font-family:Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#000000">
              <p style="margin:0 0 10px 0">Hi Support Team,</p>
              <p style="margin:0 0 16px 0">{intro}</p>

              <!-- User info box -->
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                     style="background:#f8f8f8;border-left:4px solid #ec5d25;margin-bottom:16px">
                <tr>
                  <td style="padding:12px 15px;font-family:Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#000">
                    <strong style="color:#ec5d25">Traveller</strong><br>
                    <span style="color:#333">{user_id}</span>
                  </td>
                </tr>
              </table>

              <!-- Summary box -->
              <p style="margin:0 0 6px 0;font-weight:bold;color:#ec5d25">{summary_label}</p>
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                     style="background:#fff9f7;border:1px solid #f0d5cb;margin-bottom:20px">
                <tr>
                  <td style="padding:12px 15px;font-family:Roboto,Helvetica,Arial,sans-serif;
                             font-size:14px;line-height:1.6;color:#333">
                    {summary_html}
                  </td>
                </tr>
              </table>

              <!-- Chat history -->
              {history_section}
            </td>
          </tr>

          <!-- Sign-off -->
          <tr>
            <td style="padding:12px 15px;background-color:#ffffff;
                       font-family:Roboto,Helvetica,Arial,sans-serif;font-size:15px;
                       line-height:1.5;color:#4e4e4e">
              <p style="margin:0">Thanks,</p>
              <p style="margin:0">The ITILITE Team</p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:12px 15px;background-color:#ffffff;
                       font-family:Roboto,Helvetica,Arial,sans-serif;font-size:14px;color:#4e4e4e">
              Need help? Reach out to us at
              <a href="https://www.itilite.com/faq/contact-us/"
                 style="color:#ec5d25;text-decoration:underline">
                www.itilite.com/faq/contact-us/
              </a>
            </td>
          </tr>

        </tbody>
      </table>
    </div>
  </center>
</body>
</html>"""


def _send_smtp(to: str, subject: str, user_id: str, summary: str, messages: list, request_type: str = "support") -> None:
    """Blocking SMTP send — called via asyncio.to_thread."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to
    if SUPPORT_CC:
        msg["Cc"] = SUPPORT_CC

    history_plain = _build_history_plain(messages) if messages else ""
    plain = (
        f"Hi Support Team,\n\n"
        f"A traveller has requested human assistance.\n\n"
        f"Traveller: {user_id}\n\n"
        f"Conversation Summary:\n{summary or 'No summary provided.'}\n\n"
        + (f"Chat History:\n{history_plain}\n\n" if history_plain else "")
        + "Thanks,\nThe ITILITE Team"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_html(user_id, summary, messages, request_type), "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        if SMTP_PORT == 587:
            server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        recipients = [to] + ([SUPPORT_CC] if SUPPORT_CC else [])
        server.sendmail(SMTP_USER, recipients, msg.as_string())


async def send_support_email(user_id: str, summary: str, messages: list | None = None, request_type: str = "support") -> bool:
    """Send a branded support/modification email. Returns True on success."""
    label = "Modification Request" if request_type == "modification" else "Support Request"
    subject = f"{label} – {user_id}"
    try:
        await asyncio.to_thread(_send_smtp, SUPPORT_EMAIL, subject, user_id, summary, messages or [], request_type)
        logger.info("Support email sent for user %s", user_id)
        return True
    except Exception as exc:
        logger.error("Failed to send support email for user %s: %s", user_id, exc)
        return False
