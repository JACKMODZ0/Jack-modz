import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "7840587350:AAGq_IH6ZM2IOVD9Ih1rnzWdOauUCf42we4" 
PING_INTERVAL = 3600  # 1 hour

codespace_url = None
chat_id = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🤖 Bot ready!\n\n"
        "Codespace URL set karne ke liye:\n"
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
        f"✅ URL set ho gaya:\n{codespace_url}\n\n"
        "Ab har 1 ghante ping status bheja jayega."
    )

async def ping_codespace(app):
    global codespace_url, chat_id

    while True:
        if codespace_url and chat_id:
            try:
                r = requests.get(codespace_url, timeout=15)
                if r.status_code == 200:
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ Ping SUCCESS\n{codespace_url}\nStatus: {r.status_code}"
                    )
                else:
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ Ping FAILED\n{codespace_url}\nStatus: {r.status_code}"
                    )

            except Exception as e:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Ping ERROR\n{codespace_url}\nError: {str(e)}"
                )
        else:
            print("[WAIT] URL ya chat_id set nahi")

        await asyncio.sleep(PING_INTERVAL)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("seturl", seturl))

    asyncio.create_task(ping_codespace(app))

    print("✅ Bot running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
