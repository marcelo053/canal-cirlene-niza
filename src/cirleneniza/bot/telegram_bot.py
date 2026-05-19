import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from loguru import logger
from cirleneniza.config import get_settings
from cirleneniza.crew.video_crew import VideoCrew


settings = get_settings()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    await update.message.reply_text(
        "Olá! Sou a equipe da Cirlene Niza.\n\n"
        "Comandos disponíveis:\n"
        "/criar [tema] — Pipeline completo\n"
        "/roteiro [tema] — Só o roteiro\n"
        "/arte [descrição] — Arte avulsa\n"
        "/ajuda — Lista de comandos"
    )


async def ajuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /ajuda command."""
    await update.message.reply_text(
        "📋 *Comandos disponíveis:*\n\n"
        "`/criar [tema]` — Pesquisa + Roteiro + Revisão → vídeo final\n"
        "`/roteiro [tema]` — Gera só o roteiro para aprovação\n"
        "`/arte [descrição]` — Gera arte/avatar/logo\n"
        "`/thumbnail [tema]` — Gera thumbnail\n"
        "`/status` — Ver status do job atual\n"
        "`/ajuda` — Esta lista\n\n"
        "_Após `/roteiro`, use `/aprovar` para iniciar produção._",
        parse_mode="Markdown",
    )


async def criar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /criar command — full pipeline."""
    topic = ctx.args
    if not topic:
        await update.message.reply_text("Uso: /criar [tema do vídeo]")
        return

    topic = " ".join(topic)
    await update.message.reply_text(f"🔄 Iniciando produção: {topic}")

    try:
        crew = VideoCrew()
        result = crew.run(topic)
        video_line = f"\n🎥 Vídeo: {result['video_url']}" if result.get("video_url") else ""
        thumb_line = f"\n🖼️ Thumb: {result['thumbnail_url']}" if result.get("thumbnail_url") else ""
        await update.message.reply_text(
            f"✅ *Produção completa!*\n\n"
            f"🎬 {result['topic']}\n"
            f"🆔 production\\_id: {result.get('production_id', '—')}\n"
            f"📊 Status: {result['status']}{video_line}{thumb_line}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        await update.message.reply_text(f"❌ Erro: {str(e)}")


async def roteiro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /roteiro command — script only."""
    topic = ctx.args
    if not topic:
        await update.message.reply_text("Uso: /roteiro [tema]")
        return

    topic = " ".join(topic)
    await update.message.reply_text(f"📝 Gerando roteiro: {topic}")

    try:
        crew = VideoCrew()
        result = crew.run(topic)
        await update.message.reply_text(
            f"📝 *Roteiro gerado!*\n\n"
            f"Use `/aprovar` para iniciar produção.",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Erro ao gerar roteiro: {e}")
        await update.message.reply_text(f"❌ Erro: {str(e)}")


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command."""
    await update.message.reply_text(
        "📊 _Status da produção_\n\n"
        "Use `/roteiro [tema]` para gerar um roteiro.",
        parse_mode="Markdown",
    )


def run_bot():
    """Start the Telegram bot."""
    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("criar", criar))
    app.add_handler(CommandHandler("roteiro", roteiro))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ajuda", ajuda))

    logger.info("Telegram bot iniciado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()