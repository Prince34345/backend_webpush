from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv
import uvicorn;
import json, os

load_dotenv()

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-webpush.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

subscriptions = []

class SubscriptionIn(BaseModel):
    endpoint: str
    keys: dict

class NotificationPayload(BaseModel):
    title: str
    body: str
    url: str = "/"

@app.get("/")
def read_root():
    return {"message": os.getenv("MY_VARIABLE")}

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
    for sub in subscriptions[:]:
        background_tasks.add_task(push_to_subscriber, sub, payload.dict())
    return {"queued": len(subscriptions)}

def push_to_subscriber(subscription, payload):
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_EMAIL},
        )
    except WebPushException as ex:
        if "410" in str(ex):
            subscriptions.remove(subscription)
