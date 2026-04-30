# ============================================================
# app/agent.py
# Code Review Agent menggunakan LangChain + LangGraph
#
# LangChain 1.x menggunakan langgraph untuk agent
# ReAct pattern: Reason → Act → Observe → Reason lagi
# ============================================================

import os
import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ============================================================
# INISIALISASI LLM
# ============================================================
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0.1,
)

# ============================================================
# TOOL 1: Analisis Security
# ============================================================
@tool
def analyze_security(code: str) -> str:
    """Analisis kode untuk security vulnerabilities seperti SQL injection,
    hardcoded credentials, command injection, dan missing authentication.
    Gunakan tool ini jika kode mengandung database query, user input, atau auth."""

    response = llm.invoke(
        f"""Kamu adalah security expert. Analisis kode berikut KHUSUS untuk security issues.

Cek untuk: SQL Injection, Hardcoded credentials, Command injection,
Missing authentication, Sensitive data exposure.

Kode:
{code}

Format output:
[SEVERITY: HIGH/MEDIUM/LOW] Nama issue: deskripsi + solusi konkret.
Kalau tidak ada issue: tulis "No security issues found." """
    )
    return response.content


# ============================================================
# TOOL 2: Analisis Performance
# ============================================================
@tool
def analyze_performance(code: str) -> str:
    """Analisis kode untuk performance issues seperti N+1 query,
    unnecessary loops, memory leaks, dan missing pagination.
    Gunakan tool ini jika kode mengandung loop, database query, atau data processing."""

    response = llm.invoke(
        f"""Kamu adalah performance engineer. Analisis kode berikut KHUSUS untuk performance issues.

Cek untuk: N+1 query, Unnecessary loops, Memory leaks,
Missing pagination, Inefficient data structures.

Kode:
{code}

Format output:
[IMPACT: HIGH/MEDIUM/LOW] Nama issue: deskripsi + solusi konkret.
Kalau tidak ada issue: tulis "No performance issues found." """
    )
    return response.content


# ============================================================
# TOOL 3: Search Similar Bugs dari RAG
# ============================================================
@tool
def search_similar_bugs(code: str) -> str:
    """Cari bug serupa dari database review history menggunakan RAG.
    Selalu gunakan tool ini untuk memberikan konteks dari bug yang
    pernah ditemukan sebelumnya."""

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "RAG database tidak tersedia di environment ini — skip."

    try:
        from app.rag import find_similar_code
        results = find_similar_code(code, top_k=3)
        if not results:
            return "Tidak ada bug serupa di history."
        context = "Bug serupa yang pernah ditemukan:\n"
        for i, r in enumerate(results, 1):
            context += f"\n{i}. PR: '{r[0]}'\n   Bug: {str(r[2])[:150]}\n"
        return context
    except Exception as e:
        return f"RAG tidak tersedia: {e}"
    
# ============================================================
# TOOL 4: Analisis Code Quality
# ============================================================
@tool
def analyze_code_quality(code: str) -> str:
    """Analisis kode untuk code smells, readability, error handling,
    dan best practices. Gunakan tool ini untuk semua kode."""

    response = llm.invoke(
        f"""Kamu adalah senior developer. Analisis kode berikut untuk code quality.

Cek untuk: Code smells, Poor naming, Missing error handling,
Missing input validation, Poor structure, Missing documentation.

Kode:
{code}

Format output:
[TYPE: SMELL/ERROR/STRUCTURE] Nama issue: deskripsi + solusi konkret.
Kalau tidak ada issue: tulis "Code quality is good." """
    )
    return response.content


# ============================================================
# SETUP AGENT dengan LangGraph
# ============================================================
tools = [
    search_similar_bugs,
    analyze_security,
    analyze_performance,
    analyze_code_quality,
]

agent = create_react_agent(llm, tools)


# ============================================================
# FUNGSI UTAMA
# ============================================================
def run_agent_review(diff_text: str, pr_number: int,
                     pr_title: str, repo_name: str) -> str:

    print(f"\n🤖 Agent mulai review PR #{pr_number}: {pr_title}")

    prompt = f"""Kamu adalah AI Code Reviewer. Review Pull Request berikut secara menyeluruh.

PR Title: {pr_title}
PR Number: #{pr_number}
Repository: {repo_name}

Perubahan kode:
{diff_text[:3000]}

Instruksi:
1. Gunakan search_similar_bugs untuk cek bug serupa di history
2. Gunakan analyze_security untuk cek security issues
3. Gunakan analyze_performance untuk cek performance issues  
4. Gunakan analyze_code_quality untuk cek code quality
5. Setelah semua tool selesai, berikan summary review yang komprehensif

Berikan final review dalam format:
## Summary
## Security Issues
## Performance Issues  
## Code Quality
## Similar Past Bugs
## Recommendation"""

    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=prompt)]
        })

        # Ambil pesan terakhir dari agent
        final_message = result["messages"][-1].content
        print(f"✅ Agent selesai review PR #{pr_number}")
        return final_message

    except Exception as e:
        print(f"❌ Agent error: {e}")
        return f"Agent review gagal: {e}"


def post_agent_review(repo_name: str, pr_number: int, review: str):
    """Post hasil review agent ke GitHub PR"""
    url = f"https://api.github.com/repos/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    comment = f"## 🤖 Agentic AI Code Review\n\n{review}\n\n---\n*Powered by LangChain ReAct Agent + LLaMA 3.1*"
    response = requests.post(url, headers=headers, json={"body": comment})

    if response.status_code == 201:
        print(f"✅ Review diposting ke PR #{pr_number}")
    else:
        print(f"❌ Gagal post: {response.status_code}")