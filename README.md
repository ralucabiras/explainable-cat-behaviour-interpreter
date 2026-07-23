# Animal Behaviour Interpreter

An explainable, multimodal companion-cat behaviour interpreter. This foundation deliberately starts with pet profiles, written observations, and situational context. Video comes after the text/context pipeline is stable; audio is deferred until the rest of the system is reliable.

The application communicates possible interpretations rather than diagnoses. It must preserve uncertainty, provide alternative explanations, and direct users to a veterinarian for sudden or concerning signs.

## Architecture

```text
frontend/                 React + TypeScript user interface
backend/app/
  api/routes/             FastAPI HTTP endpoints
  models/                 API and persistence contracts
  services/               Application and validation logic
  repositories/           MongoDB persistence boundary
  ai/                     Independent text, context, video, audio, and fusion modules
compose.yaml              Frontend, backend, and MongoDB development services
```

Analysis output is stored separately for each modality, including a status, label, evidence, confidence, alternatives, recommendations, and explanation. Text and context use a deterministic, auditable rules baseline; video and audio remain pending.

## Run with Docker

Prerequisites: Docker Desktop with Compose.

```bash
cp .env.example .env
docker compose up --build
```

Open:

- UI: http://localhost:5173
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

MongoDB data is retained in the `mongo_data` named volume. Stop the services with `docker compose down`.

## Run without Docker

Start a local MongoDB instance on port `27017`. Then run the backend (Python 3.12+):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

In another terminal, run the frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

For a backend outside Docker, set `MONGODB_URL=mongodb://localhost:27017`. The frontend defaults to `http://localhost:8000/api/v1`.

## Current API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Service health |
| `POST` | `/api/v1/auth/signup` | Create an unverified user account |
| `GET` | `/api/v1/auth/confirm-email` | Confirm an email token |
| `POST` | `/api/v1/auth/login` | Log in after confirmation |
| `GET` | `/api/v1/auth/me` | Retrieve the authenticated user |
| `POST` | `/api/v1/pets` | Create a cat profile |
| `GET` | `/api/v1/pets` | List cat profiles |
| `GET` | `/api/v1/pets/{id}` | Retrieve one profile |
| `POST` | `/api/v1/observations` | Save a text and context observation |
| `GET` | `/api/v1/observations` | List observations; optionally filter by `pet_id` |
| `GET` | `/api/v1/observations/{id}` | Retrieve one observation |

Creating an observation synchronously runs text and context interpretation and returns the completed explainable result. Media fields exist in the backend models, but video and audio inference are intentionally not active yet.

Pet and observation endpoints require a bearer token and only return records belonging to the authenticated user.

## Gmail email confirmation

Local development defaults to `EMAIL_DELIVERY_MODE=console`. After sign-up, the UI displays a development confirmation link and the backend logs it.

To send real confirmation mail through Gmail:

1. Enable two-step verification on the sending Google account.
2. Create a Google app password for this application.
3. Set these values in the root `.env` file:

```env
JWT_SECRET=use-a-long-random-value-here
EMAIL_DELIVERY_MODE=gmail
GMAIL_ADDRESS=your-address@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password
```

Use the app password, not the Gmail account password. Never commit `.env`; it is ignored by Git. Gmail SMTP uses `smtp.gmail.com` over SSL on port `465`.

## Development checks

```bash
cd backend
ruff check .
pytest

cd ../frontend
npm run test
npm run lint
npm run build
```

## Current analysis scope

The English-language baseline covers nine broad cat behaviour states, context-aware weighted evidence, simple negation, uncertainty, alternatives, and urgent safety escalation. Its confidence value is evidence strength from deterministic rules, not a medically validated probability.
