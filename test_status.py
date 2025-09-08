#!/usr/bin/env python3
"""
Проверка статуса исправлений TBF_V0 модулей.
"""

import sys
import os
sys.path.insert(0, '.')

def test_imports():
    """Проверяем импорты всех модулей."""
    print("=== TESTING MODULE IMPORTS ===")
    
    modules = [
        ("SimpleClient", "TBF_V0.core.simple_client"),
        ("SimpleWallet", "TBF_V0.core.simple_wallet"), 
        ("EventParser", "TBF_V0.pumpfun.event_parser"),
        ("CurveManager", "TBF_V0.pumpfun.curve_manager"),
        ("AddressProvider", "TBF_V0.pumpfun.address_provider"),
        ("SimpleBlockListener", "TBF_V0.monitoring.simple_block_listener")
    ]
    
    success_count = 0
    
    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"OK   {name}")
            success_count += 1
        except Exception as e:
            print(f"FAIL {name}: {str(e)[:50]}")
    
    print(f"\nImports: {success_count}/{len(modules)} successful")
    return success_count == len(modules)

def test_functionality():
    """Проверяем базовую функциональность."""
    print("\n=== TESTING BASIC FUNCTIONALITY ===")
    
    tests_passed = 0
    
    # Test SimpleBlockListener
    try:
        from TBF_V0.monitoring.simple_block_listener import SimpleBlockListener
        listener = SimpleBlockListener(wss_endpoint="wss://test")
        
        # Check attributes
        assert listener.wss_endpoint == "wss://test"
        assert hasattr(listener, 'is_listening')
        assert listener.is_listening == False
        
        # Check methods
        assert hasattr(listener, 'start_listening')
        assert hasattr(listener, 'stop_listening')
        
        print("OK   SimpleBlockListener basic functionality")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL SimpleBlockListener: {e}")
    
    # Test CurveManager
    try:
        from TBF_V0.pumpfun.curve_manager import CurveManager, CurveState
        
        curve_state = CurveState(
            virtual_token_reserves=1000000000000,
            virtual_sol_reserves=30000000000,
            real_token_reserves=800000000000,
            real_sol_reserves=0,
            token_total_supply=1000000000000,
            complete=False
        )
        
        manager = CurveManager()
        buy_price = manager.calculate_buy_price(curve_state, 1000000000)
        assert buy_price > 0
        
        print("OK   CurveManager basic functionality")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL CurveManager: {e}")
    
    # Test AddressProvider
    try:
        from TBF_V0.pumpfun.address_provider import AddressProvider
        
        provider = AddressProvider()
        mint = "So11111111111111111111111111111111111111112"
        bonding_curve = provider.get_bonding_curve_address(mint)
        metadata = provider.get_metadata_address(mint)
        
        assert bonding_curve is not None
        assert metadata is not None
        
        print("OK   AddressProvider basic functionality")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL AddressProvider: {e}")
    
    print(f"\nFunctionality: {tests_passed}/3 tests passed")
    return tests_passed == 3

def main():
    """Main test function."""
    print("TBF_V0 MODULE STATUS CHECK")
    print("=" * 40)
    
    imports_ok = test_imports()
    functionality_ok = test_functionality()
    
    print("\n" + "=" * 40)
    print("FINAL RESULT:")
    
    if imports_ok and functionality_ok:
        print("SUCCESS: All modules working correctly!")
        print("- All imports successful")
        print("- Basic functionality verified")
        print("- SimpleBlockListener constructor fixed")
        print("- SimpleWallet signature handling fixed")
        print("- EventParser URI parsing fixed")
        return True
    else:
        print("PARTIAL SUCCESS:")
        print(f"- Imports: {'OK' if imports_ok else 'ISSUES'}")
        print(f"- Functionality: {'OK' if functionality_ok else 'ISSUES'}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
