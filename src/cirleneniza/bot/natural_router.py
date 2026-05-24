"""
NaturalLanguageRouter — converte mensagem livre em chamada de handler.
Usado pelo MessageHandler do telegram_bot.py para linguagem natural.
"""
import json
from loguru import logger
from cirleneniza.tools.minimax import MiniMaxClient

_SYSTEM = """Você é o roteador do bot de produção de vídeos do Canal Cirlene Niza.

Seu papel: classificar a mensagem do usuário e extrair parâmetros.

Retorne APENAS JSON válido com este schema:
{
  "intent": "<intent>",
  "params": { ... },
  "reply": "<resposta curta para o usuário em pt-BR, max 2 frases>"
}

Intents disponíveis:
- "novo_tema"      → usuário quer iniciar vídeo. params: {"topic": "string"}
- "gerar_roteiro"  → usuário quer gerar/criar roteiro
- "ver_roteiro"    → usuário quer ver o roteiro gerado
- "corrigir"       → usuário quer corrigir algo. params: {"instrucao": "string"}
- "gerar_thumbnail"→ usuário quer thumbnail
- "thumbnail_novo" → usuário quer thumbnail diferente. params: {"ajuste": "string"}
- "produzir"       → usuário quer produzir/montar o vídeo
- "status"         → usuário quer ver status atual
- "conversa"       → qualquer outra coisa — responder conversacionalmente sobre o canal

Para "conversa", o campo "reply" deve ser uma resposta útil sobre produção de conteúdo de nutrição.

Exemplos:
- "quero fazer um vídeo sobre vitamina D" → intent: "novo_tema", params: {"topic": "vitamina D"}
- "gera o roteiro agora" → intent: "gerar_roteiro"
- "a intro ficou muito longa" → intent: "corrigir", params: {"instrucao": "intro muito longa"}
- "qual o próximo passo?" → intent: "conversa" + reply explicando o fluxo
- "produz" → intent: "produzir"
"""


class NaturalLanguageRouter:
    def __init__(self):
        self.llm = MiniMaxClient()

    def route(self, message: str, session: dict) -> dict:
        """
        Returns dict with:
          - intent: str
          - params: dict
          - reply: str
        """
        session_ctx = (
            f"Contexto atual da sessão:\n"
            f"- Tema: {session.get('topic') or 'nenhum'}\n"
            f"- Etapa: {session.get('step') or 'início'}\n"
            f"- Roteiro: {'gerado' if session.get('script_data') else 'não gerado'}\n"
            f"- Thumbnail: {'gerado' if session.get('thumbnail_url') else 'não gerado'}\n"
        )

        prompt = f"{session_ctx}\nMensagem do usuário: {message}"

        try:
            raw = self.llm.generate(
                prompt=prompt,
                system=_SYSTEM,
                temperature=0.3,
                max_tokens=1024,
            )
            # strip markdown fences if present
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"NLRouter parse error: {e} | raw: {raw!r}")
            return {
                "intent": "conversa",
                "params": {},
                "reply": "Desculpe, não entendi. Pode reformular? Ou use /ajuda para ver os comandos.",
            }
