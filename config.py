import os

# Bot tokenini shu yerga kiriting (BotFather'dan olingan)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8819956556:AAGlFJPVK33aPicMF4v3N8Lo1kMz4PaxsLg")

# Admin paneli uchun maxsus parol
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "superadmin123")

# Adminlarning Telegram ID raqamlari (Vergul bilan ajrating, misol uchun "123,456")
_admins_env = os.environ.get("ADMINS", "8135353129")
ADMINS = [int(x.strip()) for x in _admins_env.split(",") if x.strip().isdigit()]

# Telegram Web App uchun URL (Sizning yangi serveringiz)
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://web-production-5c6b3.up.railway.app/")

# Ma'lumotlar bazasi parametrlari
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "db1")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "sardorproject")
DB_NAME = os.environ.get("DB_NAME", "db1")
