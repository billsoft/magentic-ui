"""
智能浏览策略系统 - 解决重复点击、无章法浏览和无法及时停止的问题
"""

import json
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, urljoin
import re

class BrowsingPhase(Enum):
    """浏览阶段枚举"""
    PLANNING = "planning"          # 规划阶段：分析网站结构，制定访问计划
    EXECUTING = "executing"        # 执行阶段：按计划执行访问
    GATHERING = "gathering"        # 收集阶段：提取和整理信息
    EVALUATING = "evaluating"      # 评估阶段：判断信息是否充分
    COMPLETED = "completed"        # 完成阶段：任务已完成

class ActionType(Enum):
    """动作类型枚举"""
    VISIT_URL = "visit_url"
    CLICK_LINK = "click_link" 
    SCROLL = "scroll"
    EXTRACT_INFO = "extract_info"
    SEARCH = "search"

class InformationCategory(Enum):
    """信息类别枚举"""
    PRODUCT_SPECS = "product_specs"      # 产品规格
    PRODUCT_IMAGES = "product_images"    # 产品图片
    PRICING = "pricing"                  # 价格信息
    FEATURES = "features"                # 功能特性
    COMPANY_INFO = "company_info"        # 公司信息
    CONTACT_INFO = "contact_info"        # 联系信息
    GENERAL_INFO = "general_info"        # 一般信息

@dataclass
class BrowsingAction:
    """浏览动作"""
    action_type: ActionType
    target: str                          # URL或元素ID
    description: str                     # 动作描述
    expected_info: List[InformationCategory]  # 期望获得的信息类型
    priority: int = 1                    # 优先级 1-5，1最高
    estimated_time: int = 10             # 预估耗时（秒）

@dataclass
class AccessRecord:
    """访问记录"""
    url: str
    timestamp: float
    action_taken: str
    elements_clicked: List[str] = field(default_factory=list)
    information_found: Dict[InformationCategory, str] = field(default_factory=dict)
    success: bool = True

@dataclass
class InformationGoal:
    """信息目标"""
    category: InformationCategory
    description: str
    required: bool = True               # 是否必需
    priority: int = 1                   # 优先级
    satisfaction_criteria: str = ""     # 满足标准
    current_status: str = "pending"     # pending, partial, complete
    collected_info: str = ""            # 已收集的信息

class IntelligentBrowsingStrategy:
    """
    智能浏览策略系统
    
    解决三大核心问题：
    1. 重复点击和循环访问
    2. 无章法的浏览
    3. 无法及时停止
    """
    
    def __init__(self):
        self.current_phase = BrowsingPhase.PLANNING
        self.access_history: List[AccessRecord] = []
        self.visited_urls: Set[str] = set()
        self.clicked_elements: Set[str] = set()
        self.browsing_plan: List[BrowsingAction] = []
        self.information_goals: List[InformationGoal] = []
        self.collected_information: Dict[InformationCategory, str] = {}
        self.start_time = time.time()
        self.max_browsing_time = 300  # 5分钟最大浏览时间
        self.max_actions = 15         # 最大动作数量
        self.current_action_count = 0
        
    def analyze_task_and_create_goals(self, task_description: str, target_url: str) -> List[InformationGoal]:
        """
        分析任务并创建信息目标
        
        Args:
            task_description: 任务描述
            target_url: 目标网站URL
            
        Returns:
            信息目标列表
        """
        goals = []
        
        # 根据任务描述分析需要的信息类型
        task_lower = task_description.lower()
        
        if any(keyword in task_lower for keyword in ["产品", "相机", "设备", "product", "camera"]):
            goals.extend([
                InformationGoal(
                    category=InformationCategory.PRODUCT_SPECS,
                    description="获取产品的详细技术规格",
                    required=True,
                    priority=1,
                    satisfaction_criteria="包含主要技术参数，如分辨率、镜头数量、功能特性等"
                ),
                InformationGoal(
                    category=InformationCategory.PRODUCT_IMAGES,
                    description="获取产品图片或视觉参考",
                    required=True,
                    priority=2,
                    satisfaction_criteria="找到产品的外观图片或渲染图"
                ),
                InformationGoal(
                    category=InformationCategory.FEATURES,
                    description="了解产品的主要功能特性",
                    required=True,
                    priority=1,
                    satisfaction_criteria="列出3-5个主要功能特点"
                )
            ])
        
        if any(keyword in task_lower for keyword in ["价格", "报价", "cost", "price"]):
            goals.append(
                InformationGoal(
                    category=InformationCategory.PRICING,
                    description="获取产品价格信息",
                    required=False,
                    priority=3,
                    satisfaction_criteria="找到具体价格或价格范围"
                )
            )
        
        if any(keyword in task_lower for keyword in ["公司", "厂商", "制造商", "company", "manufacturer"]):
            goals.append(
                InformationGoal(
                    category=InformationCategory.COMPANY_INFO,
                    description="了解公司背景信息",
                    required=False,
                    priority=4,
                    satisfaction_criteria="包含公司简介、规模、专业领域等"
                )
            )
        
        # 如果没有明确的信息需求，添加通用目标
        if not goals:
            goals.append(
                InformationGoal(
                    category=InformationCategory.GENERAL_INFO,
                    description="收集与任务相关的一般信息",
                    required=True,
                    priority=1,
                    satisfaction_criteria="收集到与任务相关的有用信息"
                )
            )
        
        self.information_goals = goals
        return goals
    
    def create_browsing_plan(self, website_structure: Dict[str, Any], task_description: str) -> List[BrowsingAction]:
        """
        根据网站结构和任务创建浏览计划
        
        Args:
            website_structure: 网站结构信息（从首页分析得出）
            task_description: 任务描述
            
        Returns:
            浏览动作计划列表
        """
        plan = []
        
        # 1. 首页概览和导航分析
        plan.append(BrowsingAction(
            action_type=ActionType.EXTRACT_INFO,
            target="homepage",
            description="分析首页结构，识别主要导航和重要链接",
            expected_info=[InformationCategory.GENERAL_INFO],
            priority=1,
            estimated_time=5
        ))
        
        # 2. 根据任务类型规划访问路径
        task_lower = task_description.lower()
        
        if any(keyword in task_lower for keyword in ["产品", "相机", "product", "camera"]):
            # 产品相关任务
            plan.extend([
                BrowsingAction(
                    action_type=ActionType.CLICK_LINK,
                    target="产品|products|camera",  # 支持多种可能的链接文本
                    description="访问产品页面获取产品列表",
                    expected_info=[InformationCategory.PRODUCT_SPECS, InformationCategory.PRODUCT_IMAGES],
                    priority=1,
                    estimated_time=10
                ),
                BrowsingAction(
                    action_type=ActionType.EXTRACT_INFO,
                    target="product_page",
                    description="从产品页面提取详细信息",
                    expected_info=[InformationCategory.PRODUCT_SPECS, InformationCategory.FEATURES],
                    priority=1,
                    estimated_time=15
                )
            ])
        
        # 3. 备选方案
        plan.extend([
            BrowsingAction(
                action_type=ActionType.CLICK_LINK,
                target="关于我们|about|company",
                description="了解公司背景（备选）",
                expected_info=[InformationCategory.COMPANY_INFO],
                priority=3,
                estimated_time=8
            ),
            BrowsingAction(
                action_type=ActionType.SEARCH,
                target="search_if_needed",
                description="如果导航无效，使用搜索功能",
                expected_info=[InformationCategory.GENERAL_INFO],
                priority=4,
                estimated_time=10
            )
        ])
        
        # 按优先级排序
        plan.sort(key=lambda x: (x.priority, x.estimated_time))
        
        self.browsing_plan = plan
        self.current_phase = BrowsingPhase.EXECUTING
        return plan
    
    def should_perform_action(self, action: BrowsingAction) -> Tuple[bool, str]:
        """
        判断是否应该执行某个动作
        
        Args:
            action: 要评估的动作
            
        Returns:
            (是否执行, 决策理由)
        """
        # 1. 检查时间限制
        if time.time() - self.start_time > self.max_browsing_time:
            return False, "已达到最大浏览时间限制"
        
        # 2. 检查动作数量限制
        if self.current_action_count >= self.max_actions:
            return False, "已达到最大动作数量限制"
        
        # 3. 检查是否已经访问过相同的目标
        if action.action_type == ActionType.VISIT_URL:
            if action.target in self.visited_urls:
                return False, f"已访问过URL: {action.target}"
        
        elif action.action_type == ActionType.CLICK_LINK:
            # 检查是否已点击过相似的元素
            for clicked in self.clicked_elements:
                if self._is_similar_element(action.target, clicked):
                    return False, f"已点击过相似元素: {clicked}"
        
        # 4. 检查信息目标是否已满足
        expected_categories = action.expected_info
        if all(self._is_information_sufficient(cat) for cat in expected_categories):
            return False, "所需信息已充分收集"
        
        # 5. 检查动作的价值
        if action.priority > 3 and len(self.access_history) > 5:
            return False, "低优先级动作，已有足够访问历史"
        
        return True, "动作有效，应该执行"
    
    def record_action(self, action: BrowsingAction, url: str, result: str, 
                     elements_clicked: List[str] = None, success: bool = True):
        """
        记录执行的动作
        
        Args:
            action: 执行的动作
            url: 当前URL
            result: 动作结果
            elements_clicked: 点击的元素列表
            success: 是否成功
        """
        # 记录访问历史
        record = AccessRecord(
            url=url,
            timestamp=time.time(),
            action_taken=f"{action.action_type.value}: {action.description}",
            elements_clicked=elements_clicked or [],
            success=success
        )
        
        self.access_history.append(record)
        self.visited_urls.add(url)
        
        if elements_clicked:
            self.clicked_elements.update(elements_clicked)
        
        # 更新动作计数
        self.current_action_count += 1
        
        # 分析结果中的信息
        self._analyze_and_extract_information(result, action.expected_info)
    
    def _analyze_and_extract_information(self, content: str, expected_categories: List[InformationCategory]):
        """
        分析内容并提取信息
        
        Args:
            content: 页面内容或结果
            expected_categories: 期望的信息类别
        """
        content_lower = content.lower()
        
        for category in expected_categories:
            if category == InformationCategory.PRODUCT_SPECS:
                # 查找产品规格信息
                specs_keywords = ["分辨率", "镜头", "像素", "规格", "参数", "技术", "性能"]
                if any(keyword in content_lower for keyword in specs_keywords):
                    self.collected_information[category] = self._extract_product_specs(content)
                    self._update_goal_status(category, "complete")
            
            elif category == InformationCategory.PRODUCT_IMAGES:
                # 查找产品图片相关信息
                if any(keyword in content_lower for keyword in ["图片", "照片", "image", "photo"]):
                    self.collected_information[category] = "发现产品图片"
                    self._update_goal_status(category, "complete")
            
            elif category == InformationCategory.FEATURES:
                # 查找功能特性
                feature_keywords = ["功能", "特性", "特点", "优势", "feature", "capability"]
                if any(keyword in content_lower for keyword in feature_keywords):
                    self.collected_information[category] = self._extract_features(content)
                    self._update_goal_status(category, "complete")
            
            elif category == InformationCategory.COMPANY_INFO:
                # 查找公司信息
                company_keywords = ["公司", "企业", "关于", "团队", "company", "about"]
                if any(keyword in content_lower for keyword in company_keywords):
                    self.collected_information[category] = self._extract_company_info(content)
                    self._update_goal_status(category, "complete")
    
    def _extract_product_specs(self, content: str) -> str:
        """提取产品规格信息"""
        # 简化的规格提取逻辑
        specs = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["分辨率", "镜头", "像素", "k", "规格"]):
                specs.append(line.strip())
        
        return '\n'.join(specs[:5])  # 最多5行规格信息
    
    def _extract_features(self, content: str) -> str:
        """提取功能特性"""
        features = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["功能", "特性", "支持", "具备"]):
                features.append(line.strip())
        
        return '\n'.join(features[:5])
    
    def _extract_company_info(self, content: str) -> str:
        """提取公司信息"""
        company_info = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["公司", "企业", "成立", "专业", "领先"]):
                company_info.append(line.strip())
        
        return '\n'.join(company_info[:3])
    
    def _update_goal_status(self, category: InformationCategory, status: str):
        """更新信息目标状态"""
        for goal in self.information_goals:
            if goal.category == category:
                goal.current_status = status
                if category in self.collected_information:
                    goal.collected_info = self.collected_information[category]
                break
    
    def _is_information_sufficient(self, category: InformationCategory) -> bool:
        """判断某类信息是否已充分收集"""
        for goal in self.information_goals:
            if goal.category == category:
                return goal.current_status == "complete"
        return False
    
    def _is_similar_element(self, element1: str, element2: str) -> bool:
        """判断两个元素是否相似"""
        # 简化的相似性判断
        elem1_lower = element1.lower()
        elem2_lower = element2.lower()
        
        # 如果包含相同的关键词，认为是相似的
        keywords1 = set(re.findall(r'\w+', elem1_lower))
        keywords2 = set(re.findall(r'\w+', elem2_lower))
        
        if keywords1 & keywords2:  # 有交集
            return True
        
        return False
    
    def should_stop_browsing(self) -> Tuple[bool, str]:
        """
        判断是否应该停止浏览
        
        Returns:
            (是否停止, 停止理由)
        """
        # 1. 检查信息目标完成情况
        required_goals = [g for g in self.information_goals if g.required]
        completed_required = [g for g in required_goals if g.current_status == "complete"]
        
        if len(completed_required) == len(required_goals):
            return True, "所有必需的信息目标已完成"
        
        # 2. 检查时间限制
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.max_browsing_time:
            return True, f"已达到最大浏览时间限制({self.max_browsing_time}秒)"
        
        # 3. 检查动作数量限制
        if self.current_action_count >= self.max_actions:
            return True, f"已达到最大动作数量限制({self.max_actions})"
        
        # 4. 检查信息收集的充分性
        if len(self.collected_information) >= 2:  # 至少收集了2类信息
            completion_rate = len(completed_required) / max(len(required_goals), 1)
            if completion_rate >= 0.6:  # 60%完成率
                return True, "信息收集已达到较高完成率"
        
        # 5. 检查连续失败
        recent_failures = 0
        for record in self.access_history[-5:]:  # 最近5次操作
            if not record.success:
                recent_failures += 1
        
        if recent_failures >= 3:
            return True, "连续多次操作失败，建议停止"
        
        return False, "继续浏览"
    
    def get_next_recommended_action(self) -> Optional[BrowsingAction]:
        """
        获取下一个推荐的动作
        
        Returns:
            推荐的浏览动作，如果没有则返回None
        """
        # 检查是否应该停止
        should_stop, reason = self.should_stop_browsing()
        if should_stop:
            return None
        
        # 从计划中找到下一个应该执行的动作
        for action in self.browsing_plan:
            should_perform, reason = self.should_perform_action(action)
            if should_perform:
                return action
        
        return None
    
    def generate_completion_summary(self) -> str:
        """
        生成完成总结
        
        Returns:
            总结文本
        """
        summary_parts = []
        
        # 1. 总体完成情况
        required_goals = [g for g in self.information_goals if g.required]
        completed_goals = [g for g in self.information_goals if g.current_status == "complete"]
        
        summary_parts.append(f"✅ 当前步骤已完成：浏览任务完成")
        summary_parts.append(f"📊 完成情况：{len(completed_goals)}/{len(self.information_goals)} 个信息目标已完成")
        
        # 2. 收集到的信息
        if self.collected_information:
            summary_parts.append("\n📋 已收集的信息：")
            for category, info in self.collected_information.items():
                category_name = {
                    InformationCategory.PRODUCT_SPECS: "产品规格",
                    InformationCategory.PRODUCT_IMAGES: "产品图片",
                    InformationCategory.FEATURES: "功能特性",
                    InformationCategory.COMPANY_INFO: "公司信息",
                    InformationCategory.GENERAL_INFO: "一般信息"
                }.get(category, category.value)
                
                summary_parts.append(f"  • {category_name}: {info[:100]}{'...' if len(info) > 100 else ''}")
        
        # 3. 访问统计
        summary_parts.append(f"\n📈 访问统计：")
        summary_parts.append(f"  • 访问页面数：{len(self.visited_urls)}")
        summary_parts.append(f"  • 执行动作数：{self.current_action_count}")
        summary_parts.append(f"  • 用时：{int(time.time() - self.start_time)}秒")
        
        # 4. 未完成的目标（如果有）
        incomplete_goals = [g for g in required_goals if g.current_status != "complete"]
        if incomplete_goals:
            summary_parts.append(f"\n⚠️ 未完成的必需目标：")
            for goal in incomplete_goals:
                summary_parts.append(f"  • {goal.description}")
        
        return "\n".join(summary_parts)
    
    def get_browsing_context(self) -> str:
        """
        获取浏览上下文信息（供LLM使用）
        
        Returns:
            上下文信息字符串
        """
        context_parts = []
        
        # 1. 当前阶段和进度
        context_parts.append(f"🔄 浏览阶段：{self.current_phase.value}")
        context_parts.append(f"📊 动作计数：{self.current_action_count}/{self.max_actions}")
        
        # 2. 信息目标状态
        context_parts.append(f"\n🎯 信息目标状态：")
        for goal in self.information_goals:
            status_icon = {"pending": "⏳", "partial": "🔄", "complete": "✅"}.get(goal.current_status, "❓")
            context_parts.append(f"  {status_icon} {goal.description} ({goal.current_status})")
        
        # 3. 访问历史
        if self.access_history:
            context_parts.append(f"\n📝 最近访问：")
            for record in self.access_history[-3:]:  # 最近3次
                context_parts.append(f"  • {record.action_taken} ({'✅' if record.success else '❌'})")
        
        # 4. 防重复提醒
        if self.clicked_elements:
            context_parts.append(f"\n🚫 已点击元素（避免重复）：")
            context_parts.append(f"  {', '.join(list(self.clicked_elements)[:5])}")
        
        return "\n".join(context_parts)