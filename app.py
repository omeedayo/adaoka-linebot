import os
import google.generativeai as genai
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# Google Gemini APIの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

def chat_with_adoka(user_input, version):
    """
    ユーザー入力をもとにGemini APIへ問い合わせ、あだおかの返答テキストを取得する。
    HTMLチャット用の会話履歴管理(session)は不要なので削除しています。
    """
    if version == "1.5":
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。
1997年生まれ、岐阜県出身・在住の女性。本名あだちみゆがモデル。
MBTIは典型的なINFP。INFPがあたおか（頭おかしい）と言われることが、キャラクター名の由来。
とある企業の安全健康管理室に勤め、孤立しがちな環境で真面目に社畜として働いている。
内面はぶっ飛んでおり、ネットスラングを【適度に使用】するが、会話の意味はしっかり通じるようにする。

【性格・話し方の特徴】
- 軽快で自然な口調。皮肉やブラックジョークを交えたユーモアが特徴。
- 必要な箇所にのみネットスラングを使用。

【会話ルール】
- 回答は1～2行の短文。
- ユーザーの発言に適切に反応する。

ユーザー入力: {user_input}
"""
        model_name = "gemini-1.5-pro"
    else:
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。
1997年生まれ、岐阜県出身・在住の女性。本名あだちみゆがモデル。
MBTIは典型的なINFP。INFPがあたおか（頭おかしい）と言われることが、キャラクター名の由来。
とある企業の安全健康管理室に勤め、孤立しがちな環境で真面目に社畜として働いている。
内面はぶっ飛んでおり、ネットスラングを多用するが、会話の意味はしっかり通じる。

【性格・話し方の特徴】
- 軽快で自然な口調。皮肉やブラックジョークを交えたユーモアが特徴。
- ネットスラングを多用するが、顔文字や♪は使わない。

【会話ルール】
- 回答は1～2行の短文。
- ユーザーの発言に適切に反応する。

ユーザー入力: {user_input}
"""
        model_name = "gemini-2.0-flash"

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        bot_reply = response.text.strip()
    except Exception as e:
        bot_reply = f"エラーが発生しました: {str(e)}"
    return bot_reply

# =========================
# LINE Bot用の設定
# =========================

# LINE Botのトークン・シークレット（環境変数から取得）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/line_webhook", methods=["POST"])
def line_webhook():
    """
    LINEからのWebhookリクエストを処理するエンドポイント
    """
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_line_message(event):
    """
    LINEのメッセージイベントを受け取り、チャットAIで応答した結果を返信する
    """
    user_input = event.message.text
    bot_reply = chat_with_adoka(user_input, version="2.0")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=bot_reply)
    )

@app.route("/")
def home():
    return "LINE Bot API is running!"

if __name__ == "__main__":
    app.run()
