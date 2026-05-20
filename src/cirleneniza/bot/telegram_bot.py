import asyncio
import uuid
import time
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)
from loguru import logger
from cirleneniza.config import get_settings
from cirleneniza.agents.calendario import CalendarioEditorial
from cirleneniza.agents.roteirista import RoteiristaCirleneNiza
from cirleneniza.agents.revisor import RevisorEspecialista
from cirleneniza.agents.diretor_arte import DiretorDeArte
from cirleneniza.tools.baserow import BaserowClient

settings = get_settings()

# command timeout in seconds
_CMD_TIMEOUT = 120

_sessions: dict[int, dict] = {}


def _s(user_id: int) -> dict:
    if user_id not in _sessions:
        _sessions[user_id] = {
            "topic": None,
            "research": None,
            "style_guide": None,
            "script_data": None,
            "thumbnail_url": None,
            "production_id": None,
            "step": None,
        }
    return _sessions[user_id]


def _t(text: str, max_chars: int) -> str:
    """Escape and truncate user content for safe plain-text Telegram output."""
    if not text:
        return ""
    text = text.replace("*", "#").replace("_", "-").replace("`", "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Canal Cirlene Niza - Pipeline de Producao\n\n"
        "Comandos:\n"
        "/novo [tema] - Iniciar video\n"
        "/validar_tema - Ver research e style guide\n"
        "/roteiro - Gerar roteiro (intro/main/outro)\n"
        "/validar_roteiro - Ver roteiro completo\n"
        "/corrigir [instrucao] - Corrigir parte do roteiro\n"
        "/gerar_thumbnail - Gerar thumbnail\n"
        "/thumbnail_novo [ajuste] - Regenerar thumbnail\n"
        "/produzir - Iniciar producao\n"
        "/status - Ver estado atual",
    )


async def cmd_ajuda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


async def cmd_novo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else None
    if not topic:
        await update.message.reply_text("Uso: /novo [tema do video]")
        return

    user_id = update.effective_user.id
    session = _s(user_id)
    session["topic"] = topic
    session["step"] = "Pesquisando..."

    msg = await update.message.reply_text(f"Pesquisando: {topic}...")

    try:
        def timeout_handler(signum, frame):
            raise TimeoutError("timed out")

        old = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(_CMD_TIMEOUT)
        calendario = CalendarioEditorial()
        cal_result = calendario.execute(topic)
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

        session["research"] = cal_result["research"]
        session["style_guide"] = cal_result["style_guide"]
        session["step"] = "tema_ok"

        await msg.edit_text(
            f"[OK] Tema pesquisado\n\n"
            f"Topico: {topic}\n\n"
            f"Research:\n{_t(cal_result['research'], 400)}\n\n"
            f"Style Guide:\n{_t(cal_result['style_guide'], 400)}\n\n"
            f"Use /validar_tema para rever ou /roteiro para gerar roteiro.",
        )
    except TimeoutError:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        logger.error("Timeout cmd_novo")
        await msg.edit_text(f"[TEMPO EXCEDIDO]超过了{_CMD_TIMEOUT}s。Tente novamente.")
    except Exception as e:
        logger.error(f"Erro cmd_novo: {e}")
        await msg.edit_text(f"[ERRO] {str(e)}")


async def cmd_validar_tema(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("research"):
        await update.message.reply_text("Nenhum tema. Use /novo [tema] primeiro.")
        return

    topic = session["topic"]
    await update.message.reply_text(f"Research - {topic}:\n\n{session['research']}")
    await update.message.reply_text(f"Style Guide - {topic}:\n\n{session['style_guide']}")


async def cmd_validar_roteiro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("research"):
        await update.message.reply_text("Pesquise o tema primeiro com /novo [tema].")
        return

    if not session.get("script_data"):
        await update.message.reply_text("Roteiro ainda nao gerado. Use /roteiro.")
        return

    sd = session["script_data"]
    await update.message.reply_text(f"INTRO:\n\n{_t(sd.get('intro', ''), 500)}")
    await update.message.reply_text(f"MAIN:\n\n{_t(sd.get('main', ''), 800)}")
    await update.message.reply_text(f"OUTRO:\n\n{_t(sd.get('outro', ''), 500)}")

    cena_prompts = sd.get("cena_prompts", [])
    if cena_prompts:
        cenas_text = "\n".join([f"- {c['scene']}: {_t(c['prompt'], 80)}" for c in cena_prompts])
        await update.message.reply_text(f"Cenas ({len(cena_prompts)}):\n{cenas_text}")


async def cmd_gerar_roteiro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("research"):
        await update.message.reply_text("Use /novo [tema] primeiro.")
        return

    msg = await update.message.reply_text("Gerando roteiro...")

    def timeout_handler(signum, frame):
        raise TimeoutError("timed out")

    try:
        old = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(_CMD_TIMEOUT)

        roteirista = RoteiristaCirleneNiza()
        sd = roteirista.execute(
            topic=session["topic"],
            research=session["research"],
            style_guide=session["style_guide"],
        )

        signal.signal(signal.SIGALRM, timeout_handler)
        revisor = RevisorEspecialista()
        rev = revisor.execute(sd["full_script"])

        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

        session["script_data"] = sd
        session["step"] = "roteiro_ok"

        await msg.edit_text(
            f"[OK] Roteiro gerado e revisado\n"
            f"Cenas: {len(sd.get('cena_prompts', []))}\n"
            f"Revisao: {rev.get('status', '-')}",
        )

        await update.message.reply_text(f"INTRO:\n\n{_t(sd.get('intro', ''), 500)}")
        await update.message.reply_text(f"MAIN:\n\n{_t(sd.get('main', ''), 800)}")
        await update.message.reply_text(f"OUTRO:\n\n{_t(sd.get('outro', ''), 500)}")
        await update.message.reply_text(
            "Correcoes? Use /corrigir [instrucao]  ex: /corrigir intro muito longa",
        )
    except TimeoutError:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        logger.error("Timeout cmd_gerar_roteiro")
        await msg.edit_text(f"[TEMPO EXCEDIDO]超过了{_CMD_TIMEOUT}s。Tente novamente.")
    except Exception as e:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        logger.error(f"Erro gerar roteiro: {e}")
        await msg.edit_text(f"[ERRO] {str(e)}")


async def cmd_corrigir(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("script_data"):
        await update.message.reply_text("Nenhum roteiro para corrigir.")
        return

    correction = " ".join(ctx.args) if ctx.args else None
    if not correction:
        await update.message.reply_text("Uso: /corrigir [instrucao]  ex: /corrigir intro muito longa")
        return

    msg = await update.message.reply_text(f"Corrigindo: {correction}...")

    try:
        roteirista = RoteiristaCirleneNiza()

        step = "all"
        if "intro" in correction.lower():
            step = "intro"
        elif "main" in correction.lower() or "cena" in correction.lower():
            step = "main"
        elif "outro" in correction.lower():
            step = "outro"

        corrected = roteirista.apply_correction(
            current=session["script_data"],
            correction=correction,
            step=step,
        )

        session["script_data"] = corrected

        await msg.edit_text(f"[OK] Correcao aplicada na parte: {step}")
        await update.message.reply_text(f"INTRO (corrigido):\n\n{_t(corrected.get('intro', ''), 500)}")
        await update.message.reply_text(f"MAIN (corrigido):\n\n{_t(corrected.get('main', ''), 800)}")
        await update.message.reply_text(f"OUTRO (corrigido):\n\n{_t(corrected.get('outro', ''), 500)}")

    except Exception as e:
        logger.error(f"Erro cmd_corrigir: {e}")
        await msg.edit_text(f"[ERRO] {str(e)}")


async def cmd_gerar_thumbnail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("script_data"):
        await update.message.reply_text("Gere o roteiro primeiro com /roteiro.")
        return

    msg = await update.message.reply_text("Gerando thumbnail...")

    try:
        director = DiretorDeArte()
        topic = session["topic"]
        thumbnail_prompts = session["script_data"].get("thumbnail_prompts", [])
        thumb_result = director.execute(
            task="thumbnail",
            context={
                "topic": topic,
                "thumbnail_prompt": thumbnail_prompts[0] if thumbnail_prompts else None,
            },
        )
        session["thumbnail_url"] = thumb_result.get("thumbnail_url")
        session["step"] = "thumbnail_ok"

        await msg.edit_text("[OK] Thumbnail gerado!")
        await update.message.reply_photo(thumb_result.get("thumbnail_url"))
        await update.message.reply_text(
            "Use /thumbnail_novo [ajuste] para gerar outro, ou /produzir para iniciar.",
        )
    except Exception as e:
        logger.error(f"Erro gerar thumbnail: {e}")
        await msg.edit_text(f"[ERRO] {str(e)}")


async def cmd_thumbnail_novo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    correction = " ".join(ctx.args) if ctx.args else ""
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("script_data"):
        await update.message.reply_text("Gere o roteiro primeiro.")
        return

    prompt_override = session["script_data"].get("thumbnail_prompts", [{}])
    prompt_override = prompt_override[0] if prompt_override else ""
    if correction:
        prompt_override = f"{prompt_override} {correction}"

    msg = await update.message.reply_text("Gerando thumbnail...")

    try:
        director = DiretorDeArte()
        thumb_result = director.execute(
            task="thumbnail",
            context={
                "topic": session["topic"],
                "thumbnail_prompt": prompt_override if prompt_override else None,
            },
        )
        session["thumbnail_url"] = thumb_result.get("thumbnail_url")

        await msg.edit_text("[OK] Novo thumbnail!")
        await update.message.reply_photo(thumb_result.get("thumbnail_url"))
    except Exception as e:
        await msg.edit_text(f"[ERRO] {str(e)}")


async def cmd_produzir(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    if not session.get("script_data"):
        await update.message.reply_text("Gere roteiro e thumbnail primeiro.")
        return

    msg = await update.message.reply_text("Iniciando producao (pode levar 15-20 min)...")

    asyncio.create_task(
        run_production_background(user_id, msg.message_id, update.effective_chat.id)
    )


async def run_production_background(chat_id: int, reply_to: int, user_id: int):
    from telegram import Bot
    bot = Bot(token=settings.telegram_bot_token)
    session = _sessions.get(user_id, {})

    try:
        await bot.edit_message_text(
            "Producao em andamento... aguarde 15-20 min.",
            chat_id=chat_id,
            message_id=reply_to,
        )

        from cirleneniza.crew.video_crew_produzir import ProduzirCrew
        crew = ProduzirCrew()
        result = crew.run(session)

        await bot.edit_message_text(
            f"[OK] Producao concluida\n\n"
            f"Video: {result.get('video_url', '-')}\n"
            f"Thumbnail: {session.get('thumbnail_url', '-')}\n"
            f"ID: {result.get('production_id', '-')}",
            chat_id=chat_id,
            message_id=reply_to,
        )
    except Exception as e:
        logger.error(f"Erro producao: {e}")
        await bot.edit_message_text(
            f"[ERRO] Producao: {str(e)}",
            chat_id=chat_id,
            message_id=reply_to,
        )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = _s(user_id)

    step = session.get("step", "nenhum")
    topic = session.get("topic", "-")

    await update.message.reply_text(
        f"Status atual:\n\n"
        f"Tema: {topic}\n"
        f"Etapa: {step}\n"
        f"Thumbnail: {'OK' if session.get('thumbnail_url') else 'FALTA'}\n"
        f"Roteiro: {'OK' if session.get('script_data') else 'FALTA'}",
    )


def run_bot():
    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))
    app.add_handler(CommandHandler("novo", cmd_novo))
    app.add_handler(CommandHandler("validar_tema", cmd_validar_tema))
    app.add_handler(CommandHandler("roteiro", cmd_gerar_roteiro))
    app.add_handler(CommandHandler("validar_roteiro", cmd_validar_roteiro))
    app.add_handler(CommandHandler("corrigir", cmd_corrigir))
    app.add_handler(CommandHandler("gerar_thumbnail", cmd_gerar_thumbnail))
    app.add_handler(CommandHandler("thumbnail_novo", cmd_thumbnail_novo))
    app.add_handler(CommandHandler("produzir", cmd_produzir))
    app.add_handler(CommandHandler("status", cmd_status))

    logger.info("Telegram bot iniciado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()