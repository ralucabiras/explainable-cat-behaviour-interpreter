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

For a backend outside Docker, use `MONGODB_URL=mongodb://localhost:27017`.
Docker Compose automatically uses its internal `mongo` hostname regardless of this local
setting. The frontend defaults to `http://localhost:8000/api/v1`.

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
| `PATCH` | `/api/v1/pets/{id}` | Update an owned cat profile |
| `DELETE` | `/api/v1/pets/{id}` | Delete a cat and its observations |
| `POST` | `/api/v1/observations` | Save a text and context observation |
| `GET` | `/api/v1/observations` | List observations; optionally filter by `pet_id` |
| `GET` | `/api/v1/observations/{id}` | Retrieve one observation |
| `DELETE` | `/api/v1/observations/{id}` | Permanently delete an observation |

Creating an observation synchronously runs text and context interpretation and returns the completed explainable result. Audio inference remains intentionally inactive.

Short private MP4, WebM, and MOV clips can be attached through the optional video flow.
Clips are limited to 50 MB and 30 seconds. The system extracts deterministic motion
features and representative frames, but video does not yet influence the final fused
interpretation. Media access requires ownership and explicit upload consent.

Pet and observation endpoints require a bearer token and only return records belonging to the authenticated user.
Expired access tokens are cleared by the frontend and force a full return to the public
landing page before another authenticated request can be made.

The authenticated app includes a global recent-observation view, per-cat newest-first
timelines, behaviour-state and date filtering, permanent interpretation pages, and
profile/observation deletion. Observation inputs and results are immutable so saved
interpretations remain reproducible.

Cat profiles include feeding routine, activity level, sociability, routine sensitivity,
known triggers, and personality notes. Situationally relevant profile traits are recorded
as explicit context evidence during interpretation. Cat names are unique per owner using
case-insensitive, whitespace-normalized matching.

Observation history accepts `pet_id`, `state`, `date_from`, `date_to`, `skip`, and
`limit` query parameters. The default page size is 20 and the maximum is 100.

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

## Reproducible baseline evaluation

The versioned evaluation dataset contains synthetic, brief-derived scenarios rather than
user journal data. It measures deterministic software behaviour and does not establish
clinical or veterinary validity.

Run the text-only, context-only, and fused evaluation from the backend directory:

```bash
python -m app.evaluation.cli \
  --dataset evaluation/datasets/v1.json \
  --output evaluation/results/current
```

The output includes a compact JSON summary, full JSON report, prediction CSV, and one
confusion-matrix CSV per configuration. Metrics include accuracy, per-state
precision/recall/F1, macro and weighted F1, uncertain coverage, safety precision/recall,
and fixed-bin calibration.
Confidence in these reports is rule-evidence strength, not a validated probability.

To detect prediction changes against a prior report, add:

```bash
--compare evaluation/baseline/report.json
```

The command exits with status `1` when a scenario's predicted state or safety escalation
changes, and status `2` for invalid input or file errors. Add scenarios by following the
existing JSON schema: every case needs a unique stable ID, cat profile, observation,
expected state, and expected safety flag.

## Video dataset preparation

The observable-action dataset workflow is provenance-first and does not bundle third-party
videos. Its initial inventory and annotation guide live under `backend/video_dataset`.

```bash
cd backend
python -m app.video_dataset.cli validate --manifest video_dataset/manifests/v1.inventory.json
python -m app.video_dataset.cli inspect --manifest manifest.json --media-root video_dataset/media --output inspected.json
python -m app.video_dataset.cli split --manifest inspected.json --output split.json
python -m app.video_dataset.cli report --manifest split.json --output video_dataset/reports/feasibility.json
```

The tooling validates licenses and provenance, decodes files, records checksums and media
metadata, detects exact and possible visual duplicates, preserves source groups across
splits, and applies the documented training-feasibility thresholds.

## Current analysis scope

The English-language baseline covers nine broad cat behaviour states, context-aware weighted evidence, simple negation, uncertainty, alternatives, and urgent safety escalation. Its confidence value is evidence strength from deterministic rules, not a medically validated probability.
