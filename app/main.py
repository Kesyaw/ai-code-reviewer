from fastapi import FastAPI, Request
import hmac
import hashlib

app = FastAPI()

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
    pr = payload.get("pull_request", {})
    pr_title = pr.get("title", "")
    pr_number = pr.get("number", "")
    sender = payload.get("sender", {}).get("login", "")
    
    print(f"\n🔔 PR #{pr_number}: '{pr_title}' — action: {action} by {sender}")
    
    return {"status": "received"}