from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.values.get("Body", "").lower()
    resp = MessagingResponse()
    reply = resp.message()

    if "oi" in msg:
        reply.body("Olá! Bot online no Render 🚀")
    else:
        reply.body("Comando não reconhecido")

    return str(resp)

if __name__ == "__main__":
    app.run()
