import os
from flask import Flask,request,jsonify
import requests
app=Flask(__name__)
k=os.environ.get("GEMINI_API_KEY")
i=os.environ.get("GREEN_API_INSTANCE")
t=os.environ.get("GREEN_API_TOKEN")
@app.route('/',methods=['GET'])
def h():return "Active",200
@app.route('/webhook',methods=['POST'])
def w():
 d=request.get_json()
 try:
  if d.get('typeWebhook')!='incomingMessageReceived':return jsonify({'s':'i'}),200
  m=d.get('messageData',{})
  s=d.get('senderData',{})
  c=s.get('chatId')
  if s.get('self') or not c:return jsonify({'s':'i'}),200
  u=m.get('textMessageData',{}).get('textMessage') or m.get('extendedTextMessageData',{}).get('text','')
  if not u:return jsonify({'s':'n'}),200
  models=["gemini-1.5-flash","gemini-2.0-flash","gemini-flash"]
  re=""
  for mod in models:
   url=f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={k}"
   p={"contents":[{"parts":[{"text":f"أنت موظف مبيعات محترف. أجب على: {u}"}]}]}
   res=requests.post(url,json=p).json()
   try:
    re=res['candidates'][0]['content']['parts'][0]['text']
    if re:break
   except:continue
  if not re:re="عذراً يا مهندس، لم أتمكن من جلب الرد حالياً."
  requests.post(f"https://api.green-api.com/waInstance{i}/sendMessage/{t}",json={"chatId":c,"message":re})
  return jsonify({'s':'o'}),200
 except Exception as e:
  print(e)
  return jsonify({'s':'e'}),500
if __name__=='__main__':app.run(host='0.0.0.0',port=5000)
