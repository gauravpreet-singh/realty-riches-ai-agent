from fastapi import APIRouter, Form, Request, Response
from twilio.twiml.voice_response import VoiceResponse

from app.telephony_service import TelephonyService

router = APIRouter(prefix="/telephony/twilio", tags=["telephony"])
service = TelephonyService()


def _gather_xml(prompt: str, action: str) -> str:
    response = VoiceResponse()
    gather = response.gather(
        input="speech",
        action=action,
        method="POST",
        speech_timeout="auto",
        timeout=5,
    )
    gather.say(prompt)
    return str(response)


@router.post("/voice")
async def incoming_call(
    request: Request,
    From: str = Form(...),
    CallSid: str = Form(...),
):
    # Twilio calls this endpoint when the call is answered.
    return Response(
        content=_gather_xml(
            "Hi, this is Realty Riches. How can I help you today?",
            "/telephony/twilio/gather",
        ),
        media_type="application/xml",
    )


@router.post("/gather")
async def gather_speech(
    request: Request,
    From: str = Form(...),
    CallSid: str = Form(...),
    SpeechResult: str | None = Form(None),
):
    if not SpeechResult:
        return Response(
            content=_gather_xml(
                "Sorry, I didn't catch that. Could you please say that again?",
                "/telephony/twilio/gather",
            ),
            media_type="application/xml",
        )

    result = service.process_transcript(CallSid, From, SpeechResult)
    response = VoiceResponse()
    response.say(result.get("response") or "Thank you. I have noted that.")
    gather = response.gather(
        input="speech",
        action="/telephony/twilio/gather",
        method="POST",
        speech_timeout="auto",
        timeout=5,
    )
    gather.say("Is there anything else I can help you with?")
    return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
):
    if CallStatus in {"completed", "busy", "failed", "no-answer", "canceled"}:
        service.end_call(CallSid, CallStatus)
    return {"ok": True}
