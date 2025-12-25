import os
import sys
from pathlib import Path

# Значения по умолчанию для инициализации Settings при импорте приложения
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_BOT_USERNAME", "test_bot")
os.environ.setdefault("WEB_APP_URL", "https://example.com")
os.environ.setdefault("APP_DOMAIN", "example.com")


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
