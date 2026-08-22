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
أنت موظف مبيعات وتواصل مع العملاء محترف ومدرب بشكل ممتاز. 
مهامك وأسلوبك:
1. الترحيب بالعميل بأسلوب راقٍ ومباشر دون إطالة مللة.
2. الإجابة بدقة متناهية على سؤال العميل بناءً على المعطيات المتاحة.
3. التحدث بلغة عربية بسيطة، واضحة، وجذابة، وتقديم حلول واقتراحات تناسب احتياج العميل.
4. إذا أرسل العميل مقطعاً صوتياً أو صورة أو ملفاً، قم بتحليله وفهمه جيداً ثم أجب على ما ورد فيه كأنك سمعته أو رأيته مباشرة.
5. هدفك الدائم هو مساعدة العميل، إقناعه بأسلوب سلس، وتوجيهه للخطوة التالية.
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
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

        if not chat_id:
            return jsonify({'status': 'no_chat_id'}), 200

        if chat_id not in sessions:
            sessions[chat_id] = model.start_chat(history=[])
        chat = sessions[chat_id]

        bot_reply = ""

        if type_message == 'textMessage':
            user_text = message_data.get('textMessageData', {}).get('textMessage', '')
            if user_text:
                response = chat.send_message(user_text)
                bot_reply = response.text

        elif type_message in ['fileMessage', 'audioMessage', 'voiceMessage']:
            file_data = message_data.get('fileMessageData', {})
            download_url = file_data.get('downloadUrl')
            caption = file_data.get('caption', '')

            if download_url:
                res = requests.get(download_url)
                if res.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(res.content)
                        tmp_file_path = tmp_file.name

                    uploaded_file = genai.upload_file(tmp_file_path)
                    
                    prompt = caption if caption else "استمع/شاهد هذا المرفق وأجب العميل بناءً على محتواه كموظف مبيعات."
                    response = chat.send_message([uploaded_file, prompt])
                    bot_reply = response.text

                    os.remove(tmp_file_path)
                    genai.delete_file(uploaded_file.name)

        if bot_reply:
            send_url = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
            payload = {
                "chatId": chat_id,
                "message": bot_reply
            }
            requests.post(send_url, json=payload)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
