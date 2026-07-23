import os
from dotenv import load_dotenv

load_dotenv()

# ===== Пути к данным =====
DATA_DIR = os.getenv("DATA_DIR", "./data")
DATABASE_PATH = os.path.join(DATA_DIR, "crm.db")
CONSULT_DB_PATH = os.path.join(DATA_DIR, "consultations.db")

# ===== Токены ботов =====
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
CONSULT_BOT_TOKEN = os.getenv("CONSULT_BOT_TOKEN")

# ===== ID админа =====
ADMIN_ID = int(os.getenv("ADMIN_ID", 258670125))

# ===== Названия ботов =====
MAIN_BOT_USERNAME = os.getenv("MAIN_BOT_USERNAME", "gtcm_assistant_bot")
CONSULT_BOT_USERNAME = os.getenv("CONSULT_BOT_USERNAME", "gtcm_consult_bot")

# ===== AI =====
AI_ENABLED = os.getenv("AI_ENABLED", "False").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")