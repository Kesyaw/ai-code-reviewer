import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import init_db, save_review

import requests
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
PR_NUMBER = os.environ.get("PR_NUMBER")
PR_TITLE = os.environ.get("PR_TITLE")
REPO_NAME = os.environ.get("REPO_NAME")
client = Groq(api_key=GROQ_API_KEY)

def get_pr_diff():
    url = f"https://api.github.com/repos/{REPO_NAME}/pulls/{PR_NUMBER}/files"
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
        if patch:
            diff_text += f"\n--- {filename} ---\n{patch}\n"
    
    return diff_text

def review_code(diff_text):
    prompt = f"""Kamu adalah senior developer yang bertugas mereview Pull Request.

PR Title: {PR_TITLE}

Perubahan kode:
{diff_text}

Berikan review dalam format berikut:
1. **Ringkasan** — apa yang dilakukan PR ini
2. **Potensi Bug** — kalau ada bug atau error yang mungkin terjadi
3. **Security** — kalau ada celah keamanan
4. **Saran Perbaikan** — saran konkret untuk improve kode

Jawab dalam Bahasa Indonesia. Kalau kodenya sudah bagus, bilang juga!"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def post_comment(comment):
    url = f"https://api.github.com/repos/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": f"## 🤖 AI Code Review\n\n{comment}"}
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"✅ Review berhasil diposting ke PR #{PR_NUMBER}")
    else:
        print(f"❌ Gagal posting: {response.status_code}")

if __name__ == "__main__":
    print(f"🔍 Mereview PR #{PR_NUMBER}: {PR_TITLE}")
    diff = get_pr_diff()
    
    if not diff:
        print("⚠️ Tidak ada perubahan kode yang bisa direview")
    else:
        review = review_code(diff)
        post_comment(review)
        
        # Simpan ke database kalau DATABASE_URL tersedia
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            from app.database import init_db, save_review
            init_db()
            save_review(REPO_NAME, PR_NUMBER, PR_TITLE, review)
        else:
            print("ℹ️ DATABASE_URL tidak ada, skip simpan ke database")