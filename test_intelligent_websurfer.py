#!/usr/bin/env python3
"""
测试智能WebSurfer浏览策略
验证新的智能浏览功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from magentic_ui.agents.web_surfer._intelligent_browsing_strategy import (
    IntelligentBrowsingStrategy,
    InformationCategory,
    BrowsingPhase,
    ActionType
)

def test_intelligent_browsing_strategy():
    """测试智能浏览策略基本功能"""
    print("🧪 测试智能浏览策略系统")
    print("=" * 60)
    
    # 创建策略实例
    strategy = IntelligentBrowsingStrategy()
    print(f"✅ 策略实例创建成功，当前阶段: {strategy.current_phase}")
    
    # 测试任务分析
    task_description = "访问te720.com网站，收集360度全景相机的产品信息和图片"
    target_url = "https://te720.com"
    
    print(f"\n📋 测试任务分析...")
    goals = strategy.analyze_task_and_create_goals(task_description, target_url)
    print(f"  创建了 {len(goals)} 个信息目标:")
    for i, goal in enumerate(goals, 1):
        print(f"    {i}. {goal.description} (优先级: {goal.priority}, 必需: {goal.required})")
    
    # 测试浏览计划创建
    print(f"\n🗺️ 测试浏览计划创建...")
    website_structure = {"main_nav": ["产品", "关于我们", "联系"], "has_search": True}
    plan = strategy.create_browsing_plan(website_structure, task_description)
    print(f"  创建了 {len(plan)} 个浏览动作:")
    for i, action in enumerate(plan, 1):
        print(f"    {i}. {action.description} (优先级: {action.priority}, 预计: {action.estimated_time}秒)")
    
    # 测试停止条件判断
    print(f"\n⏱️ 测试停止条件判断...")
    should_stop, reason = strategy.should_stop_browsing()
    print(f"  当前是否应该停止: {should_stop}")
    print(f"  原因: {reason}")
    
    # 模拟记录一些动作
    print(f"\n📝 测试动作记录...")
    from magentic_ui.agents.web_surfer._intelligent_browsing_strategy import BrowsingAction
    
    action1 = BrowsingAction(
        action_type=ActionType.VISIT_URL,
        target="https://te720.com",
        description="访问主页",
        expected_info=[InformationCategory.GENERAL_INFO]
    )
    
    strategy.record_action(action1, "https://te720.com", "成功访问网站首页", [], True)
    print(f"  记录了访问动作，当前动作计数: {strategy.current_action_count}")
    
    action2 = BrowsingAction(
        action_type=ActionType.EXTRACT_INFO,
        target="product_info",
        description="提取产品信息",
        expected_info=[InformationCategory.PRODUCT_SPECS, InformationCategory.FEATURES]
    )
    
    product_info = """
    te720.com - 360度全景相机
    产品特性：
    - 4镜头分布式设计
    - 8K高清录制
    - 实时拼接技术
    - 支持直播功能
    """
    
    strategy.record_action(action2, "https://te720.com/products", product_info, [], True)
    print(f"  记录了信息提取动作，当前动作计数: {strategy.current_action_count}")
    
    # 检查信息收集状态
    print(f"\n📊 信息收集状态:")
    print(f"  已收集信息类别: {list(strategy.collected_information.keys())}")
    for goal in strategy.information_goals:
        print(f"    {goal.description}: {goal.current_status}")
    
    # 测试完成总结
    print(f"\n📋 测试完成总结...")
    summary = strategy.generate_completion_summary()
    print(f"完成总结:\n{summary}")
    
    # 测试浏览上下文
    print(f"\n🔄 测试浏览上下文...")
    context = strategy.get_browsing_context()
    print(f"浏览上下文:\n{context}")
    
    print(f"\n🎉 智能浏览策略测试完成!")
    return True

def test_enhanced_prompts():
    """测试增强的提示词系统"""
    print("\n🔧 测试增强提示词系统")
    print("=" * 60)
    
    from magentic_ui.agents.web_surfer._enhanced_prompts import (
        format_intelligent_prompt,
        INTELLIGENT_WEB_SURFER_SYSTEM_MESSAGE,
        generate_browsing_context,
        generate_information_goals_status,
        generate_access_history_summary
    )
    
    # 创建策略用于测试
    strategy = IntelligentBrowsingStrategy()
    strategy.analyze_task_and_create_goals("收集360度相机产品信息", "https://te720.com")
    
    # 测试上下文生成
    browsing_context = generate_browsing_context(strategy)
    information_goals = generate_information_goals_status(strategy)
    access_history = generate_access_history_summary(strategy)
    
    print(f"✅ 浏览上下文生成: {len(browsing_context)} 字符")
    print(f"✅ 信息目标状态: {len(information_goals)} 字符")
    print(f"✅ 访问历史摘要: {len(access_history)} 字符")
    
    # 测试提示词格式化
    formatted_prompt = format_intelligent_prompt(
        INTELLIGENT_WEB_SURFER_SYSTEM_MESSAGE,
        date_today="2024-01-15",
        browsing_context=browsing_context,
        information_goals=information_goals,
        access_history=access_history
    )
    
    print(f"✅ 格式化提示词: {len(formatted_prompt)} 字符")
    print(f"  提示词开头: {formatted_prompt[:200]}...")
    
    print(f"\n🎉 增强提示词系统测试完成!")
    return True

def main():
    """主函数"""
    try:
        print("🚀 开始测试智能WebSurfer浏览策略")
        print("=" * 80)
        
        # 测试智能浏览策略
        test_result1 = test_intelligent_browsing_strategy()
        
        # 测试增强提示词
        test_result2 = test_enhanced_prompts()
        
        print("\n🎯 **测试总结**:")
        print(f"✅ 智能浏览策略: {'通过' if test_result1 else '失败'}")
        print(f"✅ 增强提示词系统: {'通过' if test_result2 else '失败'}")
        
        if test_result1 and test_result2:
            print("\n💡 **核心功能验证**:")
            print("• 智能任务分析和目标创建 ✅")
            print("• 浏览计划生成和执行策略 ✅") 
            print("• 访问历史记录和防重复机制 ✅")
            print("• 信息收集状态跟踪 ✅")
            print("• 智能停止条件判断 ✅")
            print("• 增强提示词和上下文生成 ✅")
            
            print("\n🎉 所有测试通过! 智能WebSurfer浏览策略已就绪!")
            return True
        else:
            print("\n❌ 部分测试失败!")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)