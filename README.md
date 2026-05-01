# AI Code Reviewer

> Sistem AI yang otomatis mereview Pull Request di GitHub — mendeteksi bug, security vulnerability, dan memberikan saran perbaikan menggunakan LLM.

## Live Demo

Setiap kali ada Pull Request baru, AI langsung posting review otomatis:

**Dashboard:** https://kesyaw-ai-code-reviewer.streamlit.app

**Model:** https://huggingface.co/Kesyaw/code-reviewer-bilingual-lora

## Arsitektur
Developer Push PR
↓
GitHub Actions (triggered otomatis)
↓
Fetch PR Diff (GitHub API)
↓
LangChain ReAct Agent
├── search_similar_bugs → RAG + pgvector
├── analyze_security    → SQL injection, hardcoded secrets, dll
├── analyze_performance → N+1 query, memory leak, dll
└── analyze_code_quality → code smells, naming, structure
↓
Agent gabungkan semua hasil
↓
Post Komentar ke GitHub PR
↓
Simpan ke PostgreSQL + pgvector

## Tech Stack

| Layer             | Technology                        |
|-------------------|-----------------------------------|
| Agent Framework   | LangChain + LangGraph             |
| API Server        | FastAPI + Uvicorn                 |
| AI Model          | LLaMA 3.1 8B via Groq API         |
| RAG Pipeline      | sentence-transformers + pgvector  |
| Database          | PostgreSQL 15                     |
| CI/CD             | GitHub Actions                    |
| Containerization  | Docker                            |

## Features

- **Agentic Review** — LangChain ReAct Agent yang decide sendiri tools mana yang dipanggil
- **Multi-tool Analysis** — 4 specialized tools: security, performance, code quality, RAG search
- **RAG Memory** — AI mengingat pola bug dari PR sebelumnya menggunakan pgvector
- **Auto Review** — triggered otomatis setiap PR dibuka atau diupdate
- **Fallback System** — kalau agent gagal, otomatis fallback ke review biasa
- **GitHub Actions** — serverless, gratis, zero maintenance
- **Bilingual** — support review dalam Bahasa Indonesia dan Inggris

## Quick Start

### Prerequisites
- Python 3.10+
- Docker
- Groq API Key (gratis di console.groq.com)
- GitHub Personal Access Token

### Installation

```bash
# Clone repo
git clone https://github.com/Kesyaw/ai-code-reviewer.git
cd ai-code-reviewer

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env dengan API key kamu
```

### Setup Database

```bash
# Jalankan PostgreSQL
docker run -d \
  --name ai-reviewer-db \
  -e POSTGRES_USER=kesyaw \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=ai_reviewer \
  -p 5432:5432 \
  postgres:15

# Install pgvector
docker exec -it ai-reviewer-db psql -U kesyaw -d ai_reviewer \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Run Locally

```bash
uvicorn app.main:app --reload
```

### GitHub Actions Setup

1. Fork repo ini
2. Tambah secrets di **Settings → Secrets → Actions**:
   - `GROQ_API_KEY`
3. Setiap PR akan otomatis direview oleh AI

## Project Structure
ai-code-reviewer/
├── app/
│   ├── main.py          # FastAPI server + webhook handler
│   ├── agent.py         # LangChain ReAct Agent + 4 tools
│   ├── database.py      # PostgreSQL models + connection
│   └── rag.py           # RAG pipeline + pgvector
├── scripts/
│   └── review.py        # AI review logic (dipakai GitHub Actions)
├── .github/
│   └── workflows/
│       └── review.yml   # GitHub Actions workflow
└── requirements.txt

## Roadmap

- [ ] Fine-tuning CodeLlama dengan LoRA (bilingual EN/ID)
- [x] Dashboard monitoring review history (Streamlit + Plotly)
- [ ] Support multi-language (JS, Go, Java)
- [ ] Slack/Discord notification
- [ ] RLHF feedback loop (thumbs up/down)

## Author

**Kesya** — [@Kesyaw](https://github.com/Kesyaw)

---

*Built with ❤️ as an AI Engineering portfolio project*