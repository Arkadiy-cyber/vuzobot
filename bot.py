from flask import Flask
app = Flask(name)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    return "OK", 200
