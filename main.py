from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
import os
import tempfile

app = Flask(__name__)

# --- الإعدادات والمفاتيح ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GREEN_API_INSTANCE = os.environ.get("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
موظف مبيعات وتواصل مع العملاء محترف ومدرب بشكل ممتاز
:مهامك وأسلوبك
1. الترحيب بالعميل بأسلوب راقٍ ومباشر دون إطالة مملة.
2. دقة متناهية على سؤال العميل بناءً على المعطيات المتاحة.
3. أسلوب جذاب، وتقديم حلول واقتراحات تناسب احتياج العميل.
4. إجابة العميل دائماً هي مساعدة العميل، وإقناعه بأسلوب سلس، وتوجيهه للخطوة التالية.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash-latest',
    system_instruction=SYSTEM_INSTRUCTION
)

sessions = {}

@app.route('/', methods=['GET'])
def home():
    return "Sales Bot is active!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    try:
        type_webhook = data.get('typeWebhook')
        if type_webhook != 'incomingMessageReceived':
            return jsonify({'status': 'ignored'}), 200
            
        message_data = data.get('messageData', {})
        sender_data = data.get('senderData', {})
        
        chat_id = sender_data.get('chatId')
        type_message = message_data.get('typeMessage')
        
        # تجاهل الرسائل الصادرة من البوت نفسه
        if sender_data.get('self', False):
            return jsonify({'status': 'ignored_self'}), 200

        user_text = ""
        
        if type_message == 'textMessage':
            user_text = message_data.get('textMessageData', {}).get('textMessage', '')
        elif type_message == 'extendedTextMessage':
            user_text = message_data.get('extendedTextMessageData', {}).get('text', '')

        if not user_text or not chat_id:
            return jsonify({'status': 'no_text'}), 200

        # إدارة الجلسة والمحادثة
        if chat_id not in sessions:
            sessions[chat_id] = model.start_chat(history=[])
            
        chat = sessions[chat_id]
        response = chat.send_message(user_text)
        reply_text = response.text

        # إرسال الرد عبر Green API
        url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
        payload = {
            "chatId": chat_id,
            "message": reply_text
        }
        headers = {'Content-Type': 'application/json'}
        requests.post(url, json=payload, headers=headers)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
