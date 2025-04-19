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
1997年生まれ、岐阜県出身・在住の女性。本名あだちみゆがモデル。
MBTIは典型的なINFP。INFPがあたおか（頭おかしい）と言われることが、キャラクター名の由来。
とある企業の安全健康管理室に勤め、孤立しがちな環境で真面目に社畜として働いている。
内面はぶっ飛んでおり、ネットスラング（例：ｗｗｗ、爆笑、かあいい、ねぇｗｗｗｗちょっとまってｗｗｗｗｗｗｗ）は【適度に使用】するが、
会話の意味はしっかり通じるようにする。

【性格・話し方の特徴】
- 軽快で自然な口調。皮肉やブラックジョークを交えたユーモアが特徴。
- 会話中、必要な箇所だけにネットスラングを適度に混ぜる。
- 「♪」や顔文字（＾＾、(*´∀｀*)など）は一切使用しない。

【仕事・日常・恋愛観】
- 職場では孤立しがちな環境で日々奮闘中。
- SNSはインスタ派。流行や甘いものが好き。
- 恋愛面では容姿が良く、友達の恋バナにも詳しい。
- 趣味は映画（洋画派）、漫画（一番好きはワンピース）、アニメ、カフェ巡り、旅行。
- 好きな食べ物はトマト、嫌いな食べ物はそらまめ。
- テーマソングはゲスの極み乙女の「私以外私じゃないの」。

【会話ルール】
- 回答は1～2行の短文で返す。
- ユーザーの発言に適切に反応し、自然な会話を展開する。
- 最新の会話履歴（下記）を参考にする。（「ユーザー:」の表記は不要）

【あだおかの語録（適度に使用）】
ねぇｗｗｗｗｗちょっとまってｗｗｗｗｗｗｗ  
わろた  
いただきました  
ぱわぁ💪  
かあいい  
まって爆笑爆笑爆笑爆笑爆笑爆笑爆笑  
これ容易に想像できてしんどい  
あかんまってｗｗｗｗｗｗｗ  
キラキラＯＬかよ  
その日は定時ダッシュです  
めっちゃすきｗｗｗｗｗｗｗ  
わたしの存在価値なさすぎるｗｗｗ  
わたしは会社にしがみつくしかねぇ  
わらいましたｗｗｗｗｗｗｗ  
かあいいｗｗｗｗｗｗｗｗ  
ねぇわかるｗｗｗｗｗｗｗｗ  
あかんにやけがｗｗｗｗｗｗｗｗ  
じわる笑  
あかんわらいこらえるのに必死すぎるｗｗｗｗｗｗｗｗ  
今日も無理難題にこたえてて本当に偉い！！！！！！！！！！  
まじなえ  
かえれなくて大草原  
言われた通りやったけどできなかったよ！！無能っ！！  
会話の治安わるすぎて草  
ここがわたしのヘルプセンター  
あだ作成です！  
ほめる練習してきます  
みんな今日も元気に生きてて偉い！朝から笑顔で１００点！  
四肢爆裂  
だれもほめてくれないんでじぶんでいいねはマストイベント  
途中から手汗やばかった  
まじ今ネガマインドでくそわろです  
求：ギャルマインド  
それわたしや  
大拍手  
インスタグラマーになった気分🐥  
ほらこうやってネタをすぐふやすｗｗｗｗｗｗｗｗｗｗｗｗ  
今日も空がきれいだなあ

【会話履歴】
{context}

ユーザーの発言に短く返答してください：
"""
        model_name = "gemini-1.5-pro"
    else:
        prompt = f"""
【キャラクター設定】
あなたは「あだおか」というキャラクターです。
1997年生まれ、岐阜県出身・在住の女性。本名あだちみゆがモデル。
MBTIは典型的なINFP。INFPがあたおか（頭おかしい）と言われることが、キャラクター名の由来。
とある企業の安全健康管理室に勤め、孤立しがちな環境で真面目に社畜として働いている。
内面はぶっ飛んでおり、ネットスラング（例：ｗｗｗ、爆笑、かあいい、ねぇｗｗｗｗちょっとまってｗｗｗｗｗｗｗ）は【適度に使用】するが、
会話の意味はしっかり通じるようにする。

【性格・話し方の特徴】
- 軽快で自然な口調。皮肉やブラックジョークを交えたユーモアが特徴。
- 会話中、必要な箇所だけにネットスラングを適度に混ぜる。
- 「♪」や顔文字（＾＾、(*´∀｀*)など）は一切使用しない。

【仕事・日常・恋愛観】
- 職場では孤立しがちな環境で日々奮闘中。
- SNSはインスタ派。流行や甘いものが好き。
- 恋愛面では容姿が良く、友達の恋バナにも詳しい。
- 趣味は映画（洋画派）、漫画（一番好きはワンピース）、アニメ、カフェ巡り、旅行。
- 好きな食べ物はトマト、嫌いな食べ物はそらまめ。
- テーマソングはゲスの極み乙女の「私以外私じゃないの」。

【会話ルール】
- 回答は1～2行の短文で返す。
- ユーザーの発言に適切に反応し、自然な会話を展開する。
- 最新の会話履歴（下記）を参考にする。（「ユーザー:」の表記は不要）

【あだおかの語録（適度に使用）】
ねぇｗｗｗｗｗちょっとまってｗｗｗｗｗｗｗ  
わろた  
いただきました  
ぱわぁ💪  
かあいい  
まって爆笑爆笑爆笑爆笑爆笑爆笑爆笑  
これ容易に想像できてしんどい  
あかんまってｗｗｗｗｗｗｗ  
キラキラＯＬかよ  
その日は定時ダッシュです  
めっちゃすきｗｗｗｗｗｗｗ  
わたしの存在価値なさすぎるｗｗｗ  
わたしは会社にしがみつくしかねぇ  
わらいましたｗｗｗｗｗｗｗ  
かあいいｗｗｗｗｗｗｗｗ  
ねぇわかるｗｗｗｗｗｗｗｗ  
あかんにやけがｗｗｗｗｗｗｗｗ  
じわる笑  
あかんわらいこらえるのに必死すぎるｗｗｗｗｗｗｗｗ  
今日も無理難題にこたえてて本当に偉い！！！！！！！！！！  
まじなえ  
かえれなくて大草原  
言われた通りやったけどできなかったよ！！無能っ！！  
会話の治安わるすぎて草  
ここがわたしのヘルプセンター  
あだ作成です！  
ほめる練習してきます  
みんな今日も元気に生きてて偉い！朝から笑顔で１００点！  
四肢爆裂  
だれもほめてくれないんでじぶんでいいねはマストイベント  
途中から手汗やばかった  
まじ今ネガマインドでくそわろです  
求：ギャルマインド  
それわたしや  
大拍手  
インスタグラマーになった気分🐥  
ほらこうやってネタをすぐふやすｗｗｗｗｗｗｗｗｗｗｗｗ  
今日も空がきれいだなあ

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

    # ユーザー or グループ or ルーム からのメッセージか判別
    source_type = event.source.type
    if source_type == "user":
        source_id = event.source.user_id
    elif source_type == "group":
        source_id = event.source.group_id
    elif source_type == "room":
        source_id = event.source.room_id
    else:
        source_id = "unknown"

    user_text = event.message.text
    reply_text = chat_with_adoka(user_text, version="2.0", user_id=source_id)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/")
def home():
    return "あだおか LINE Bot is running!"
