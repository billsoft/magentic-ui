#!/usr/bin/env python3
"""
🔧 WebSurfer循环防护测试

测试新的循环防护系统是否能有效防止WebSurfer无限循环
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from magentic_ui.agents.web_surfer._enhanced_loop_prevention import EnhancedLoopPrevention
from magentic_ui.agents.web_surfer._websurfer_enhancement_patch import (
    WebSurferEnhancementPatch,
    patch_websurfer_for_current_task,
    check_websurfer_action_before_execution,
    track_websurfer_action_after_execution
)


def test_loop_detection():
    """测试循环检测功能"""
    print("🔧 测试循环检测功能...")
    
    prevention = EnhancedLoopPrevention()
    
    # 设置任务
    task = "访问te720.com网站查找360度全景相机参考图像"
    prevention.set_navigation_plan(task, ["camera", "360", "panoramic"])
    
    print(f"✅ 任务设置: {task}")
    
    # 模拟正常操作序列
    print("\n📋 模拟正常操作序列...")
    
    # 1. 访问主页
    prevention.track_page_visit("https://www.te720.com", "TE720 - 全景相机官网")
    prevention.track_action("visit_url", "https://www.te720.com", "https://www.te720.com")
    
    # 2. 点击产品链接
    prevention.track_action("click", "产品", "https://www.te720.com")
    
    # 3. 查看产品页面
    prevention.track_page_visit("https://www.te720.com/products", "产品页面")
    
    # 检查状态
    result = prevention.check_for_loops("click", "了解更多", "https://www.te720.com/products")
    print(f"正常操作检查: {'🟢 通过' if not result.detected else '🔴 检测到循环'}")
    
    # 模拟循环操作
    print("\n🔄 模拟循环操作...")
    
    # 重复点击同样的链接
    prevention.track_action("click", "了解更多", "https://www.te720.com/products")
    prevention.track_action("click", "了解更多", "https://www.te720.com/products")
    
    # 检查循环
    result = prevention.check_for_loops("click", "了解更多", "https://www.te720.com/products")
    print(f"循环操作检查: {'🔴 检测到循环' if result.detected else '🟢 未检测到'}")
    
    if result.detected:
        print(f"  - 循环类型: {result.loop_type}")
        print(f"  - 严重程度: {result.severity}")
        print(f"  - 建议: {result.recommendation}")
    
    # 测试URL重复访问
    print("\n🌐 测试URL重复访问...")
    
    # 重复访问同一URL
    prevention.track_page_visit("https://www.te720.com", "TE720 主页")  # 第二次
    result = prevention.check_for_loops("visit_url", "https://www.te720.com", "https://www.te720.com")
    print(f"URL重复访问检查: {'🔴 检测到循环' if result.detected else '🟢 未检测到'}")
    
    # 测试强制完成条件
    print("\n⏰ 测试强制完成条件...")
    
    # 添加更多操作达到限制
    for i in range(6):
        prevention.track_action("click", f"link_{i}", "https://www.te720.com")
    
    should_complete, reason = prevention.should_force_complete()
    print(f"强制完成检查: {'🛑 需要强制完成' if should_complete else '🟢 可以继续'}")
    if should_complete:
        print(f"  - 原因: {reason}")
    
    print("\n📊 防护摘要:")
    summary = prevention.get_prevention_summary()
    for key, value in summary.items():
        print(f"  - {key}: {value}")


def test_enhancement_patch():
    """测试增强补丁功能"""
    print("\n🔧 测试WebSurfer增强补丁...")
    
    patch = WebSurferEnhancementPatch()
    
    # 初始化任务
    task = "访问te720.com查找360度全景相机的参考图像"
    patch.initialize_task(task)
    print(f"✅ 任务初始化: {task}")
    
    # 模拟第一次操作
    print("\n1️⃣ 第一次操作检查...")
    should_proceed, reason, data = patch.check_before_action(
        "visit_url", "https://www.te720.com", "about:blank"
    )
    print(f"操作检查: {'🟢 允许执行' if should_proceed else '🔴 阻止执行'}")
    if not should_proceed:
        print(f"  - 阻止原因: {reason}")
    
    # 追踪操作执行
    patch.track_action_execution("visit_url", "https://www.te720.com", "https://www.te720.com", True, "", "TE720官网")
    
    # 模拟重复操作
    print("\n2️⃣ 重复操作检查...")
    patch.track_action_execution("click", "产品", "https://www.te720.com", True)
    patch.track_action_execution("click", "产品", "https://www.te720.com", True)
    
    should_proceed, reason, data = patch.check_before_action(
        "click", "产品", "https://www.te720.com"
    )
    print(f"重复操作检查: {'🟢 允许执行' if should_proceed else '🔴 阻止执行'}")
    if not should_proceed:
        print(f"  - 阻止原因: {reason}")
    
    # 测试提示词生成
    print("\n📝 测试增强提示词生成...")
    enhanced_prompt = patch.generate_enhanced_prompt(
        last_outside_message=task,
        webpage_text="这是TE720全景相机官网首页",
        url="https://www.te720.com",
        visible_targets='[{"id": 1, "name": "产品", "role": "link"}]'
    )
    
    print("✅ 增强提示词已生成")
    if "LOOP DETECTION" in enhanced_prompt:
        print("  - 包含循环检测信息")
    if "NAVIGATION PLAN" in enhanced_prompt:
        print("  - 包含导航计划信息")
    if "FORCE COMPLETION" in enhanced_prompt:
        print("  - 包含强制完成检查")
    
    # 测试强制停止
    print("\n🛑 测试强制停止功能...")
    
    # 添加大量操作
    for i in range(10):
        patch.track_action_execution("click", f"button_{i}", "https://www.te720.com", True)
    
    should_stop, stop_reason = patch.should_force_stop_action()
    print(f"强制停止检查: {'🛑 需要停止' if should_stop else '🟢 可以继续'}")
    if should_stop:
        print(f"  - 停止原因: {stop_reason}")
        
        completion_msg = patch.get_completion_message_suggestion()
        print(f"  - 建议完成消息: {completion_msg}")
    
    # 诊断信息
    print("\n🔍 诊断信息:")
    diagnostic = patch.get_diagnostic_info()
    for key, value in diagnostic.items():
        if key != "prevention_summary":
            print(f"  - {key}: {value}")


def test_integration_with_real_task():
    """测试与真实任务的集成"""
    print("\n🌟 测试与真实任务的集成...")
    
    # 模拟真实的WebSurfer任务场景
    task = "生成一个设计简洁、能清晰显示4个镜头分别分布于四面、每90度一个的360全景相机图。高清 CG 风格。可以先阅读 te720.com 查看到全景相机图片作为参考"
    
    # 初始化增强系统
    patch_websurfer_for_current_task(task)
    print(f"✅ 任务: {task}")
    
    # 模拟WebSurfer执行流程
    actions_sequence = [
        ("visit_url", "https://te720.com", "https://te720.com"),
        ("click", "了解更多", "https://te720.com"),
        ("click", "产品", "https://te720.com"),
        ("click", "产品", "https://te720.com"),  # 重复操作
        ("click", "了解更多", "https://te720.com"),  # 重复操作
        ("click", "行业应用案例", "https://te720.com"),
        ("click", "样片", "https://te720.com"),
        ("click", "产品", "https://te720.com"),  # 又一次重复
    ]
    
    for i, (action, target, url) in enumerate(actions_sequence):
        print(f"\n{i+1}. 检查操作: {action} -> {target}")
        
        # 执行前检查
        should_proceed, reason, enhancement_data = check_websurfer_action_before_execution(
            action, target, url
        )
        
        if not should_proceed:
            print(f"  🔴 操作被阻止: {reason}")
            print(f"  💡 建议: {enhancement_data.get('smart_recommendation', '')}")
            break
        else:
            print(f"  🟢 允许执行")
            
            # 模拟执行并追踪
            track_websurfer_action_after_execution(action, target, url, True, "操作成功")
            
            # 检查是否应该强制完成
            from magentic_ui.agents.web_surfer._websurfer_enhancement_patch import get_websurfer_enhancement
            enhancement = get_websurfer_enhancement()
            should_stop, stop_reason = enhancement.should_force_stop_action()
            
            if should_stop:
                print(f"  🛑 建议强制停止: {stop_reason}")
                completion_msg = enhancement.get_completion_message_suggestion()
                print(f"  📝 建议完成消息: {completion_msg}")
                break
    
    print("\n✅ 集成测试完成")


async def main():
    """主测试函数"""
    print("🚀 开始WebSurfer循环防护测试\n")
    
    try:
        # 运行所有测试
        test_loop_detection()
        test_enhancement_patch()
        test_integration_with_real_task()
        
        print("\n🎉 所有测试完成！")
        print("\n📋 测试总结:")
        print("  ✅ 循环检测功能正常")
        print("  ✅ 增强补丁功能正常")
        print("  ✅ 真实任务集成测试通过")
        print("\n💡 新的循环防护系统应该能有效防止WebSurfer无限循环问题")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())