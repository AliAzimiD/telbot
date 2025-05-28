from telegram.ext import Application, CommandHandler, MessageHandler, filters
from commands import query_handler
from config import config

app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

# /start
async def start(update, _):
    await update.message.reply_text(
        "Hi! Ask me questions about the dataset – e.g. "
        "“how many rows”, “plot gender distribution”, …"
    )

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("query", query_handler.handle))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, query_handler.handle))

if __name__ == "__main__":
    app.run_polling()
