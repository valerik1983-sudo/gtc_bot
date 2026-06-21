# run_bots.py
import subprocess
import sys
import time
import os
import multiprocessing
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def run_bot_with_restart(script_name, bot_name):
    """Запускает бота и перезапускает его при падении"""
    while True:
        try:
            print(f"🚀 Запуск {bot_name}...")
            # Передаём переменные окружения в дочерний процесс
            env = os.environ.copy()
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=False,
                env=env
            )
            
            if result.returncode != 0:
                print(f"❌ {bot_name} завершился с ошибкой (код: {result.returncode})")
            else:
                print(f"✅ {bot_name} завершился нормально")
                
        except KeyboardInterrupt:
            print(f"👋 {bot_name} остановлен пользователем")
            raise
            
        except Exception as e:
            print(f"❌ Ошибка в {bot_name}: {e}")
        
        print(f"🔄 Перезапуск {bot_name} через 5 секунд...")
        time.sleep(5)


def run_main_bot():
    run_bot_with_restart("main.py", "основного бота")


def run_consult_bot():
    run_bot_with_restart("consult_bot.py", "консультационного бота")


if __name__ == "__main__":
    print("🔄 Запуск ботов с автоматическим перезапуском...")
    print("📌 Для остановки нажмите Ctrl+C\n")
    
    main_process = multiprocessing.Process(target=run_main_bot)
    consult_process = multiprocessing.Process(target=run_consult_bot)
    
    main_process.start()
    consult_process.start()
    
    try:
        main_process.join()
        consult_process.join()
    except KeyboardInterrupt:
        print("\n👋 Останавливаем ботов...")
        main_process.terminate()
        consult_process.terminate()
        main_process.join()
        consult_process.join()
        print("✅ Боты остановлены")