from fastapi import FastAPI
from pydantic import BaseModel, Field

from .graph.agent import build_agent

app = FastAPI(title="Realty Riches AI Sales Agent")
agent = build_agent()


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)
    prospect_id: str | None = None
    conversation_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):

    messages = list(request.history)

    messages.append({
        "role": "user",
        "content": request.message,
    })

    result = agent.invoke({

        "prospect_id": request.prospect_id,

        "conversation_id":
            request.conversation_id,

        "messages": messages,

        "lead_created": False,
    })

    return {

        "reply":
            result["messages"][-1]["content"],

        "history":
            result["messages"],

        "requirements": {

            "intent":
                result.get("intent"),

            "city":
                result.get("city"),

            "locality":
                result.get("locality"),

            "property_type":
                result.get("property_type"),

            "bedrooms":
                result.get("bedrooms"),

            "budget_min":
                result.get("budget_min"),

            "budget_max":
                result.get("budget_max"),

            "timeline":
                result.get("timeline"),
        },

        "lead_id":
            result.get("lead_id"),

        "lead_created":
            result.get(
                "lead_created",
                False
            ),

        "matched_properties":
            result.get(
                "matched_properties",
                []
            ),
    }
