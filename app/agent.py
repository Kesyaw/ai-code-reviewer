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
        f"""You are a security expert. Analyze the following code SPECIFICALLY for security issues.

Check for: SQL Injection, Hardcoded credentials, Command injection,
Missing authentication, Sensitive data exposure.

Code:
{code}

Output format:
[SEVERITY: HIGH/MEDIUM/LOW] Issue name: description + concrete solution.
If no issues: write "No security issues found." """
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
        f"""You are a performance engineer. Analyze the following code SPECIFICALLY for performance issues.

Check for: N+1 query, Unnecessary loops, Memory leaks,
Missing pagination, Inefficient data structures.

Code:
{code}

Output format:
[IMPACT: HIGH/MEDIUM/LOW] Issue name: description + concrete solution.
If no issues: write "No performance issues found." """
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
            return "No similar bugs found in history."
        context = "Similar bugs found in history:\n"
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
        f"""You are a senior developer. Analyze the following code for quality issues.

Check for: Code smells, Poor naming, Missing error handling,
Missing input validation, Poor structure, Missing documentation.

Code:
{code}

Output format:
[TYPE: SMELL/ERROR/STRUCTURE] Issue name: description + concrete solution.
If no issues: write "Code quality is good." """
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

    # ============================================================
    # AUTO-DETECT BAHASA dari PR title
    # Kalau PR title pakai kata Inggris → review Inggris
    # Kalau PR title pakai kata Indonesia → review Indonesia
    # ============================================================
    english_keywords = [
        'add', 'fix', 'update', 'refactor', 'remove', 'feat',
        'bug', 'test', 'docs', 'chore', 'improve', 'implement',
        'create', 'delete', 'merge', 'hotfix', 'release', 'revert'
    ]
    pr_title_lower = pr_title.lower()
    is_english = any(kw in pr_title_lower for kw in english_keywords)

    if is_english:
        language_instruction = "Respond entirely in English."
        format_section = """## Summary
## Security Issues
## Performance Issues
## Code Quality
## Similar Past Bugs
## Recommendation"""
    else:
        language_instruction = "Jawab seluruhnya dalam Bahasa Indonesia."
        format_section = """## Ringkasan
## Masalah Keamanan
## Masalah Performa
## Kualitas Kode
## Bug Serupa
## Rekomendasi"""

    prompt = f"""You are an AI Code Reviewer. Review the following Pull Request thoroughly.

PR Title: {pr_title}
PR Number: #{pr_number}
Repository: {repo_name}

Code changes:
{diff_text[:3000]}

Instructions:
1. Use search_similar_bugs to check for similar bugs in history
2. Use analyze_security to check security issues
3. Use analyze_performance to check performance issues
4. Use analyze_code_quality to check code quality
5. After all tools complete, provide a comprehensive review summary

{language_instruction}

Provide final review in this format:
{format_section}"""

    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=prompt)]
        })

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