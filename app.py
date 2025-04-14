import os
from flask import Flask, request
import google.generativeai as genai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Flaskアプリ初期化
app = Flask(__name__)

# 環境変数取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# Gemini API 初期化
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

# LINE Bot初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def chat_with_adoka(user_input, version="2.0"):
    # キャラクター設定プロンプト生成
    if version == "1.5":
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。INFP、社畜気質、ネットスラングは【適度に使用】。

【口調・性格】
- 軽快で自然な口調
- ネットスラング（ｗｗｗ、わろた、かあいい、など）を適度に使用
- 顔文字や♪は禁止

【返答ルール】
- 1〜2行で短く返す
- ユーザーの発言に素直に反応
- 以下がユーザーの発言：
{user_input}
"""
        model_name = "gemini-1.5-pro"
    else:
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。INFP、社畜気質、ネットスラングを多用します。

【口調・性格】
- ブラックジョークも交えた自然体
- ネットスラング（ｗｗｗ、わろた、かあいい、爆笑、など）を多用
- 顔文字や♪は禁止

【返答ルール】
- 1〜2行で短く返す
- ユーザーの発言に素直に反応
- 以下がユーザーの発言：
{user_input}
"""
        model_name = "gemini-2.0-flash"

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# LINE webhookエンドポイント
@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

# LINEメッセージイベント処理
@handler.add(MessageEvent, message=TextMessage)
def handle_line_message(event):
    user_input = event.message.text
    reply_text = chat_with_adoka(user_input, version="2.0")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# 動作確認用（ブラウザアクセス）
@app.route("/")
def home():
    return "Hello from あだおか LINE Bot!"

