# AI Product Manager

An MCP-powered AI pipeline that transforms raw customer feedback into a full product roadmap — automatically.

## What it does

Feed it customer feedback. It produces:

- **Clustered issues** — semantically grouped, duplicates removed, frequency scored
- **Ranked opportunities** — scored on customer impact, business impact, and effort
- **Product requirement docs** — problem, users affected, solution, acceptance criteria, metrics
- **Engineering tickets** — broken down per acceptance criterion with priority and estimate

## Pipeline

```
Customer Feedback
      │
      ▼
Feedback Agent → clusters + frequency scores
      │
      ▼
Prioritization Agent → P1 / P2 / P3 opportunities
      │
      ▼
PRD Agent → full product requirements (markdown)
      │
      ▼
Ticket Agent → engineering backlog
      │
      ▼
Manager Agent → strategic summary
```

## Stack

| Layer | Tech |
|---|---|
| Agents | Claude API (claude-sonnet-4-6) |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | Next.js 14 + Tailwind CSS |
| MCP Server | Official MCP Python SDK |

## Project Structure

```
ai-product-manager/
├── agents/                  # Agent prompt definitions (.md)
├── backend/
│   ├── agents/              # Claude API agent runners
│   ├── api/routes/          # FastAPI endpoints
│   ├── db/                  # SQLAlchemy models + database
│   └── services/            # Orchestration logic
├── frontend/                # Next.js app
│   └── src/
│       ├── app/             # Pages (feedback, insights, roadmap, prds, tickets)
│       ├── components/      # Sidebar, Providers
│       └── lib/api.ts       # Typed API client
└── mcp_servers/             # MCP server + tools
```

## Setup

### Backend

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Environment Variables

```env
DATABASE_URL=sqlite+aiosqlite:///./ai_pm.db
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-sonnet-4-6
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/feedback/ingest` | Submit feedback |
| POST | `/api/v1/feedback/ingest/batch` | Batch ingest (CSV) |
| POST | `/api/v1/feedback/analyze` | Run Feedback Agent |
| POST | `/api/v1/insights/prioritize` | Run Prioritization Agent |
| POST | `/api/v1/prd/generate/{id}` | Run PRD Agent |
| POST | `/api/v1/tickets/generate/{id}` | Run Ticket Agent |
| POST | `/api/v1/pipeline/run` | Run full pipeline |
| GET | `/api/v1/pipeline/status` | Pipeline data counts |

## MCP Tools

| Tool | Description |
|---|---|
| `store_feedback` | Save raw customer feedback |
| `search_feedback` | Search feedback by keyword |
| `create_prd` | Create a PRD record |
| `create_ticket` | Create an engineering ticket |
| `list_tickets` | List tickets with filters |

## Pages

| Page | Description |
|---|---|
| Upload Feedback | Paste or upload feedback, run analysis |
| Insights | Clusters, frequency scores, ranked opportunities |
| Roadmap | P1/P2/P3 Kanban with opportunity cards |
| PRDs | Expandable PRDs with all sections |
| Tickets | Engineering tasks grouped by PRD |
