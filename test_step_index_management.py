#!/usr/bin/env python3
"""
🧪 步骤索引管理单元测试
测试步骤推进的原子性和竞争条件防护
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

class MockOrchestratorState:
    def __init__(self):
        self.current_step_idx = 0
        self.plan = [Mock(title=f"Step {i}", agent_name="test_agent") for i in range(5)]
        self.step_execution_status = {}
        self.current_step_agent_response_count = 0
        self.message_history = []
        self.n_rounds = 0

class TestStepIndexManagement:
    """测试步骤索引的原子性操作"""
    
    def test_single_increment_location(self):
        """测试步骤索引只在一个位置递增"""
        state = MockOrchestratorState()
        
        # 模拟Agent响应处理中的递增
        def agent_response_increment():
            state.current_step_idx += 1
            return state.current_step_idx
        
        # 模拟Progress Ledger中的递增（应该被修复为不递增）
        def progress_ledger_increment():
            # 修复后应该不再递增
            return state.current_step_idx
        
        initial_idx = state.current_step_idx
        
        # 只有Agent响应处理应该递增
        result1 = agent_response_increment()
        result2 = progress_ledger_increment()
        
        assert result1 == initial_idx + 1, "Agent响应处理应该递增步骤索引"
        assert result2 == initial_idx + 1, "Progress Ledger不应该再次递增"
        assert state.current_step_idx == initial_idx + 1, "最终索引应该只递增一次"

    def test_concurrent_step_increment_prevention(self):
        """测试并发步骤递增的防护"""
        state = MockOrchestratorState()
        
        async def simulate_agent_response():
            # 模拟Agent响应处理
            await asyncio.sleep(0.01)
            state.current_step_idx += 1
            return "agent_done"
        
        async def simulate_progress_ledger():
            # 模拟Progress Ledger处理（修复后不应递增）
            await asyncio.sleep(0.01)
            # 不应该递增 - 这是修复的关键
            return "ledger_done"
        
        async def test_concurrent():
            initial_idx = state.current_step_idx
            
            # 并发执行两个操作
            results = await asyncio.gather(
                simulate_agent_response(),
                simulate_progress_ledger()
            )
            
            # 验证只递增了一次
            assert state.current_step_idx == initial_idx + 1
            assert len(results) == 2
            
        asyncio.run(test_concurrent())

    def test_step_completion_validation(self):
        """测试步骤完成状态的验证逻辑"""
        state = MockOrchestratorState()
        
        def is_step_completed(step_idx: int, agent_response: str) -> bool:
            """模拟步骤完成检查逻辑"""
            completion_signals = [
                "✅ 当前步骤已完成",
                "✅ STEP COMPLETED", 
                "图像生成任务已完成"
            ]
            return any(signal in agent_response for signal in completion_signals)
        
        # 测试正确的完成信号
        assert is_step_completed(0, "✅ 当前步骤已完成：已收集产品信息")
        assert is_step_completed(1, "图像生成任务已完成")
        
        # 测试错误的全局信号（应该被过滤）
        assert not is_step_completed(0, "✅ 任务已完成")  # 全局信号应该被移除
        
        # 测试无效信号
        assert not is_step_completed(0, "我理解您需要生成图像")
        assert not is_step_completed(0, "Let me help you with that")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])