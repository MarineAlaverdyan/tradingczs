#!/usr/bin/env python3
"""
Скрипт для очистки старых логов.
"""

import os
import glob

def clean_logs():
    """Очищает старые лог файлы"""
    
    print("🧹 ОЧИСТКА СТАРЫХ ЛОГОВ")
    print("=" * 40)
    
    # Удаляем все trading_log_*.log файлы
    trading_logs = glob.glob("trading_log_*.log")
    print(f"📁 Найдено trading логов: {len(trading_logs)}")
    
    for log_file in trading_logs:
        try:
            os.remove(log_file)
            print(f"🗑️  Удален: {log_file}")
        except Exception as e:
            print(f"❌ Ошибка удаления {log_file}: {e}")
    
    # Очищаем логи в папке logs/
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        log_files = [
            "real_buy_performance.log",
            "test_buy_detailed.log", 
            "test_buy_errors.log"
        ]
        
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'w') as f:
                        f.write("")  # Очищаем содержимое
                    print(f"🧽 Очищен: {log_path}")
                except Exception as e:
                    print(f"❌ Ошибка очистки {log_path}: {e}")
    
    print("✅ Очистка завершена!")

if __name__ == "__main__":
    clean_logs()
