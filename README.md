# Realty Riches AI Sales Agent — Phase 2

Python + LangGraph + LangChain + Supabase.

## What this version does

1. Accepts a customer message.
2. Extracts structured buying requirements.
3. Searches the real `public.properties` table.
4. Treats `price = 0` as unknown.
5. Generates a response using only returned property data.

The architecture deliberately separates:
- deterministic property retrieval
- LLM conversation/extraction
- future semantic matching
- future voice/telephony

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
```

Put the server-only Supabase secret key and OpenAI API key in `.env`.

Supabase secret keys must remain backend-only.

## Run

```bash
uvicorn app.main:app --reload
```

Then POST:

```json
{
  "message": "I want a 3 BHK around 1 crore in Kharar",
  "history": []
}
```

## Next production steps

- Persist conversations/messages in Supabase.
- Add prospect + lead tools.
- Preserve requirements across turns instead of extracting from only the latest message.
- Add deterministic property scoring.
- Add pgvector semantic matching for soft preferences.
- Add call eligibility/compliance gate.
- Add voice adapter and telephony provider.
