#!/usr/bin/env python3
"""
🧪 Magentic-UI 多步骤执行系统测试套件运行器
分层执行所有单元测试和集成测试
"""

import subprocess
import sys
import time
from typing import List, Dict, Any
from pathlib import Path

class TestSuiteRunner:
    """测试套件运行器"""
    
    def __init__(self):
        self.test_files = [
            "test_step_index_management.py",
            "test_websurfer_completion_signals.py", 
            "test_orchestrator_signal_recognition.py",
            "test_agent_collaboration.py",
            "test_instruction_generation.py",
            "test_task_interruption_management.py",
            "test_complete_system_integration.py"
        ]
        self.results = {}
        self.execution_times = {}
    
    def run_single_test(self, test_file: str) -> Dict[str, Any]:
        """运行单个测试文件"""
        print(f"\n🧪 Running {test_file}...")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60  # 60秒超时
            )
            
            execution_time = time.time() - start_time
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Test execution timeout (60s)',
                'execution_time': 60.0,
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Test execution error: {str(e)}',
                'execution_time': time.time() - start_time,
                'return_code': -2
            }
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 Starting Magentic-UI Multi-Step Execution Test Suite")
        print("=" * 60)
        
        total_start_time = time.time()
        all_passed = True
        
        for test_file in self.test_files:
            # 检查测试文件是否存在
            if not Path(test_file).exists():
                print(f"❌ Test file not found: {test_file}")
                all_passed = False
                continue
            
            # 运行测试
            result = self.run_single_test(test_file)
            self.results[test_file] = result
            self.execution_times[test_file] = result['execution_time']
            
            # 显示结果
            if result['success']:
                print(f"✅ {test_file} PASSED ({result['execution_time']:.2f}s)")
            else:
                print(f"❌ {test_file} FAILED ({result['execution_time']:.2f}s)")
                print(f"   Error: {result['stderr'][:200]}...")
                all_passed = False
        
        # 总结报告
        total_time = time.time() - total_start_time
        self.print_summary_report(total_time, all_passed)
        
        return all_passed
    
    def print_summary_report(self, total_time: float, all_passed: bool):
        """打印总结报告"""
        print("\n" + "=" * 60)
        print("📊 TEST SUITE SUMMARY REPORT")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.results.values() if result['success'])
        total_tests = len(self.results)
        
        print(f"📈 Overall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
        print(f"⏱️  Total Execution Time: {total_time:.2f}s")
        print(f"⚡ Average Test Time: {total_time/max(total_tests, 1):.2f}s")
        
        print("\n📋 Detailed Results:")
        for test_file, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} {test_file:<40} ({result['execution_time']:.2f}s)")
        
        if not all_passed:
            print("\n🔍 Failed Test Details:")
            for test_file, result in self.results.items():
                if not result['success']:
                    print(f"\n❌ {test_file}:")
                    print(f"   Return Code: {result['return_code']}")
                    if result['stderr']:
                        print(f"   Error: {result['stderr'][:300]}...")
        
        print("\n" + "=" * 60)

def check_dependencies():
    """检查测试依赖"""
    print("🔍 Checking test dependencies...")
    
    required_packages = ['pytest', 'asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install pytest pytest-asyncio")
        return False
    
    return True

def main():
    """主函数"""
    print("🧪 Magentic-UI Multi-Step Execution System Test Suite")
    print("Testing the fixes for step progression, signal handling, and error recovery")
    print()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 运行测试套件
    runner = TestSuiteRunner()
    success = runner.run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()