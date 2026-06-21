# start_bots.py
import subprocess
import sys
import time
import os

def start_bots():
    """Запуск обоих ботов"""
    
    # Запускаем основного бота
    main_bot = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("✅ Основной бот запущен (PID: {})".format(main_bot.pid))
    
    time.sleep(2)  # Пауза между запусками
    
    # Запускаем консультационного бота
    consult_bot = subprocess.Popen(
        [sys.executable, "consult_bot.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("✅ Консультационный бот запущен (PID: {})".format(consult_bot.pid))
    
    print("\n📌 Для остановки нажмите Ctrl+C\n")
    
    try:
        # Ждем завершения
        main_bot.wait()
        consult_bot.wait()
    except KeyboardInterrupt:
        print("\n👋 Останавливаем ботов...")
        main_bot.terminate()
        consult_bot.terminate()
        main_bot.wait()
        consult_bot.wait()
        print("✅ Боты остановлены")

if __name__ == "__main__":
    start_bots()