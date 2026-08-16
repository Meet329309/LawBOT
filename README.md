# NyaayGPT — Indian Legal AI Assistant

NyaayGPT is a full-stack Indian legal AI assistant that combines a Flutter application, FastAPI backend, MongoDB, Retrieval-Augmented Generation (RAG), FAISS, Sentence Transformers, and Groq's Llama model.

The system is designed to provide users with Indian-law-focused answers through text and voice-based interaction while maintaining user authentication and conversation history.

## Features

* Indian legal question answering using RAG
* Text-based legal chat
* Voice input using speech-to-text
* Voice output using text-to-speech
* User registration and login
* JWT-based authentication
* Persistent chat history using MongoDB
* FAISS-based semantic retrieval
* Legal document knowledge base
* Groq Llama-based answer generation
* Flutter-based user interface
* FastAPI REST API

## Project Architecture

```text
                    ┌─────────────────────┐
                    │     Flutter App     │
                    │                     │
                    │  Text Chat          │
                    │  Voice Chat         │
                    │  Authentication     │
                    └──────────┬──────────┘
                               │
                         HTTP + JWT
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │                     │
                    │  Authentication     │
                    │  Chat APIs          │
                    │  RAG Integration    │
                    └───────┬───────┬─────┘
                            │       │
                            ▼       ▼
                    ┌───────────┐  ┌──────────────────┐
                    │ MongoDB   │  │    RAG System    │
                    │           │  │                  │
                    │ Users     │  │ Sentence         │
                    │ Chats     │  │ Transformers     │
                    │ Messages  │  │ FAISS            │
                    └───────────┘  │ Legal Documents  │
                                   │ Groq / Llama      │
                                   └──────────────────┘
```

## How the RAG System Works

When a user asks a legal question, NyaayGPT follows this process:

```text
User Question
      ↓
SentenceTransformer
(all-MiniLM-L6-v2)
      ↓
Question Embedding
      ↓
FAISS Similarity Search
      ↓
Top Relevant Legal Chunks
      ↓
Groq Llama 3.3 70B
      ↓
Generated Legal Response
      ↓
Flutter Application
```

The system uses the existing legal document corpus and corresponding embeddings to retrieve relevant information before generating the response.

## Technology Stack

### Frontend

* Flutter
* Dart
* `http`
* `shared_preferences`
* `speech_to_text`
* `flutter_tts`

### Backend

* Python
* FastAPI
* Uvicorn
* Motor
* MongoDB
* JWT authentication
* Passlib / bcrypt
* python-dotenv

### AI / RAG

* Sentence Transformers
* `all-MiniLM-L6-v2`
* FAISS
* NumPy
* Groq API
* Llama 3.3 70B Versatile

## Project Structure

```text
NyaayGPT.mini/
│
├── main.py
├── chatbot.py
├── requirements.txt
├── docs (1).json
├── embeddings (1) (1).npy
├── .env.example
├── .gitignore
│
└── nyaaygpt_app/
    ├── lib/
    │   ├── main.dart
    │   ├── pages/
    │   └── services/
    │
    ├── pubspec.yaml
    ├── pubspec.lock
    └── ...
```

## Backend API

The FastAPI backend currently provides the following endpoints:

| Method | Endpoint           | Description                      |
| ------ | ------------------ | -------------------------------- |
| GET    | `/`                | Check whether the API is running |
| POST   | `/signup`          | Register a new user              |
| POST   | `/login`           | Authenticate an existing user    |
| POST   | `/ask`             | Ask a legal question             |
| POST   | `/chats/create`    | Create a new chat                |
| GET    | `/chats`           | Get the user's chats             |
| GET    | `/chats/{chat_id}` | Get a specific chat              |
| PATCH  | `/chats/{chat_id}` | Update a chat title              |

## Local Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd NyaayGPT.mini
```

### 2. Backend setup

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
MONGODB_URL=your_mongodb_connection_string
```

Do not commit `.env` to GitHub.

### 4. Start MongoDB

The project uses MongoDB for user accounts and chat history.

For local development:

```env
MONGODB_URL=mongodb://127.0.0.1:27017/lawbot_db
```

Make sure the MongoDB server is running before starting FastAPI.

### 5. Start the FastAPI backend

From the project root:

```bash
uvicorn main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Swagger API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Flutter Setup

Navigate to the Flutter project:

```bash
cd nyaaygpt_app
```

Install Flutter dependencies:

```bash
flutter pub get
```

Check available devices:

```bash
flutter devices
```

Run the application on a supported target, for example:

```bash
flutter run -d chrome
```

or:

```bash
flutter run -d windows
```

The FastAPI backend must be running separately while using the application.

## Voice Features

NyaayGPT supports voice interaction through:

* `speech_to_text` for converting speech into text
* `flutter_tts` for reading generated responses aloud

The voice workflow is:

```text
User Speech
    ↓
Speech-to-Text
    ↓
Legal Question
    ↓
FastAPI + RAG
    ↓
AI Answer
    ↓
Text-to-Speech
    ↓
Spoken Response
```

## Authentication

User authentication is handled through JWT tokens.

The general authentication flow is:

```text
Signup / Login
      ↓
FastAPI
      ↓
MongoDB
      ↓
JWT Token
      ↓
Flutter stores token
      ↓
Authenticated API Requests
```

Chat requests use the authenticated user's identity to associate conversations with the correct account.

## Current Limitations

NyaayGPT is currently a working project under development and has some known limitations.

### Legal knowledge coverage

The current knowledge base does not contain every Indian legal provision or every current judgment. As a result, the system may not be able to answer questions about provisions that are missing from the corpus.

### Current vs. historical law

The current retrieval system can retrieve older legal material alongside newer material. It does not yet have a dedicated mechanism for automatically identifying whether a provision has been repealed, replaced, amended, or superseded.

### Citation verification

The system currently does not independently verify every case citation or legal authority generated by the language model.

### Chat service integration

Some Flutter chat-service functionality does not currently match all FastAPI routes. In particular, some older chat operations use different endpoint names or response formats.

### Localhost networking

The application currently uses a local backend address during development. Running the Flutter application on a physical Android device requires the backend URL to be reachable from that device rather than using `127.0.0.1`.

## Security

Never commit credentials or secrets to GitHub.

The following should remain private:

* Groq API keys
* MongoDB credentials
* JWT secret keys
* `.env` files

Use `.env.example` to document required environment variables without exposing real credentials.

## Project Goal

The goal of NyaayGPT is to provide an accessible Indian legal information assistant that combines conversational AI with retrieval from a legal knowledge base.

The project is intended as a legal-information and research assistant and should not be treated as a replacement for a qualified lawyer or professional legal advice.

## Future Improvements

Potential improvements include:

* Current-law and amendment tracking
* Citation verification
* Authority ranking
* Better legal source attribution
* Detection of conflicting judgments
* Improved retrieval and reranking
* Evidence-confidence scoring
* Stronger hallucination detection
* Improved chat-history integration
* Production deployment
* Mobile-device backend configuration

## Authors

NyaayGPT was developed as a group project.

For educational and research purposes.
