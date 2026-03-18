# Smart NVR

Intelligent Network Video Recorder with AI-powered video analytics. Smart NVR provides real-time camera monitoring, event detection (line crossing, zone intrusion, smoking, weapons, loitering, crowd detection), and automated alerting.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend   │────▶│  PostgreSQL  │
│  React/Vite  │     │   FastAPI   │     │   Database   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────▼─────┐ ┌────▼────┐
              │   Redis    │ │  go2rtc  │
              │  Streams   │ │  RTSP/   │
              │            │ │  WebRTC  │
              └────────────┘ └─────────┘
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Redis Streams
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: PostgreSQL 16
- **Cache/Streams**: Redis 7
- **Video**: go2rtc (RTSP/WebRTC)
- **Infrastructure**: Docker Compose

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/maxetek/smart-nvr.git
   cd smart-nvr
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Start all services:
   ```bash
   docker compose up -d
   ```

4. Access the application:
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **go2rtc**: http://localhost:1984

## Development

Start services with hot-reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Migrations

```bash
cd backend
alembic upgrade head
```

## Project Structure

```
smart-nvr/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── models/   # SQLAlchemy models
│   │   ├── routers/  # API route handlers
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── alembic/      # Database migrations
├── frontend/         # React application
│   └── src/
│       ├── components/
│       └── pages/
└── docker/           # Service configurations
```

## License

MIT
