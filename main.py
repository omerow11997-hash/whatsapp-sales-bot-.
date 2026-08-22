import os
from flask import Flask,request,jsonify
import requests
app=Flask(__name__)
k=os.environ.get("GEMINI_API_KEY")
i=os.environ.get("GREEN_API_INSTANCE")
t=os.environ.get("GREEN_API_TOKEN")
@app.route('/webhook',methods=['POST'])
def w():
 d=request.get_json()
 if d.get('typeWebhook')!='incomingMessageReceived':return jsonify({'s':'i'}),200
 m=d.get('messageData',{})
 s=d.get('senderData',{})
 c=s.get('chatId')
 if s.get('self'):return jsonify({'s':'i'}),200
 u=m.get('textMessageData',{}).get('textMessage') or m.get('extendedTextMessageData',{}).get('text','')
 if not u or not c:return jsonify({'s':'n'}),200
 url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={k}"
 p={"contents":[{"parts":[{"text":f"أنت موظف مبيعات محترف، أجب باختصار واحترافية على: {u}"}]}]}
 r=requests.post(url,json=p).json()
 try:
  re=r['candidates'][0]['content']['parts'][0]['text']
  requests.post(f"https://api.green-api.com/waInstance{i}/sendMessage/{t}",json={"chatId":c,"message":re})
 except:pass
 return jsonify({'s':'o'}),200
if __name__=='__main__':app.run(host='0.0.0.0',port=5000)
