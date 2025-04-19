import os
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# 環境変数から読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET      = os.getenv("LINE_CHANNEL_SECRET")

# LINE SDK の初期化
line_bot_api    = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(LINE_CHANNEL_SECRET)  # ← ここだけ変更

@app.route("/")
def home():
    return "Hello from minimal LINE Bot!"

@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    signature = request.headers.get("X-Line-Signature")
    body      = request.get_data(as_text=True)
    try:
        # handler.handle → webhook_handler.handle に
        webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

# decorator も webhook_handler に合わせて変更
@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text  = event.message.text
    reply = f"Got your message: {text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
