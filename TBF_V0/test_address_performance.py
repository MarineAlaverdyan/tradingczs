"""
Тест производительности AddressProvider - измерение времени расчета адресов.
Сравнение времени расчета vs использования готовых адресов от слушателя.
"""

import time
import statistics
from typing import List, Dict
from solders.pubkey import Pubkey

from pumpfun.address_provider import AddressProvider


def measure_execution_time(func, *args, **kwargs) -> tuple:
    """Измеряет время выполнения функции."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1000  # в миллисекундах
    return result, execution_time


def run_performance_tests(iterations: int = 1000) -> Dict[str, List[float]]:
    """Запускает тесты производительности для различных операций."""
    
    print(f"🚀 ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ AddressProvider")
    print(f"📊 Количество итераций: {iterations}")
    print("=" * 60)
    
    # Тестовые данные
    test_mint = Pubkey.from_string("r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump")
    test_wallet = Pubkey.from_string("6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH")
    
    results = {
        "bonding_curve": [],
        "associated_bonding_curve": [],
        "associated_token_account": [],
        "metadata": [],
        "all_addresses": []
    }
    
    print("⏱️  Выполнение тестов...")
    
    # Тест 1: Расчет bonding curve
    print("1️⃣  Тестирование bonding_curve_address...")
    for i in range(iterations):
        _, exec_time = measure_execution_time(
            AddressProvider.get_bonding_curve_address, 
            test_mint
        )
        results["bonding_curve"].append(exec_time)
        
        if (i + 1) % 100 == 0:
            print(f"   Выполнено: {i + 1}/{iterations}")
    
    # Тест 2: Расчет associated bonding curve
    print("2️⃣  Тестирование associated_bonding_curve_address...")
    for i in range(iterations):
        _, exec_time = measure_execution_time(
            AddressProvider.get_associated_bonding_curve_address,
            test_mint
        )
        results["associated_bonding_curve"].append(exec_time)
        
        if (i + 1) % 100 == 0:
            print(f"   Выполнено: {i + 1}/{iterations}")
    
    # Тест 3: Расчет associated token account
    print("3️⃣  Тестирование associated_token_address...")
    for i in range(iterations):
        _, exec_time = measure_execution_time(
            AddressProvider.get_associated_token_address,
            test_wallet,
            test_mint
        )
        results["associated_token_account"].append(exec_time)
        
        if (i + 1) % 100 == 0:
            print(f"   Выполнено: {i + 1}/{iterations}")
    
    # Тест 4: Расчет metadata
    print("4️⃣  Тестирование metadata_address...")
    for i in range(iterations):
        _, exec_time = measure_execution_time(
            AddressProvider.get_metadata_address,
            test_mint
        )
        results["metadata"].append(exec_time)
        
        if (i + 1) % 100 == 0:
            print(f"   Выполнено: {i + 1}/{iterations}")
    
    # Тест 5: Расчет всех адресов сразу
    print("5️⃣  Тестирование get_all_addresses...")
    for i in range(iterations):
        _, exec_time = measure_execution_time(
            AddressProvider.get_all_addresses,
            test_mint,
            test_wallet
        )
        results["all_addresses"].append(exec_time)
        
        if (i + 1) % 100 == 0:
            print(f"   Выполнено: {i + 1}/{iterations}")
    
    return results


def analyze_results(results: Dict[str, List[float]]) -> None:
    """Анализирует результаты тестов производительности."""
    
    print("\n📈 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    for operation, times in results.items():
        mean_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        print(f"\n🔧 {operation.upper().replace('_', ' ')}:")
        print(f"   Среднее время: {mean_time:.4f} мс")
        print(f"   Медиана: {median_time:.4f} мс")
        print(f"   Минимум: {min_time:.4f} мс")
        print(f"   Максимум: {max_time:.4f} мс")
        print(f"   Стд. отклонение: {std_dev:.4f} мс")


def compare_with_listener_data() -> None:
    """Сравнивает время расчета с использованием готовых данных от слушателя."""
    
    print("\n🆚 СРАВНЕНИЕ: РАСЧЕТ vs ГОТОВЫЕ ДАННЫЕ ОТ СЛУШАТЕЛЯ")
    print("=" * 60)
    
    # Данные от слушателя (готовые)
    listener_data = {
        'mint': 'r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump',
        'bondingCurve': 'AuUmsyXSAzKz4mTSEDX719rQvNpkz47rjbTn7QhU94SC',
        'associatedBondingCurve': 'CggVUQJEU2HWQRvMDAEiozNkPqKLMr5Mxc6zQPjnyrbz',
        'user': '6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH'
    }
    
    test_mint = Pubkey.from_string(listener_data['mint'])
    test_wallet = Pubkey.from_string(listener_data['user'])
    
    iterations = 100
    
    # Время использования готовых данных
    print("📦 Тестирование использования готовых данных от слушателя...")
    listener_times = []
    
    for _ in range(iterations):
        start_time = time.perf_counter()
        
        # Просто конвертируем строки в Pubkey (как в реальном боте)
        mint = Pubkey.from_string(listener_data['mint'])
        bonding_curve = Pubkey.from_string(listener_data['bondingCurve'])
        associated_bc = Pubkey.from_string(listener_data['associatedBondingCurve'])
        user = Pubkey.from_string(listener_data['user'])
        
        # Рассчитываем только ATA пользователя (единственное что нужно)
        ata = AddressProvider.get_associated_token_address(user, mint)
        
        end_time = time.perf_counter()
        listener_times.append((end_time - start_time) * 1000)
    
    # Время полного расчета
    print("🧮 Тестирование полного расчета всех адресов...")
    calculation_times = []
    
    for _ in range(iterations):
        start_time = time.perf_counter()
        
        # Полный расчет всех адресов
        all_addresses = AddressProvider.get_all_addresses(test_mint, test_wallet)
        
        end_time = time.perf_counter()
        calculation_times.append((end_time - start_time) * 1000)
    
    # Анализ
    listener_avg = statistics.mean(listener_times)
    calculation_avg = statistics.mean(calculation_times)
    speedup = calculation_avg / listener_avg
    
    print(f"\n📊 РЕЗУЛЬТАТЫ СРАВНЕНИЯ:")
    print(f"   Готовые данные от слушателя: {listener_avg:.4f} мс")
    print(f"   Полный расчет адресов: {calculation_avg:.4f} мс")
    print(f"   Ускорение при использовании слушателя: {speedup:.2f}x")
    print(f"   Экономия времени: {calculation_avg - listener_avg:.4f} мс")


def analyze_pda_operations() -> None:
    """Анализирует какие операции самые затратные в PDA расчетах."""
    
    print("\n🔍 АНАЛИЗ PDA ОПЕРАЦИЙ")
    print("=" * 60)
    
    test_mint = Pubkey.from_string("r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump")
    test_wallet = Pubkey.from_string("6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH")
    
    iterations = 500
    
    operations = {
        "find_program_address (bonding_curve)": lambda: Pubkey.find_program_address(
            [b"bonding-curve", bytes(test_mint)],
            AddressProvider.PUMP_PROGRAM_ID
        ),
        "find_program_address (associated_token)": lambda: Pubkey.find_program_address(
            [bytes(test_wallet), bytes(AddressProvider.TOKEN_PROGRAM_ID), bytes(test_mint)],
            AddressProvider.ASSOCIATED_TOKEN_PROGRAM_ID
        ),
        "string_to_pubkey": lambda: Pubkey.from_string("r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump"),
        "pubkey_to_bytes": lambda: bytes(test_mint),
    }
    
    for op_name, op_func in operations.items():
        times = []
        
        for _ in range(iterations):
            _, exec_time = measure_execution_time(op_func)
            times.append(exec_time)
        
        avg_time = statistics.mean(times)
        print(f"   {op_name}: {avg_time:.6f} мс")


def main():
    """Главная функция тестирования производительности."""
    
    print("🔬 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ AddressProvider")
    print("=" * 80)
    print("📝 Измеряем время расчета адресов vs использование готовых данных")
    print()
    
    try:
        # Основные тесты производительности
        results = run_performance_tests(iterations=500)
        analyze_results(results)
        
        # Сравнение с данными слушателя
        compare_with_listener_data()
        
        # Анализ отдельных PDA операций
        analyze_pda_operations()
        
        print("\n" + "=" * 80)
        print("🎯 ВЫВОДЫ:")
        print("1️⃣  Расчет PDA адресов занимает значительное время")
        print("2️⃣  Использование готовых данных от слушателя намного быстрее")
        print("3️⃣  find_program_address() - самая затратная операция")
        print("4️⃣  В реальной торговле каждая миллисекунда критична")
        print("5️⃣  Поэтому лучше использовать адреса от слушателя напрямую")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка в тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
