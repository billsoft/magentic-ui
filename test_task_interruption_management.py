#!/usr/bin/env python3
"""
🧪 任务中断和管理测试
测试任务中断、恢复、错误处理和资源管理
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    RECOVERING = "recovering"

class MockTask:
    def __init__(self, task_id: str, steps: List[str]):
        self.task_id = task_id
        self.steps = steps
        self.current_step = 0
        self.status = TaskStatus.PENDING
        self.error_count = 0
        self.interruption_reason = None
        self.recovery_attempts = 0

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.active_task = None
        self.interruption_handlers = {}
        self.max_recovery_attempts = 3
    
    def register_interruption_handler(self, error_type: str, handler):
        """注册中断处理器"""
        self.interruption_handlers[error_type] = handler
    
    async def handle_interruption(self, task: MockTask, error: Exception) -> bool:
        """处理任务中断"""
        error_type = type(error).__name__
        task.status = TaskStatus.INTERRUPTED
        task.interruption_reason = str(error)
        
        if error_type in self.interruption_handlers:
            handler = self.interruption_handlers[error_type]
            return await handler(task, error)
        
        return False  # 无法处理的中断
    
    async def attempt_recovery(self, task: MockTask) -> bool:
        """尝试任务恢复"""
        if task.recovery_attempts >= self.max_recovery_attempts:
            task.status = TaskStatus.FAILED
            return False
        
        task.recovery_attempts += 1
        task.status = TaskStatus.RECOVERING
        
        # 模拟恢复逻辑
        await asyncio.sleep(0.1)
        
        # 70% 恢复成功率
        success = task.recovery_attempts <= 2
        if success:
            task.status = TaskStatus.RUNNING
            task.interruption_reason = None
        
        return success

class TestTaskInterruptionManagement:
    """测试任务中断和管理机制"""
    
    @pytest.mark.asyncio
    async def test_websurfer_validation_error_recovery(self):
        """测试WebSurfer验证错误的恢复机制"""
        
        async def websurfer_validation_error_handler(task: MockTask, error: Exception) -> bool:
            """WebSurfer验证错误处理器"""
            error_str = str(error).lower()
            if "validation error" in error_str or "textmessage" in error_str:
                # 发送恢复完成信号
                recovery_message = "✅ 当前步骤已完成：已成功访问te720.com并获得搜索结果，虽然遇到数据处理问题但已收集足够信息。"
                task.recovery_data = recovery_message
                return True
            return False
        
        manager = TaskManager()
        manager.register_interruption_handler("Exception", websurfer_validation_error_handler)
        
        # 创建任务
        task = MockTask("websurfer_task", ["visit_te720", "extract_info"])
        task.status = TaskStatus.RUNNING
        
        # 模拟验证错误
        validation_error = Exception("validation error for TextMessage: Input should be a valid string")
        
        # 处理中断
        can_recover = await manager.handle_interruption(task, validation_error)
        
        assert can_recover, "验证错误应该可以恢复"
        assert task.status == TaskStatus.INTERRUPTED
        assert hasattr(task, 'recovery_data'), "应该生成恢复数据"
        assert "当前步骤已完成" in task.recovery_data

    @pytest.mark.asyncio
    async def test_step_progression_interruption_recovery(self):
        """测试步骤推进中断的恢复"""
        
        class StepProgressionManager:
            def __init__(self):
                self.current_step = 0
                self.step_lock = asyncio.Lock()
                self.step_history = []
            
            async def safe_advance_step(self, step_increment: int = 1) -> bool:
                """安全的步骤推进（防止竞争条件）"""
                async with self.step_lock:
                    old_step = self.current_step
                    self.current_step += step_increment
                    self.step_history.append({
                        'from': old_step,
                        'to': self.current_step,
                        'timestamp': len(self.step_history)
                    })
                    return True
            
            async def rollback_step(self) -> bool:
                """回滚到上一步"""
                async with self.step_lock:
                    if self.step_history:
                        last_change = self.step_history.pop()
                        self.current_step = last_change['from']
                        return True
                    return False
            
            def detect_step_inconsistency(self) -> bool:
                """检测步骤不一致"""
                # 检查是否有重复或跳跃的步骤变化
                if len(self.step_history) < 2:
                    return False
                
                last_two = self.step_history[-2:]
                # 检测是否有同时的步骤变化
                return last_two[0]['timestamp'] == last_two[1]['timestamp']
        
        manager = StepProgressionManager()
        
        # 测试正常步骤推进
        success1 = await manager.safe_advance_step()
        assert success1 and manager.current_step == 1
        
        success2 = await manager.safe_advance_step()
        assert success2 and manager.current_step == 2
        
        # 测试并发步骤推进（应该被锁保护）
        async def concurrent_advance():
            results = await asyncio.gather(
                manager.safe_advance_step(),
                manager.safe_advance_step(),
                return_exceptions=True
            )
            return results
        
        results = await concurrent_advance()
        
        # 即使并发执行，最终步骤应该是一致的
        assert manager.current_step == 4  # 2 + 2次推进
        assert len(manager.step_history) == 4
        
        # 测试回滚机制
        rollback_success = await manager.rollback_step()
        assert rollback_success and manager.current_step == 3

    @pytest.mark.asyncio
    async def test_agent_response_timeout_handling(self):
        """测试Agent响应超时处理"""
        
        class AgentTimeoutManager:
            def __init__(self, timeout_seconds: float = 2.0):
                self.timeout_seconds = timeout_seconds
                self.active_requests = {}
            
            async def execute_with_timeout(self, agent_name: str, instruction: str) -> tuple[bool, str]:
                """带超时的Agent执行"""
                request_id = f"{agent_name}_{len(self.active_requests)}"
                
                async def mock_agent_execution():
                    # 模拟不同的执行时间
                    if "timeout_test" in instruction:
                        await asyncio.sleep(3.0)  # 超时
                    else:
                        await asyncio.sleep(0.5)  # 正常
                    return f"✅ {agent_name} completed: {instruction[:30]}"
                
                try:
                    self.active_requests[request_id] = True
                    result = await asyncio.wait_for(
                        mock_agent_execution(), 
                        timeout=self.timeout_seconds
                    )
                    return True, result
                    
                except asyncio.TimeoutError:
                    # 生成超时恢复信号
                    recovery_signal = f"⚠️ 当前步骤因超时完成：{agent_name}响应超时，但基于已有信息继续执行"
                    return False, recovery_signal
                    
                finally:
                    self.active_requests.pop(request_id, None)
        
        timeout_manager = AgentTimeoutManager(timeout_seconds=1.0)
        
        # 测试正常执行
        success, response = await timeout_manager.execute_with_timeout("web_surfer", "visit website")
        assert success, "正常指令应该成功执行"
        assert "completed" in response
        
        # 测试超时处理
        success, response = await timeout_manager.execute_with_timeout("web_surfer", "timeout_test instruction")
        assert not success, "超时指令应该失败"
        assert "超时完成" in response
        assert "当前步骤因超时完成" in response

    def test_resource_cleanup_on_interruption(self):
        """测试中断时的资源清理"""
        
        class ResourceManager:
            def __init__(self):
                self.allocated_resources = {}
                self.cleanup_handlers = []
            
            def allocate_resource(self, resource_type: str, resource_id: str):
                """分配资源"""
                if resource_type not in self.allocated_resources:
                    self.allocated_resources[resource_type] = []
                self.allocated_resources[resource_type].append(resource_id)
            
            def register_cleanup_handler(self, handler):
                """注册清理处理器"""
                self.cleanup_handlers.append(handler)
            
            def cleanup_resources(self, reason: str = "interruption"):
                """清理所有资源"""
                cleanup_results = []
                
                for handler in self.cleanup_handlers:
                    try:
                        result = handler(self.allocated_resources, reason)
                        cleanup_results.append(result)
                    except Exception as e:
                        cleanup_results.append(f"Cleanup error: {e}")
                
                # 清空资源记录
                self.allocated_resources.clear()
                return cleanup_results
        
        def browser_cleanup_handler(resources: Dict, reason: str) -> str:
            """浏览器资源清理"""
            browsers = resources.get('browser', [])
            for browser_id in browsers:
                # 模拟关闭浏览器
                pass
            return f"Cleaned {len(browsers)} browser instances for {reason}"
        
        def file_cleanup_handler(resources: Dict, reason: str) -> str:
            """文件资源清理"""
            files = resources.get('temp_files', [])
            for file_id in files:
                # 模拟删除临时文件
                pass
            return f"Cleaned {len(files)} temporary files for {reason}"
        
        # 测试资源管理
        resource_mgr = ResourceManager()
        resource_mgr.register_cleanup_handler(browser_cleanup_handler)
        resource_mgr.register_cleanup_handler(file_cleanup_handler)
        
        # 分配资源
        resource_mgr.allocate_resource('browser', 'browser_1')
        resource_mgr.allocate_resource('browser', 'browser_2')
        resource_mgr.allocate_resource('temp_files', 'temp_1.png')
        resource_mgr.allocate_resource('temp_files', 'temp_2.html')
        
        # 验证资源分配
        assert len(resource_mgr.allocated_resources['browser']) == 2
        assert len(resource_mgr.allocated_resources['temp_files']) == 2
        
        # 执行清理
        cleanup_results = resource_mgr.cleanup_resources("task_interruption")
        
        # 验证清理结果
        assert len(cleanup_results) == 2
        assert "Cleaned 2 browser instances" in cleanup_results[0]
        assert "Cleaned 2 temporary files" in cleanup_results[1]
        assert len(resource_mgr.allocated_resources) == 0

    @pytest.mark.asyncio
    async def test_task_recovery_state_persistence(self):
        """测试任务恢复状态的持久化"""
        
        class TaskStatePersistence:
            def __init__(self):
                self.saved_states = {}
            
            def save_task_state(self, task_id: str, state: Dict[str, Any]):
                """保存任务状态"""
                self.saved_states[task_id] = {
                    'state': state.copy(),
                    'timestamp': len(self.saved_states),
                    'version': state.get('version', 1)
                }
            
            def load_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
                """加载任务状态"""
                if task_id in self.saved_states:
                    return self.saved_states[task_id]['state']
                return None
            
            def can_resume_task(self, task_id: str) -> bool:
                """检查任务是否可以恢复"""
                state = self.load_task_state(task_id)
                if not state:
                    return False
                
                # 检查状态完整性
                required_fields = ['current_step', 'plan', 'context']
                return all(field in state for field in required_fields)
        
        persistence = TaskStatePersistence()
        
        # 保存任务状态
        task_state = {
            'task_id': 'test_task_123',
            'current_step': 2,
            'plan': ['step1', 'step2', 'step3', 'step4'],
            'context': {
                'research_completed': True,
                'image_generated': False
            },
            'version': 1
        }
        
        persistence.save_task_state('test_task_123', task_state)
        
        # 验证状态保存
        assert 'test_task_123' in persistence.saved_states
        
        # 测试状态加载
        loaded_state = persistence.load_task_state('test_task_123')
        assert loaded_state is not None
        assert loaded_state['current_step'] == 2
        assert loaded_state['context']['research_completed'] == True
        
        # 测试恢复可行性检查
        can_resume = persistence.can_resume_task('test_task_123')
        assert can_resume, "完整的任务状态应该可以恢复"
        
        # 测试不完整状态
        incomplete_state = {'current_step': 1}  # 缺少必要字段
        persistence.save_task_state('incomplete_task', incomplete_state)
        
        can_resume_incomplete = persistence.can_resume_task('incomplete_task')
        assert not can_resume_incomplete, "不完整的任务状态不应该可以恢复"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])