import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
PING_INTERVAL = 3600  # 1 hour

codespace_url = None
chat_id = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "🤖 Bot started\n\n/seturl <your_url>"
    )

async def seturl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global codespace_url
    if not context.args:
        await update.message.reply_text("❌ URL missing")
        return
    codespace_url = context.args[0]
    await update.message.reply_text(f"✅ URL saved:\n{codespace_url}")

async def ping_loop(app: Application):
    while True:
        if codespace_url and chat_id:
            try:
                r = requests.get(codespace_url, timeout=15)
                msg = f"✅ Ping SUCCESS ({r.status_code})" if r.status_code == 200 else f"⚠️ Ping FAIL ({r.status_code})"
            except Exception as e:
                msg = f"❌ Ping ERROR\n{e}"

            await app.bot.send_message(chat_id, msg)

        await asyncio.sleep(PING_INTERVAL)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("seturl", seturl))

    asyncio.create_task(ping_loop(app))

    print("✅ Bot running")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
