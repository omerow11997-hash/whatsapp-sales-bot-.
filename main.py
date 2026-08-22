import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

k = os.environ.get("GEMINI_API_KEY")
i = os.environ.get("GREEN_API_INSTANCE")
t = os.environ.get("GREEN_API_TOKEN")

@app.route('/', methods=['GET'])
def h():
    return "Active", 200

@app.route('/webhook', methods=['POST'])
def w():
    d = request.get_json()
    print("Received webhook data:", d)
    try:
        if d.get('typeWebhook') != 'incomingMessageReceived':
            return jsonify({'s': 'i'}), 200
            
        m = d.get('messageData', {})
        s = d.get('senderData', {})
        c = s.get('chatId')
        
        if s.get('self') or not c:
            return jsonify({'s': 'i'}), 200
            
        u = m.get('textMessageData', {}).get('textMessage') or m.get('extendedTextMessageData', {}).get('text', '')
        print(f"User message: {u}")
        
        if not u:
            return jsonify({'s': 'n'}), 200
            
        models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-flash"]
        re = ""
        
        for mod in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={k}"
            p = {"contents": [{"parts": [{"text": u}]}]}
            res = requests.post(url, json=p).json()
            try:
                re = res['candidates'][0]['content']['parts'][0]['text']
                if re:
                    break
            except Exception as ex:
                print(f"Model {mod} failed: {ex}")
                continue
                
        print(f"Gemini response: {re}")
        
        if re:
            green_url = f"https://api.green-api.com/waInstance{i}/sendMessage/{t}"
            payload = {"chatId": c, "message": re}
            send_res = requests.post(green_url, json=payload)
            print("Green-API response:", send_res.status_code, send_res.text)
            
        return jsonify({'s': 'o'}), 200
        
    except Exception as e:
        print("Main Exception:", e)
        return jsonify({'s': 'e'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
