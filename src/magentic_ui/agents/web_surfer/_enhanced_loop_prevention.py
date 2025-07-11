"""
🔧 WebSurfer循环检测和防护增强模块

主要功能：
1. 追踪URL访问历史
2. 检测重复操作模式
3. 智能规划和目标管理
4. 强制防循环机制
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
from loguru import logger


class ActionType(Enum):
    """操作类型枚举"""
    CLICK = "click"
    VISIT_URL = "visit_url"
    TYPE = "type"
    SCROLL = "scroll"
    SEARCH = "search"
    STOP = "stop_action"
    ANSWER = "answer_question"


@dataclass
class ActionRecord:
    """操作记录"""
    action_type: ActionType
    target: str  # URL, element_id, or text content
    timestamp: datetime
    page_url: str
    success: bool = True
    result: str = ""
    page_title: str = ""


@dataclass
class PageVisit:
    """页面访问记录"""
    url: str
    visit_time: datetime
    page_title: str = ""
    actions_performed: List[ActionRecord] = field(default_factory=list)
    content_hash: str = ""
    found_target_content: bool = False


@dataclass
class NavigationPlan:
    """导航计划"""
    primary_goal: str
    sub_goals: List[str] = field(default_factory=list)
    completed_goals: List[str] = field(default_factory=list)
    target_keywords: List[str] = field(default_factory=list)
    max_pages: int = 3
    max_actions: int = 8
    current_strategy: str = "explore"  # explore, focused_search, extract_info, complete


class LoopDetectionResult:
    """循环检测结果"""
    def __init__(self, detected: bool, loop_type: str = "", severity: str = "low", 
                 recommendation: str = "", evidence: List[str] = None):
        self.detected = detected
        self.loop_type = loop_type
        self.severity = severity
        self.recommendation = recommendation
        self.evidence = evidence or []


class EnhancedLoopPrevention:
    """🔧 增强的循环检测和防护系统"""
    
    def __init__(self, max_url_visits: int = 2, max_same_action: int = 2):
        # 历史记录
        self.url_visit_history: List[PageVisit] = []
        self.action_history: List[ActionRecord] = []
        
        # 循环检测配置
        self.max_url_visits = max_url_visits
        self.max_same_action = max_same_action
        
        # 访问统计
        self.url_visit_count: Dict[str, int] = {}
        self.action_sequence: List[str] = []
        
        # 导航计划
        self.current_plan: Optional[NavigationPlan] = None
        
        # 目标追踪
        self.found_content: Set[str] = set()
        self.search_keywords: List[str] = []
        
        logger.info("🔧 EnhancedLoopPrevention 初始化完成")
    
    def set_navigation_plan(self, goal: str, keywords: List[str] = None) -> None:
        """设置导航计划"""
        self.current_plan = NavigationPlan(
            primary_goal=goal,
            target_keywords=keywords or [],
            max_pages=3,
            max_actions=8
        )
        
        # 从目标中提取关键词
        if keywords:
            self.search_keywords.extend(keywords)
        
        # 根据目标类型调整策略
        if any(keyword in goal.lower() for keyword in ['image', 'picture', '图像', '图片']):
            self.current_plan.current_strategy = "find_image"
            self.current_plan.max_actions = 4
        elif any(keyword in goal.lower() for keyword in ['read', 'information', '阅读', '信息']):
            self.current_plan.current_strategy = "extract_info"
            self.current_plan.max_actions = 6
        
        logger.info(f"🎯 设置导航计划: {goal} - 策略: {self.current_plan.current_strategy}")
    
    def track_page_visit(self, url: str, page_title: str = "", content_hash: str = "") -> PageVisit:
        """追踪页面访问"""
        # 更新访问计数
        normalized_url = self._normalize_url(url)
        self.url_visit_count[normalized_url] = self.url_visit_count.get(normalized_url, 0) + 1
        
        # 创建访问记录
        visit = PageVisit(
            url=normalized_url,
            visit_time=datetime.now(),
            page_title=page_title,
            content_hash=content_hash
        )
        
        self.url_visit_history.append(visit)
        
        logger.info(f"📍 追踪页面访问: {page_title} ({self.url_visit_count[normalized_url]}次)")
        
        return visit
    
    def track_action(self, action_type: str, target: str, page_url: str, 
                    success: bool = True, result: str = "") -> ActionRecord:
        """追踪操作"""
        try:
            action_enum = ActionType(action_type)
        except ValueError:
            action_enum = ActionType.CLICK  # 默认值
        
        action = ActionRecord(
            action_type=action_enum,
            target=target,
            timestamp=datetime.now(),
            page_url=self._normalize_url(page_url),
            success=success,
            result=result
        )
        
        self.action_history.append(action)
        
        # 更新操作序列（用于模式检测）
        action_signature = f"{action_type}:{target}"
        self.action_sequence.append(action_signature)
        
        # 保持序列在合理长度
        if len(self.action_sequence) > 10:
            self.action_sequence = self.action_sequence[-8:]
        
        logger.info(f"🔨 追踪操作: {action_type} -> {target}")
        
        return action
    
    def check_for_loops(self, proposed_action: str, proposed_target: str, 
                       current_url: str) -> LoopDetectionResult:
        """检查循环模式"""
        
        # 1. 检查URL访问循环
        url_loop = self._check_url_visit_loop(current_url)
        if url_loop.detected:
            return url_loop
        
        # 2. 检查操作重复循环
        action_loop = self._check_action_repetition_loop(proposed_action, proposed_target)
        if action_loop.detected:
            return action_loop
        
        # 3. 检查导航模式循环
        navigation_loop = self._check_navigation_pattern_loop()
        if navigation_loop.detected:
            return navigation_loop
        
        # 4. 检查目标达成情况
        goal_check = self._check_goal_completion()
        if goal_check.detected:
            return goal_check
        
        return LoopDetectionResult(detected=False)
    
    def _check_url_visit_loop(self, current_url: str) -> LoopDetectionResult:
        """检查URL访问循环"""
        normalized_url = self._normalize_url(current_url)
        visit_count = self.url_visit_count.get(normalized_url, 0)
        
        if visit_count >= self.max_url_visits:
            return LoopDetectionResult(
                detected=True,
                loop_type="url_revisit",
                severity="high",
                recommendation="避免重复访问相同URL，尝试新的页面或完成任务",
                evidence=[f"URL {normalized_url} 已访问 {visit_count} 次"]
            )
        elif visit_count >= self.max_url_visits - 1:
            return LoopDetectionResult(
                detected=True,
                loop_type="url_revisit_warning",
                severity="medium",
                recommendation="即将达到URL访问限制，考虑从当前页面提取信息或转向新页面",
                evidence=[f"URL {normalized_url} 已访问 {visit_count} 次"]
            )
        
        return LoopDetectionResult(detected=False)
    
    def _check_action_repetition_loop(self, proposed_action: str, proposed_target: str) -> LoopDetectionResult:
        """检查操作重复循环"""
        proposed_signature = f"{proposed_action}:{proposed_target}"
        
        # 检查最近的操作序列
        if len(self.action_sequence) >= 2:
            recent_actions = self.action_sequence[-2:]
            if all(action == proposed_signature for action in recent_actions):
                return LoopDetectionResult(
                    detected=True,
                    loop_type="action_repetition",
                    severity="high",
                    recommendation="避免重复相同操作，尝试不同的策略或完成任务",
                    evidence=[f"连续重复操作: {proposed_signature}"]
                )
        
        # 检查操作计数
        action_count = self.action_sequence.count(proposed_signature)
        if action_count >= self.max_same_action:
            return LoopDetectionResult(
                detected=True,
                loop_type="excessive_action_repetition",
                severity="high",
                recommendation="操作重复次数过多，强制切换策略或完成任务",
                evidence=[f"操作 {proposed_signature} 已执行 {action_count} 次"]
            )
        
        return LoopDetectionResult(detected=False)
    
    def _check_navigation_pattern_loop(self) -> LoopDetectionResult:
        """检查导航模式循环"""
        if len(self.action_history) >= 4:
            # 检查最近的导航是否形成循环模式
            recent_actions = self.action_history[-4:]
            click_actions = [a for a in recent_actions if a.action_type == ActionType.CLICK]
            
            if len(click_actions) >= 3:
                # 检查是否在相同的几个链接之间循环点击
                targets = [a.target for a in click_actions]
                unique_targets = set(targets)
                
                if len(unique_targets) <= 2 and len(targets) >= 3:
                    return LoopDetectionResult(
                        detected=True,
                        loop_type="navigation_cycle",
                        severity="medium",
                        recommendation="检测到导航循环，尝试不同的链接或使用页面内容提取",
                        evidence=[f"在少数几个链接间循环: {list(unique_targets)}"]
                    )
        
        return LoopDetectionResult(detected=False)
    
    def _check_goal_completion(self) -> LoopDetectionResult:
        """检查目标完成情况"""
        if not self.current_plan:
            return LoopDetectionResult(detected=False)
        
        # 检查是否已经执行了足够多的操作
        action_count = len(self.action_history)
        
        if action_count >= self.current_plan.max_actions:
            return LoopDetectionResult(
                detected=True,
                loop_type="max_actions_reached",
                severity="medium",
                recommendation="已达到最大操作数，应该总结现有信息并完成任务",
                evidence=[f"已执行 {action_count} 个操作，达到限制 {self.current_plan.max_actions}"]
            )
        
        # 检查是否访问了足够多的页面
        unique_urls = len(set(visit.url for visit in self.url_visit_history))
        if unique_urls >= self.current_plan.max_pages:
            return LoopDetectionResult(
                detected=True,
                loop_type="max_pages_reached",
                severity="medium",
                recommendation="已访问足够多的页面，应该从现有信息中提取内容",
                evidence=[f"已访问 {unique_urls} 个页面，达到限制 {self.current_plan.max_pages}"]
            )
        
        # 检查策略特定的完成条件
        if self.current_plan.current_strategy == "find_image":
            # 对于图像查找任务，如果已经访问了产品相关页面，应该完成
            product_related_visits = sum(1 for visit in self.url_visit_history 
                                       if any(keyword in visit.page_title.lower() 
                                            for keyword in ['product', 'camera', '产品', '相机']))
            if product_related_visits >= 1 and action_count >= 3:
                return LoopDetectionResult(
                    detected=True,
                    loop_type="image_task_sufficient",
                    severity="low",
                    recommendation="已访问产品页面，应有足够信息用于图像生成",
                    evidence=[f"访问了 {product_related_visits} 个产品相关页面"]
                )
        
        return LoopDetectionResult(detected=False)
    
    def should_force_complete(self) -> Tuple[bool, str]:
        """检查是否应该强制完成"""
        if not self.current_plan:
            return False, ""
        
        # 检查各种强制完成条件
        reasons = []
        
        # 1. 时间限制检查
        if self.url_visit_history:
            first_visit = self.url_visit_history[0].visit_time
            elapsed = (datetime.now() - first_visit).total_seconds()
            if elapsed > 300:  # 5分钟
                reasons.append("超过5分钟执行时间")
        
        # 2. 操作数量检查
        if len(self.action_history) >= self.current_plan.max_actions:
            reasons.append(f"达到最大操作数 {self.current_plan.max_actions}")
        
        # 3. 页面访问数量检查
        unique_urls = len(set(visit.url for visit in self.url_visit_history))
        if unique_urls >= self.current_plan.max_pages:
            reasons.append(f"达到最大页面数 {self.current_plan.max_pages}")
        
        # 4. 循环检测触发
        recent_loops = sum(1 for action in self.action_history[-3:] if "重复" in action.result)
        if recent_loops >= 2:
            reasons.append("检测到多次循环行为")
        
        should_complete = len(reasons) > 0
        reason_text = "; ".join(reasons) if reasons else ""
        
        return should_complete, reason_text
    
    def get_navigation_recommendation(self, current_page_content: str = "") -> str:
        """获取导航建议"""
        if not self.current_plan:
            return "建议设置明确的导航目标"
        
        # 分析当前策略
        strategy = self.current_plan.current_strategy
        action_count = len(self.action_history)
        
        if strategy == "find_image":
            if action_count == 0:
                return "建议首先访问产品主页，查找产品图片"
            elif action_count >= 2:
                return "已执行多次操作，建议使用answer_question工具提取页面信息或stop_action完成任务"
            else:
                return "继续在当前页面查找图片信息，避免过度导航"
        
        elif strategy == "extract_info":
            if action_count >= 3:
                return "建议使用answer_question工具从当前页面提取信息"
            else:
                return "继续收集信息，但避免重复访问相同页面"
        
        else:
            if action_count >= 4:
                return "建议总结现有信息并完成任务"
            else:
                return "继续探索，但保持目标导向"
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        # 移除fragment和某些查询参数
        url = re.sub(r'#.*$', '', url)
        url = re.sub(r'[?&]utm_[^&]*', '', url)
        url = re.sub(r'[?&]ref=[^&]*', '', url)
        return url.lower().strip()
    
    def get_prevention_summary(self) -> Dict[str, Any]:
        """获取防护摘要"""
        unique_urls = len(set(visit.url for visit in self.url_visit_history))
        
        return {
            "total_actions": len(self.action_history),
            "unique_urls_visited": unique_urls,
            "url_visit_counts": dict(self.url_visit_count),
            "current_strategy": self.current_plan.current_strategy if self.current_plan else "none",
            "found_content_count": len(self.found_content),
            "recent_action_pattern": self.action_sequence[-5:] if len(self.action_sequence) >= 5 else self.action_sequence
        }
    
    def reset_for_new_task(self) -> None:
        """为新任务重置状态"""
        self.url_visit_history.clear()
        self.action_history.clear()
        self.url_visit_count.clear()
        self.action_sequence.clear()
        self.found_content.clear()
        self.search_keywords.clear()
        self.current_plan = None
        
        logger.info("🔄 循环防护系统已重置")