import os
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数から LINE 用のキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LINE SDK の初期化（グローバルにOK）
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# google-generativeai は遅延インポート（リクエスト時に読み込む）
def get_genai_model(model_name):
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY, transport="rest")
    return genai.GenerativeModel(model_name)

@app.route("/")
def home():
    return "Hello from LINE Bot!"

@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    # 遅延で model を取得
    model = get_genai_model("gemini-1.5-pro")
    response = model.generate_content(user_input)
    bot_reply = response.text.strip()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=bot_reply)
    )
