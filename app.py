import os
import google.generativeai as genai
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# ———— Gemini API の設定 ————
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

# ———— LINE Bot の設定 ————
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET       = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api              = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler           = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーごとの会話履歴をメモリ内に保持（簡易版）
chat_histories = {}

def chat_with_adoka(user_input: str, version: str, user_id: str) -> str:
    """あだおかAIに問い合わせて返答を得る"""
    # 過去履歴を取得（なければ空リスト）
    history = chat_histories.get(user_id, [])
    history.append(f"ユーザー: {user_input}")
    # 直近2ターン分をコンテキストとして使う
    context = "\n".join(history[-2:])

    if version == "1.5":
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。
…（省略）…

【会話履歴】
{context}

ユーザーの発言に短く返答してください：
"""
        model_name = "gemini-1.5-pro"
    else:
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。
…（省略）…

【会話履歴】
{context}

ユーザーの発言に短く返答してください：
"""
        model_name = "gemini-2.0-flash"

    try:
        model    = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        bot_reply = response.text.strip()
    except Exception as e:
        bot_reply = f"エラーが発生しました: {e}"

    # 履歴にボットの返答も追加
    history.append(bot_reply)
    chat_histories[user_id] = history
    return bot_reply

@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    """LINE からの Webhook を受け取るエンドポイント"""
    signature = request.headers.get("X-Line-Signature")
    body      = request.get_data(as_text=True)
    try:
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """メッセージイベントを受け取り、あだおかAIの返答を返信"""
    user_id   = event.source.user_id
    user_text = event.message.text
    # ここでは常に最新版（2.0）で動かす例
    reply_text = chat_with_adoka(user_text, version="2.0", user_id=user_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/")
def home():
    return "あだおか LINE Bot is running!"
