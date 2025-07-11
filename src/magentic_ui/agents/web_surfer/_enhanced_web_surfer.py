"""
增强的WebSurfer Agent - 改进循环检测和错误处理
"""

import asyncio
from typing import Dict, List, Optional, Any
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ._web_surfer import WebSurferAgent
from .._enhanced_workflow_coordinator import EnhancedWorkflowCoordinator

@dataclass
class ActionRecord:
    """操作记录"""
    timestamp: datetime
    action_type: str
    action_details: str
    result: Optional[str] = None
    error: Optional[str] = None

@dataclass
class LoopDetectionState:
    """循环检测状态"""
    action_history: List[ActionRecord] = field(default_factory=list)
    consecutive_errors: int = 0
    last_success_time: Optional[datetime] = None
    current_operation_start: Optional[datetime] = None
    page_visit_count: Dict[str, int] = field(default_factory=dict)
    element_interaction_count: Dict[str, int] = field(default_factory=dict)

class EnhancedWebSurferAgent(WebSurferAgent):
    """增强的WebSurfer Agent"""
    
    def __init__(self, *args, **kwargs):
        # 获取workflow_coordinator参数
        self.workflow_coordinator: Optional[EnhancedWorkflowCoordinator] = kwargs.pop('workflow_coordinator', None)
        
        super().__init__(*args, **kwargs)
        
        # 增强的循环检测状态
        self.loop_detection = LoopDetectionState()
        
        # 配置参数
        self.config = {
            'max_page_visits': 5,  # 单个页面最大访问次数
            'max_element_interactions': 3,  # 单个元素最大交互次数
            'max_consecutive_errors': 3,  # 最大连续错误次数
            'operation_timeout': 300,  # 操作超时时间（秒）
            'success_threshold': 60,  # 成功阈值时间（秒）
            'adaptive_threshold': True,  # 自适应阈值
            'context_aware_detection': True  # 上下文感知检测
        }
    
    def _record_action(self, action_type: str, action_details: str, result: Optional[str] = None, error: Optional[str] = None) -> None:
        """记录操作"""
        record = ActionRecord(
            timestamp=datetime.now(),
            action_type=action_type,
            action_details=action_details,
            result=result,
            error=error
        )
        self.loop_detection.action_history.append(record)
        
        # 保持历史记录在合理范围内
        if len(self.loop_detection.action_history) > 50:
            self.loop_detection.action_history = self.loop_detection.action_history[-30:]
        
        # 更新错误计数
        if error:
            self.loop_detection.consecutive_errors += 1
        else:
            self.loop_detection.consecutive_errors = 0
            self.loop_detection.last_success_time = datetime.now()
    
    def _is_task_context_appropriate(self) -> bool:
        """判断任务上下文是否适合继续"""
        if not self.workflow_coordinator:
            return True
        
        current_step = self.workflow_coordinator.get_current_step()
        if not current_step:
            return False
        
        # 检查步骤是否适合WebSurfer继续操作
        step_title = current_step.plan_step.title.lower()
        step_details = current_step.plan_step.details.lower()
        
        # 如果步骤明确表示需要找到特定信息，允许更多尝试
        exploration_keywords = ['查找', '浏览', '搜索', '探索', '寻找', 'find', 'search', 'explore', 'browse']
        is_exploration_task = any(keyword in step_title or keyword in step_details for keyword in exploration_keywords)
        
        return is_exploration_task
    
    def _detect_productive_loop(self) -> bool:
        """检测是否为有效循环（例如，在正确的页面上进行有意义的探索）"""
        if len(self.loop_detection.action_history) < 3:
            return False
        
        recent_actions = self.loop_detection.action_history[-5:]
        
        # 检查是否在产品页面和详情页面之间有意义地导航
        navigation_actions = [a for a in recent_actions if a.action_type in ['click', 'visit']]
        
        # 如果最近的操作都是导航相关的，并且没有明显的错误
        if len(navigation_actions) >= 2:
            error_count = sum(1 for a in navigation_actions if a.error)
            success_count = len(navigation_actions) - error_count
            
            # 如果成功率足够高，认为是有效的探索
            if success_count >= error_count:
                return True
        
        return False
    
    def _should_terminate_due_to_loop(self) -> bool:
        """判断是否应该因循环而终止"""
        current_time = datetime.now()
        
        # 检查连续错误
        if self.loop_detection.consecutive_errors >= self.config['max_consecutive_errors']:
            logger.warning(f"🔴 连续错误过多: {self.loop_detection.consecutive_errors}")
            return True
        
        # 检查操作超时
        if (self.loop_detection.current_operation_start and 
            current_time - self.loop_detection.current_operation_start > timedelta(seconds=self.config['operation_timeout'])):
            logger.warning(f"⏰ 操作超时")
            return True
        
        # 检查页面访问次数
        for url, count in self.loop_detection.page_visit_count.items():
            if count > self.config['max_page_visits']:
                logger.warning(f"🔄 页面访问次数过多: {url} ({count})")
                return True
        
        # 检查是否为有效循环
        if self._detect_productive_loop():
            logger.info("✅ 检测到有效探索循环，继续执行")
            return False
        
        # 检查任务上下文
        if self.config['context_aware_detection'] and self._is_task_context_appropriate():
            logger.info("📋 任务上下文适合继续，放宽循环检测")
            return False
        
        # 原有的循环检测逻辑
        if len(self.loop_detection.action_history) >= 8:
            recent_actions = self.loop_detection.action_history[-6:]
            
            # 检查重复操作模式
            action_signatures = [f"{a.action_type}:{a.action_details}" for a in recent_actions]
            
            # 计算重复度
            unique_actions = set(action_signatures)
            if len(unique_actions) <= 2:  # 只有1-2种不同的操作
                logger.warning(f"🔄 检测到重复操作模式: {unique_actions}")
                return True
        
        return False
    
    def _generate_context_aware_completion(self) -> str:
        """生成上下文感知的完成消息"""
        if not self.workflow_coordinator:
            return "✅ 当前步骤已完成"
        
        current_step = self.workflow_coordinator.get_current_step()
        if not current_step:
            return "✅ 当前步骤已完成"
        
        # 生成包含收集信息的完成消息
        recent_successful_actions = [
            a for a in self.loop_detection.action_history[-10:] 
            if a.result and not a.error
        ]
        
        if recent_successful_actions:
            completion_msg = f"✅ 当前步骤已完成 - {current_step.plan_step.title}\n"
            completion_msg += f"📊 成功执行了 {len(recent_successful_actions)} 个操作\n"
            completion_msg += "🔍 已收集到相关信息，可以继续下一步骤"
        else:
            completion_msg = f"✅ 当前步骤已完成 - {current_step.plan_step.title}"
        
        return completion_msg
    
    async def _enhanced_loop_detection(self, tool_call_name: str, tool_call_msg: str) -> bool:
        """增强的循环检测"""
        # 记录当前操作
        self._record_action(tool_call_name, tool_call_msg)
        
        # 更新页面访问计数
        if tool_call_name == 'visit_page':
            url = tool_call_msg
            self.loop_detection.page_visit_count[url] = self.loop_detection.page_visit_count.get(url, 0) + 1
        
        # 更新元素交互计数
        if tool_call_name in ['click', 'type', 'select']:
            element_key = f"{tool_call_name}:{tool_call_msg}"
            self.loop_detection.element_interaction_count[element_key] = self.loop_detection.element_interaction_count.get(element_key, 0) + 1
        
        # 设置操作开始时间
        if not self.loop_detection.current_operation_start:
            self.loop_detection.current_operation_start = datetime.now()
        
        # 检查是否应该终止
        should_terminate = self._should_terminate_due_to_loop()
        
        if should_terminate:
            logger.info("🎯 增强循环检测: 建议完成当前步骤")
            # 生成上下文感知的完成消息
            completion_msg = self._generate_context_aware_completion()
            
            # 如果有workflow_coordinator，记录完成状态
            if self.workflow_coordinator:
                current_step = self.workflow_coordinator.get_current_step()
                if current_step:
                    self.workflow_coordinator.complete_step(
                        result=completion_msg,
                        materials=[]
                    )
        
        return should_terminate
    
    # 重写原有的循环检测方法
    def _detect_loop_before_action(self, tool_call_name: str, tool_call_msg: str) -> bool:
        """重写的循环检测方法"""
        return asyncio.run(self._enhanced_loop_detection(tool_call_name, tool_call_msg))
    
    def reset_loop_detection(self) -> None:
        """重置循环检测状态"""
        self.loop_detection = LoopDetectionState()
        logger.info("🔄 循环检测状态已重置")
    
    def get_operation_summary(self) -> str:
        """获取操作总结"""
        if not self.loop_detection.action_history:
            return "暂无操作记录"
        
        total_actions = len(self.loop_detection.action_history)
        successful_actions = sum(1 for a in self.loop_detection.action_history if a.result and not a.error)
        error_actions = sum(1 for a in self.loop_detection.action_history if a.error)
        
        summary = f"📊 操作总结:\n"
        summary += f"  总操作数: {total_actions}\n"
        summary += f"  成功操作: {successful_actions}\n"
        summary += f"  错误操作: {error_actions}\n"
        summary += f"  成功率: {successful_actions/total_actions*100:.1f}%\n"
        
        if self.loop_detection.last_success_time:
            time_since_success = datetime.now() - self.loop_detection.last_success_time
            summary += f"  上次成功: {time_since_success.total_seconds():.1f}秒前"
        
        return summary