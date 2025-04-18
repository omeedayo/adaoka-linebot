from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def root():
    return "Hello from API root!"

@app.route("/line_webhook", methods=["GET", "POST"])
def webhook():
    return f"Webhook received via {request.method}", 200
