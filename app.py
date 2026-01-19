from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DATA_FILE = 'finance.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    from_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()
    
    data = load_data()
    user_data = data.get(from_number, {'balance': 0.0, 'history': []})

    if incoming_msg.startswith('add '):
        try:
            _, value, *desc = incoming_msg.split()
            value = float(value)
            description = ' '.join(desc) if desc else 'Despesa'
            user_data['balance'] -= value
            user_data['history'].append(f"-{value} {description}")
            msg.body(f"Despesa registrada: {value} ({description})\nSaldo atual: {user_data['balance']}")
        except:
            msg.body("Formato inválido! Use: add [valor] [descrição]")

    elif incoming_msg.startswith('income '):
        try:
            _, value, *desc = incoming_msg.split()
            value = float(value)
            description = ' '.join(desc) if desc else 'Receita'
            user_data['balance'] += value
            user_data['history'].append(f"+{value} {description}")
            msg.body(f"Receita registrada: {value} ({description})\nSaldo atual: {user_data['balance']}")
        except:
            msg.body("Formato inválido! Use: income [valor] [descrição]")

    elif incoming_msg == 'saldo':
        msg.body(f"Seu saldo atual é: {user_data['balance']}")

    elif incoming_msg == 'extrato':
        history = '\n'.join(user_data['history']) or 'Nenhuma transação'
        msg.body(f"Extrato:\n{history}\nSaldo: {user_data['balance']}")

    else:
        msg.body("Comandos disponíveis:\n- add [valor] [descrição]\n- income [valor] [descrição]\n- saldo\n- extrato")

    data[from_number] = user_data
    save_data(data)

    return str(resp)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
