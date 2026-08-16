from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import jwt
import os
import traceback
from bson import ObjectId
from pydantic import BaseModel, Extra

# ==========================================================
# 1️⃣ Load environment variables
# ==========================================================
load_dotenv()

# ==========================================================
# 2️⃣ Configuration
# ==========================================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
MONGODB_URL = os.getenv("MONGODB_URL")  # Example: mongodb+srv://user:pass@cluster0.mongodb.net/lawbot_db

# ==========================================================
# 3️⃣ MongoDB setup
# ==========================================================
try:
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.lawbot_db
    users_collection = db.users
    chats_collection = db.chats
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print("❌ MongoDB connection error:", e)
    raise e

# ==========================================================
# 4️⃣ FastAPI setup
# ==========================================================
app = FastAPI(title="Law Awareness Bot API")
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# 5️⃣ Lazy-load chatbot
# ==========================================================
_rag_query_func = None

def get_rag_query():
    global _rag_query_func
    if _rag_query_func is None:
        print("🔄 Loading RAG system (first query)...")
        try:
            from chatbot import rag_query
            _rag_query_func = rag_query
            print("✅ RAG system loaded!")
        except Exception as e:
            print(f"❌ Error loading RAG: {e}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"RAG system failed to load: {str(e)}")
    return _rag_query_func

# ==========================================================
# 6️⃣ Models
# ==========================================================
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str



class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

    class Config:
        extra = Extra.allow 

class MessageSend(BaseModel):
    chat_id: Optional[str] = None
    question: str

    class Config:
        extra = Extra.allow


# ==========================================================
# 7️⃣ Auth Helpers
# ==========================================================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==========================================================
# 8️⃣ Routes
# ==========================================================
@app.get("/")
def home():
    return {"message": "✅ Law Awareness Bot API is running!"}

# --- Signup Route ---
@app.post("/signup")
async def signup(request: Request):
    try:
        data = await request.json()
        print("📩 Raw signup request data:", data)

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not all([name, email, password]):
            raise HTTPException(status_code=400, detail="Name, email, and password are required.")

        if not isinstance(password, str):
            raise HTTPException(status_code=400, detail="Password must be a string.")
        if len(password.encode("utf-8")) > 72:
            raise HTTPException(status_code=400, detail="Password too long (max 72 characters).")

        print(f"🔍 Password received: type={type(password)}, value={password[:50]}")

        existing = await users_collection.find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered.")

        hashed_pw = pwd_context.hash(password)

        user_doc = {
            "email": email,
            "name": name,
            "password": hashed_pw,
            "created_at": datetime.utcnow()
        }
        result = await users_collection.insert_one(user_doc)

        token = create_access_token({"user_id": str(result.inserted_id), "email": email})
        print("✅ User created successfully:", email)
        return {"token": token, "name": name, "email": email}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Unexpected signup error:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# --- Login ---
@app.post("/login")
async def login(user: UserLogin):
    try:
        db_user = await users_collection.find_one({"email": user.email})
        if not db_user or not pwd_context.verify(user.password, db_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"user_id": str(db_user["_id"]), "email": user.email})
        return {"token": token, "name": db_user["name"], "email": user.email}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Ask (authenticated) ---
@app.post("/ask")
async def ask_question(message: MessageSend, payload: dict = Depends(verify_token)):
    try:
        question = message.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        rag_query = get_rag_query()
        answer = rag_query(question, k=3)
        user_id = payload["user_id"]

        from bson import ObjectId

        if message.chat_id:
            chat_object_id = ObjectId(message.chat_id)

            # 🟢 Push messages
            result = await chats_collection.update_one(
                {"_id": chat_object_id, "user_id": user_id},
                {
                    "$push": {
                        "messages": [
                            {
                                "role": "user",
                                "text": question,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                            {
                                "role": "bot",
                                "text": answer,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        ]
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            # 🟢 Update title if still default
            if result.matched_count > 0:
                await chats_collection.update_one(
                    {
                        "_id": chat_object_id,
                        "user_id": user_id,
                        "$or": [
                            {"title": {"$exists": False}},
                            {"title": ""},
                            {"title": "New Chat"},
                            {"title": None},
                        ],
                    },
                    {"$set": {"title": question[:60]}},
                )

        else:
            # 🟢 No chat_id: create new chat with question as title
            chat_doc = {
                "user_id": user_id,
                "title": question[:60],
                "messages": [
                    {
                        "role": "user",
                        "text": question,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    {
                        "role": "bot",
                        "text": answer,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            await chats_collection.insert_one(chat_doc)

        return {"question": question, "answer": answer}

    except Exception as e:
        print("❌ /ask ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))




# --- Create new chat ---
@app.post("/chats/create")
async def create_chat(chat: ChatCreate, payload: dict = Depends(verify_token)):
    try:
        user_id = payload["user_id"]
        chat_doc = {
            "user_id": user_id,
            "title": chat.title or "New Chat",
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await chats_collection.insert_one(chat_doc)
        chat_doc["_id"] = str(result.inserted_id)
        return chat_doc
    except Exception as e:
        print("❌ /chats/create ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# --- Get all chats for the user ---
@app.get("/chats")
async def get_chats(payload: dict = Depends(verify_token)):
    try:
        user_id = payload["user_id"]
        cursor = chats_collection.find({"user_id": user_id}).sort("updated_at", -1)
        chats = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            chats.append(doc)
        return chats
    except Exception as e:
        print("❌ /chats GET ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# --- Get single chat by ID ---
@app.get("/chats/{chat_id}")
async def get_chat(chat_id: str, payload: dict = Depends(verify_token)):
    try:
        user_id = payload["user_id"]
        chat_doc = await chats_collection.find_one({"_id": ObjectId(chat_id), "user_id": user_id})
        if not chat_doc:
            raise HTTPException(status_code=404, detail="Chat not found")
        chat_doc["_id"] = str(chat_doc["_id"])
        return chat_doc
    except Exception as e:
        print("❌ /chats/{chat_id} ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    

    # --- Update chat title ---
@app.patch("/chats/{chat_id}")
async def update_chat_title(chat_id: str, request: Request, payload: dict = Depends(verify_token)):
    try:
        user_id = payload["user_id"]
        data = await request.json()
        title = data.get("title", "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title required")
        await chats_collection.update_one(
            {"_id": ObjectId(chat_id), "user_id": user_id},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        return {"message": "Title updated successfully"}
    except Exception as e:
        print("❌ /chats/{chat_id} PATCH ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
# 9️⃣ Entry point
# ==========================================================
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 Starting Law Awareness Bot API")
    print("="*50)
    print("📍 Ensure MongoDB Atlas or local MongoDB is running")
    print("📍 Chatbot will load when first question is asked")
    print("="*50 + "\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
