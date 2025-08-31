import json
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv
import os

# load env
load_dotenv()

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL")

app = FastAPI(title="FastAPI WebPush")

# allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store (for demo)
subscriptions = []

class SubscriptionIn(BaseModel):
    endpoint: str
    keys: dict

class NotificationPayload(BaseModel):
    title: str
    body: str
    url: str = "/"

@app.get("/vapid/public")
def get_public_key():
    return {"publicKey": VAPID_PUBLIC_KEY}

@app.post("/subscribe")
def subscribe(sub: SubscriptionIn):
    if not any(s["endpoint"] == sub.endpoint for s in subscriptions):
        subscriptions.append(sub.dict())
    return {"success": True, "total": len(subscriptions)}

@app.post("/send")
def send_notification(payload: NotificationPayload, background_tasks: BackgroundTasks):
    for sub in subscriptions:
        background_tasks.add_task(push_to_subscriber, sub, payload.dict())
    return {"queued": len(subscriptions)}

def push_to_subscriber(subscription, payload):
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_EMAIL}
        )
    except WebPushException as ex:
        print("Push failed:", repr(ex))