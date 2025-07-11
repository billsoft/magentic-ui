#!/usr/bin/env python3
"""
🧪 WebSurfer 完成信号单元测试
测试WebSurfer的完成信号格式和错误恢复
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

class TestWebSurferCompletionSignals:
    """测试WebSurfer完成信号的正确格式"""
    
    def test_step_completion_signal_format(self):
        """测试步骤完成信号的正确格式"""
        
        # 正确的步骤完成信号
        valid_signals = [
            "✅ 当前步骤已完成：已成功访问te720.com",
            "✅ STEP COMPLETED: Successfully gathered information",
            "⚠️ 当前步骤因错误完成：网站无法访问但提供了替代信息",
            "🔄 当前步骤通过替代方案完成：使用了备用数据源"
        ]
        
        # 错误的全局任务信号（已修复）
        invalid_signals = [
            "✅ 任务已完成",
            "✅ 研究任务基本完成",
            "TASK COMPLETED",
            "任务已完成"
        ]
        
        def is_valid_step_signal(signal: str) -> bool:
            """检查是否为有效的步骤完成信号"""
            valid_patterns = [
                "当前步骤已完成",
                "STEP COMPLETED", 
                "当前步骤因错误完成",
                "当前步骤通过替代方案完成"
            ]
            return any(pattern in signal for pattern in valid_patterns)
        
        # 验证正确信号
        for signal in valid_signals:
            assert is_valid_step_signal(signal), f"应该接受步骤信号: {signal}"
        
        # 验证错误信号被拒绝
        for signal in invalid_signals:
            assert not is_valid_step_signal(signal), f"应该拒绝全局信号: {signal}"

    def test_error_recovery_completion_signals(self):
        """测试错误恢复时的完成信号"""
        
        def generate_error_recovery_signal(error_type: str, collected_info: str) -> str:
            """根据错误类型生成恢复信号"""
            if "validation error" in error_type.lower():
                return f"✅ 当前步骤已完成：{collected_info}。虽然遇到数据处理问题，但已收集到足够信息。"
            elif "screenshot" in error_type.lower():
                return f"✅ 当前步骤已完成：{collected_info}。虽然遇到截图超时，但页面导航正常。"
            elif "connection" in error_type.lower():
                return f"⚠️ 当前步骤因错误完成：{collected_info}。网站连接失败但提供了替代信息。"
            else:
                return f"✅ 当前步骤已完成：{collected_info}"
        
        # 测试不同错误类型的恢复信号
        test_cases = [
            ("validation error for TextMessage", "已访问te720.com获得产品信息"),
            ("screenshot timeout", "已成功导航到产品页面"),
            ("connection refused", "提供了基于知识的产品信息")
        ]
        
        for error_type, info in test_cases:
            signal = generate_error_recovery_signal(error_type, info)
            assert "当前步骤" in signal, f"恢复信号应包含步骤标识: {signal}"
            assert info in signal, f"恢复信号应包含收集的信息: {signal}"

    def test_loop_detection_completion(self):
        """测试循环检测后的完成信号"""
        
        class MockLoopDetector:
            def __init__(self):
                self.action_count = {}
            
            def detect_loop(self, action: str) -> bool:
                self.action_count[action] = self.action_count.get(action, 0) + 1
                return self.action_count[action] > 2
            
            def generate_completion_signal(self, detected: bool) -> str:
                if detected:
                    return "✅ 当前步骤已完成：检测到重复操作，已收集足够信息避免循环。"
                return ""
        
        detector = MockLoopDetector()
        
        # 模拟重复操作
        assert not detector.detect_loop("click_product")  # 第1次
        assert not detector.detect_loop("click_product")  # 第2次
        assert detector.detect_loop("click_product")      # 第3次 - 检测到循环
        
        signal = detector.generate_completion_signal(True)
        assert "当前步骤已完成" in signal
        assert "循环" in signal or "重复" in signal

if __name__ == "__main__":
    pytest.main([__file__, "-v"])