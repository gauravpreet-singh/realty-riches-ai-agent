import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()
twilio_number = os.environ["TWILIO_PHONE_NUMBER"]

client = Client(
    os.environ["TWILIO_API_KEY"],
    os.environ["TWILIO_API_SECRET"],
    os.environ["TWILIO_ACCOUNT_SID"],
)

call = client.calls.create(
    twiml="""
    <Response>
        <Say>
            Hello. This is a test call from your Realty AI Agent.
        </Say>
    </Response>
    """,
    to="+919872762760",
    from_=twilio_number,
)

print("Call created:", call.sid)