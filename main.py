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
    try:
        if d.get('typeWebhook') != 'incomingMessageReceived':
            return jsonify({'s': 'i'}), 200
            
        m = d.get('messageData', {})
        s = d.get('senderData', {})
        c = s.get('chatId')
        
        if s.get('self') or not c:
            return jsonify({'s': 'i'}), 200
            
        u = m.get('textMessageData', {}).get('textMessage') or m.get('extendedTextMessageData', {}).get('text', '')
        if not u:
            return jsonify({'s': 'n'}), 200
            
        # استخدام صيغة أبسط وأحدث للطلب
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={k}"
        payload = {
            "contents": [{
                "parts": [{"text": u}]
            }]
        }
        
        res = requests.post(url, json=payload)
        res_json = res.json()
        print("Full Gemini API Response:", res_json)
        
        re = ""
        try:
            re = res_json['candidates'][0]['content']['parts'][0]['text']
        except Exception as ex:
            print(f"Extraction error: {ex}")
            
        if re:
            green_url = f"https://api.green-api.com/waInstance{i}/sendMessage/{t}"
            requests.post(green_url, json={"chatId": c, "message": re})
            
        return jsonify({'s': 'o'}), 200
        
    except Exception as e:
        print("Main Exception:", e)
        return jsonify({'s': 'e'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
