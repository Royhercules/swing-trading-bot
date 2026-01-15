import smtplib
import os
from email.message import EmailMessage

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")

def send_email(signals, charts, market_fail=False):
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    if market_fail:
        msg["Subject"] = "🚫 Swing Trades Skipped – Market Not Favorable"
        msg.set_content("NIFTY below 200 SMA or VIX above 20.\nNo trades today.")
    else:
        msg["Subject"] = "📈 Swing Trade Signals (15–30 Days)"
        body = "Top Swing Trade Candidates:\n\n"
        for s in signals:
            body += f"{s['Symbol']} | Entry {s['Entry']} | SL {s['SL']} | Target {s['Target']}\n"
        msg.set_content(body)

        for c in charts:
            with open(c, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="png",
                    filename=c
                )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
