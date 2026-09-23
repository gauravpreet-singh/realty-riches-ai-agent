import os

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse


class TwilioAdapter:
    def __init__(self):
        sid=os.environ["TWILIO_ACCOUNT_SID"]
        key=os.environ.get("TWILIO_API_KEY")
        secret=os.environ.get("TWILIO_API_SECRET")
        self.from_number=os.environ["TWILIO_PHONE_NUMBER"]
        self.client=Client(key,secret,sid) if key and secret else Client(
            sid,os.environ["TWILIO_AUTH_TOKEN"])

    def start_call(self,to,callback_url):
        call=self.client.calls.create(url=callback_url,to=to,from_=self.from_number)
        return call.sid

    @staticmethod
    def gather(prompt,action_url):
        r=VoiceResponse()
        g=r.gather(input="speech",action=action_url,method="POST",
                   speech_timeout="auto",timeout=5)
        g.say(prompt)
        return str(r)
