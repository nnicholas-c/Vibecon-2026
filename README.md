# Drivepast

Price every job from the van that already drives past.

- Live app: https://drivepast.emergent.host
- Research: https://drivepast.emergent.host/research
- Driver phone view: https://drivepast.emergent.host/driver/van-2

## What it is

Small courier fleets quote a flat $45–65 even for jobs their vans already drive past. Drivepast reads the customer's email, finds the van that is already passing nearby, prices just the small detour, books it and replies. The customer pays less, and the courier earns on spare minutes.

## Try it

1. Open the live app and click "Open the demo" twice (once on the landing page, once on the login screen). You get a fresh demo board.
2. Email a pickup request with street addresses to emergentcouriers413@gmail.com, for example: "pick up a box of samples today at 5600 Bay St, Emeryville and drop it at 1100 Gilman St, Berkeley by 4pm".
3. Watch Fleet book it on its own, explain why, and update the driver and customer phones.

## Features

- Email to booking with no clicks
- Incremental route-insertion pricing with a price floor
- AI dispatch assistant that answers from real route data through tool calls
- Auto-send rules plus saved Memory rules
- Driver and customer phone views
- 3D landing story

## Tech

FastAPI, MongoDB, React, Deck.gl, OpenAI (gpt-6-luna) with tool calling, the Gmail API and OSRM routing. Built and deployed on Emergent.

## Run locally

```
cd backend && pip install -r requirements.txt && uvicorn server:app --port 8001
cd frontend && yarn install && yarn start
```

Environment variables (names only; .env files are not committed):

- backend: MONGO_URL, DB_NAME, CORS_ORIGINS, AGENT_API_KEY, AGENT_MODEL, AGENT_API_BASE, AGENT_REASONING, AGENT_TIMEOUT_SECONDS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, PUBLIC_APP_URL, OSRM_URL, EMERGENT_LLM_KEY, EMERGENT_EMAIL_KEY, EMAIL_FROM_NAME
- frontend: REACT_APP_BACKEND_URL

## Note

All fleet and customer data is fictional.
