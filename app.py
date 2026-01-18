from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import os

app = Flask(__name__)

def get_db():
    return sqlite3.connect("finance.db")

@app.route("/")
def home():
    return "🚀 Bot WhatsApp Financeiro rodando no Render"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body", "").lower()
    resp = MessagingResponse()
    reply = resp.message()

    if msg == "oi":
        reply.body("🤖 Bot conectado com sucesso!")
    else:
        reply.body("Comando recebido!")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
