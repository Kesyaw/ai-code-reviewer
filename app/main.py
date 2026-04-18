from fastapi import FastAPI, Request
from groq import Groq
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = FastAPI()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_pr_diff(repo_full_name, pr_number):
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    files = response.json()
    
    diff_text = ""
    for file in files:
        filename = file.get("filename", "")
        patch = file.get("patch", "")
        diff_text += f"\n--- {filename} ---\n{patch}\n"
    
    return diff_text

def review_code_with_ai(diff_text, pr_title):
    prompt = f"""Kamu adalah senior developer yang bertugas mereview Pull Request.

PR Title: {pr_title}

Perubahan kode:
{diff_text}

Berikan review dalam format berikut:
1. **Ringkasan** — apa yang dilakukan PR ini
2. **Potensi Bug** — kalau ada bug atau error yang mungkin terjadi
3. **Security** — kalau ada celah keamanan
4. **Saran Perbaikan** — saran konkret untuk improve kode

Jawab dalam Bahasa Indonesia. Kalau kodenya sudah bagus, bilang juga!"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def post_github_comment(repo_full_name, pr_number, comment):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"## 🤖 AI Code Review\n\n{comment}"}
    requests.post(url, headers=headers, json=data)

@app.get("/")
def root():
    return {"message": "AI Code Reviewer is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored"}
    
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    pr_title = pr.get("title", "")
    repo_full_name = payload.get("repository", {}).get("full_name", "")
    
    print(f"\n🔔 PR #{pr_number}: '{pr_title}' — mulai review...")
    
    diff = get_pr_diff(repo_full_name, pr_number)
    review = review_code_with_ai(diff, pr_title)
    post_github_comment(repo_full_name, pr_number, review)
    
    print(f"✅ Review selesai dan sudah diposting ke PR #{pr_number}")
    
    return {"status": "reviewed"}