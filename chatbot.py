import os
import json
import faiss
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from groq import Groq
import pyttsx3
import speech_recognition as sr
import re

# ===============================
# 1. Setup
# ===============================
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load FAISS index + docs
embeddings = np.load("embeddings (1) (1).npy", mmap_mode='r')
with open("docs (1).json", "r", encoding="utf-8") as f:
    docs = json.load(f)

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print(f"✅ Loaded FAISS index with {index.ntotal} chunks.")
model = SentenceTransformer("all-MiniLM-L6-v2")

# ===============================
# 2. Voice Input (Offline)
# ===============================
def take_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Speak now...")
        recognizer.pause_threshold = 1
        audio = recognizer.listen(source)

    try:
        print("🧠 Recognizing...")
        query = recognizer.recognize_google(audio, language='en-IN')
        print("🗣️ You said:", query)
        return query
    except Exception:
        print("⚠️ Sorry, I didn’t catch that. Please try again.")
        return None

# ===============================
# 3. Groq Inference
# ===============================
def groq_infer(question, context=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a legal assistant trained to answer only in the domain of Indian law i a very proffesional tone. "
                "Respond with accurate and concise information using IPC/BNS sections, "
                "and include helpline numbers or step-by-step FIR filing procedures wherever relevant. also include the source of infoemation sapecificaly from database or internet . dont bold any text just use plain text"
                "If the question is outside law, say: "
                "'I'm sorry, I can only assist with legal questions.'"
            )
        }
    ]
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    messages.append({"role": "user", "content": question})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0,
        max_tokens=512
    )
    return response.choices[0].message.content

# ===============================
# 4. RAG Query
# ===============================
def rag_query(question, k=3):
    q_emb = model.encode([question])
    D, I = index.search(np.array(q_emb), k)
    context = "\n\n".join([docs[idx] for idx in I[0]])
    return groq_infer(question, context)

# ===============================
# 5. Main Flow
# ===============================
def main():
    print("\n⚖️ Welcome to the Indian Law RAG Assistant")
    mode = input("Choose mode (voice/text): ").strip().lower()

    if mode == "voice":
        query = take_voice_input()
        if not query:
            return
    else:
        query = input("Enter your legal query: ")

    answer = rag_query(query)
    print("\n📜 Answer:\n", answer)
   

    # Remove Markdown bold and italic markers
    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)  # **bold**
    answer = re.sub(r'\*(.*?)\*', r'\1', answer)      # *italic*
    answer = re.sub(r'__(.*?)__', r'\1', answer)      # __bold__
    answer= re.sub(r'_(.*?)_', r'\1', answer)        # _italic_
    

    # Text-to-Speech (Offline)
    engine = pyttsx3.init()
    engine.say(answer)
    engine.runAndWait()




    



# ===============================
# Run
# ===============================
if __name__ == "__main__":
    main()
