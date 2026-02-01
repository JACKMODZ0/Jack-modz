import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

PING_INTERVAL = 3600  # 1 hour

codespace_url = None
chat_id = None

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway variable

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🤖 Bot started!\n\n"
        "URL set karne ke liye:\n"
        "/seturl https://your-codespace-url"
    )

async def seturl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global codespace_url

    if not context.args:
        await update.message.reply_text(
            "❌ URL missing hai\n\n"
            "Example:\n/seturl https://xxxxx.app.github.dev"
        )
        return

    codespace_url = context.args[0]
    await update.message.reply_text(
        f"✅ URL saved:\n{codespace_url}\n\n"
        "Ab har 1 ghante ping status aayega."
    )

async def ping_job(app: Application):
    global codespace_url, chat_id

    while True:
        if codespace_url and chat_id:
            try:
                r = requests.get(codespace_url, timeout=15)

                if r.status_code == 200:
                    msg = f"✅ Ping SUCCESS\n{codespace_url}\nStatus: 200"
                else:
                    msg = f"⚠️ Ping FAILED\n{codespace_url}\nStatus: {r.status_code}"

            except Exception as e:
                msg = f"❌ Ping ERROR\n{codespace_url}\n{e}"

            await app.bot.send_message(chat_id=chat_id, text=msg)
        else:
            print("⏳ Waiting for /seturl")

        await asyncio.sleep(PING_INTERVAL)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("seturl", seturl))

    asyncio.create_task(ping_job(app))

    print("✅ Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
