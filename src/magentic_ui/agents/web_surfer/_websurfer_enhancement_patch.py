"""
🔧 WebSurfer增强补丁 - 为现有WebSurfer添加循环防护功能

使用方法：
1. 在WebSurfer初始化时创建EnhancedLoopPrevention实例
2. 在每次操作前调用循环检测
3. 在生成提示词时集成增强信息
4. 在操作后更新追踪记录
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

from ._enhanced_loop_prevention import EnhancedLoopPrevention, LoopDetectionResult
from ._enhanced_prompts import (
    generate_enhanced_web_surfer_prompt,
    generate_loop_prevention_context,
    generate_smart_action_recommendation
)


class WebSurferEnhancementPatch:
    """
    🔧 WebSurfer增强补丁类
    
    为现有的WebSurfer添加循环防护和智能规划功能，
    无需修改原始WebSurfer代码
    """
    
    def __init__(self):
        self.loop_prevention = EnhancedLoopPrevention()
        self.is_enabled = True
        self.current_task_context = ""
        
        logger.info("🔧 WebSurfer增强补丁已激活")
    
    def initialize_task(self, task_description: str) -> None:
        """初始化任务"""
        self.current_task_context = task_description
        
        # 从任务描述中提取关键词
        keywords = self._extract_keywords_from_task(task_description)
        
        # 设置导航计划
        self.loop_prevention.set_navigation_plan(task_description, keywords)
        
        logger.info(f"🎯 初始化任务: {task_description}")
    
    def check_before_action(
        self, 
        proposed_action: str, 
        proposed_target: str, 
        current_url: str,
        page_content: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        在执行操作前检查是否应该阻止
        
        Returns:
            (should_proceed, reason, enhancement_data)
        """
        if not self.is_enabled:
            return True, "", {}
        
        # 执行循环检测
        loop_result = self.loop_prevention.check_for_loops(
            proposed_action, proposed_target, current_url
        )
        
        # 检查强制完成条件
        force_complete, force_reason = self.loop_prevention.should_force_complete()
        
        # 准备增强数据
        enhancement_data = {
            'loop_detection_result': loop_result,
            'navigation_plan': self.loop_prevention.current_plan,
            'action_history_summary': self.loop_prevention.get_prevention_summary(),
            'force_complete_check': (force_complete, force_reason),
            'smart_recommendation': self.loop_prevention.get_navigation_recommendation(page_content)
        }
        
        # 决策逻辑
        if force_complete:
            return False, f"强制完成: {force_reason}", enhancement_data
        
        if loop_result.detected and loop_result.severity in ["high", "critical"]:
            return False, f"循环检测阻止: {loop_result.recommendation}", enhancement_data
        
        if loop_result.detected and loop_result.severity == "medium":
            logger.warning(f"⚠️ 循环警告: {loop_result.recommendation}")
        
        return True, "", enhancement_data
    
    def track_action_execution(
        self, 
        action_type: str, 
        target: str, 
        current_url: str,
        success: bool = True,
        result: str = "",
        page_title: str = ""
    ) -> None:
        """追踪操作执行"""
        if not self.is_enabled:
            return
        
        # 更新访问记录
        if action_type == "visit_url":
            self.loop_prevention.track_page_visit(current_url, page_title)
        
        # 追踪操作
        self.loop_prevention.track_action(
            action_type, target, current_url, success, result
        )
        
        logger.info(f"📝 追踪操作: {action_type} -> {target} ({'成功' if success else '失败'})")
    
    def generate_enhanced_prompt(
        self,
        last_outside_message: str,
        webpage_text: str,
        url: str,
        visible_targets: str,
        tabs_information: str = "",
        other_targets_str: str = "",
        focused_hint: str = "",
        consider_screenshot: str = "Attached is a screenshot"
    ) -> str:
        """生成增强的提示词"""
        if not self.is_enabled:
            # 返回原始格式的提示词
            return f"""
The last request received was: {last_outside_message}

{tabs_information}

The webpage has the following text:
{webpage_text}

{consider_screenshot} which is open to the page '{url}'. In this screenshot, interactive elements are outlined in bounding boxes in red. Each bounding box has a numeric ID label in red. Additional information about each visible label is listed below:

{visible_targets}{other_targets_str}{focused_hint}
"""
        
        # 获取当前循环检测状态
        current_loop_result = None
        if self.loop_prevention.action_history:
            # 模拟检查当前状态
            current_loop_result = self.loop_prevention.check_for_loops("", "", url)
        
        # 生成增强提示词
        enhanced_prompt = generate_enhanced_web_surfer_prompt(
            last_outside_message=last_outside_message,
            webpage_text=webpage_text,
            url=url,
            visible_targets=visible_targets,
            tabs_information=tabs_information,
            other_targets_str=other_targets_str,
            focused_hint=focused_hint,
            consider_screenshot=consider_screenshot,
            loop_detection_result=current_loop_result,
            navigation_plan=self.loop_prevention.current_plan,
            action_history_summary=self.loop_prevention.get_prevention_summary(),
            force_complete_check=self.loop_prevention.should_force_complete()
        )
        
        return enhanced_prompt
    
    def should_force_stop_action(self) -> Tuple[bool, str]:
        """检查是否应该强制使用stop_action"""
        if not self.is_enabled:
            return False, ""
        
        return self.loop_prevention.should_force_complete()
    
    def get_completion_message_suggestion(self) -> str:
        """获取完成消息建议"""
        if not self.is_enabled:
            return ""
        
        summary = self.loop_prevention.get_prevention_summary()
        
        if summary['unique_urls_visited'] > 0:
            if self.loop_prevention.current_plan:
                strategy = self.loop_prevention.current_plan.current_strategy
                if strategy == "find_image":
                    return "✅ 当前步骤已完成 - 已访问产品页面，获得足够的图像参考信息用于生成360度全景相机图像"
                elif strategy == "extract_info":
                    return "✅ 当前步骤已完成 - 已收集足够的产品信息用于下一步处理"
            
            return "✅ 当前步骤已完成 - 已完成网页浏览并收集了相关信息"
        else:
            return "⚠️ 当前步骤因错误完成 - 未能访问目标页面，但可基于已有知识继续"
    
    def _extract_keywords_from_task(self, task_description: str) -> List[str]:
        """从任务描述中提取关键词"""
        keywords = []
        
        # 常见的关键词模式
        keyword_patterns = {
            'image': ['image', 'picture', 'photo', '图像', '图片', '照片'],
            'camera': ['camera', 'panoramic', '相机', '全景', '360'],
            'product': ['product', 'device', '产品', '设备'],
            'reference': ['reference', 'example', '参考', '例子'],
            'information': ['information', 'details', 'specs', '信息', '详情', '规格']
        }
        
        task_lower = task_description.lower()
        
        for category, terms in keyword_patterns.items():
            for term in terms:
                if term in task_lower:
                    keywords.append(term)
        
        return list(set(keywords))  # 去重
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """获取诊断信息"""
        if not self.is_enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "current_task": self.current_task_context,
            "prevention_summary": self.loop_prevention.get_prevention_summary(),
            "navigation_plan": {
                "goal": self.loop_prevention.current_plan.primary_goal if self.loop_prevention.current_plan else None,
                "strategy": self.loop_prevention.current_plan.current_strategy if self.loop_prevention.current_plan else None,
            },
            "force_complete_status": self.loop_prevention.should_force_complete()
        }
    
    def reset_for_new_task(self) -> None:
        """为新任务重置"""
        self.loop_prevention.reset_for_new_task()
        self.current_task_context = ""
        logger.info("🔄 WebSurfer增强补丁已重置")
    
    def enable(self) -> None:
        """启用增强功能"""
        self.is_enabled = True
        logger.info("✅ WebSurfer增强功能已启用")
    
    def disable(self) -> None:
        """禁用增强功能"""
        self.is_enabled = False
        logger.info("❌ WebSurfer增强功能已禁用")


# 全局实例，用于在整个WebSurfer系统中使用
websurfer_enhancement = WebSurferEnhancementPatch()


def patch_websurfer_for_current_task(task_description: str) -> None:
    """为当前任务修补WebSurfer"""
    websurfer_enhancement.initialize_task(task_description)


def get_websurfer_enhancement() -> WebSurferEnhancementPatch:
    """获取WebSurfer增强实例"""
    return websurfer_enhancement


def apply_websurfer_enhancements_to_prompt(
    last_outside_message: str,
    webpage_text: str,
    url: str,
    visible_targets: str,
    **kwargs
) -> str:
    """应用WebSurfer增强功能到提示词"""
    return websurfer_enhancement.generate_enhanced_prompt(
        last_outside_message, webpage_text, url, visible_targets, **kwargs
    )


def check_websurfer_action_before_execution(
    action_type: str,
    target: str,
    current_url: str,
    page_content: str = ""
) -> Tuple[bool, str, Dict[str, Any]]:
    """在执行WebSurfer操作前进行检查"""
    return websurfer_enhancement.check_before_action(
        action_type, target, current_url, page_content
    )


def track_websurfer_action_after_execution(
    action_type: str,
    target: str,
    current_url: str,
    success: bool = True,
    result: str = "",
    page_title: str = ""
) -> None:
    """在WebSurfer操作执行后进行追踪"""
    websurfer_enhancement.track_action_execution(
        action_type, target, current_url, success, result, page_title
    )