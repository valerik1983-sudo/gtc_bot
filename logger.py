import logging
from datetime import datetime

# Настройка логирования
def setup_logger():
    # Имя файла с датой (например, bot_2024-01-15.log)
    filename = f"logs/bot_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Создаём папку logs, если её нет
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Настройка
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(filename, encoding='utf-8'),
            logging.StreamHandler()  # чтобы ещё и в консоль выводило
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logger()