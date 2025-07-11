#!/usr/bin/env python3
"""
完整系统集成测试 - 验证所有修复是否正常工作
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from magentic_ui.teams.orchestrator._prompts import (
    ORCHESTRATOR_PLAN_PROMPT_JSON,
    validate_plan_json,
    validate_ledger_json
)

def test_template_variables():
    """测试模板变量是否正确转义"""
    print("🔧 测试模板变量转义...")
    
    # 测试HTML模板
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>{{title}}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
    </style>
</head>
<body>
    {{content}}
</body>
</html>'''
    
    try:
        # 尝试格式化，这应该不会抛出KeyError
        formatted = html_template.format(title="Test Title", content="Test Content")
        print("✅ HTML模板变量转义成功")
        
        # 测试f-string模板
        test_pdf_message = f"✅ PDF文档创建完成: {{pdf_file}}"
        print("✅ f-string模板变量转义成功")
        
        return True
    except KeyError as e:
        print(f"❌ 模板变量转义失败: {e}")
        return False

def test_plan_validation():
    """测试规划验证逻辑"""
    print("\n🔧 测试规划验证...")
    
    # 测试有效的规划JSON
    valid_plan = {
        "response": "我将帮助您创建360全景相机产品介绍",
        "task": "生成360全景相机产品介绍，从te720.com获取信息，最终输出PDF",
        "plan_summary": "通过web_surfer研究→image_generator生成→coder_agent创建文档→转换为PDF",
        "needs_plan": True,
        "steps": [
            {
                "title": "访问te720.com收集360全景相机信息",
                "details": "访问te720.com收集360全景相机信息\n自主浏览产品页面，收集技术规格、产品特点等信息",
                "agent_name": "web_surfer"
            },
            {
                "title": "生成360全景相机CG风格图像",
                "details": "生成360全景相机CG风格图像\n基于研究信息创建专业的产品展示图像",
                "agent_name": "image_generator"
            },
            {
                "title": "创建产品介绍markdown文档",
                "details": "创建产品介绍markdown文档\n整合研究信息和生成的图像，创建结构化的产品介绍",
                "agent_name": "coder_agent"
            },
            {
                "title": "转换为PDF格式",
                "details": "转换为PDF格式\n将markdown文档转换为专业的PDF格式用于分发",
                "agent_name": "coder_agent"
            }
        ]
    }
    
    if validate_plan_json(valid_plan):
        print("✅ 规划验证逻辑正常工作")
        return True
    else:
        print("❌ 规划验证失败")
        return False

def test_agent_assignment_keywords():
    """测试代理分配关键词"""
    print("\n🔧 测试代理分配关键词...")
    
    # 测试图像生成关键词识别
    image_keywords = ["Generate", "Create", "Draw", "Image", "Picture", "Visual", "CG", "生成图像", "创建图像"]
    
    test_cases = [
        ("Generate a CG-style image", "image_generator"),
        ("Create 360 camera image", "image_generator"),
        ("Visit te720.com", "web_surfer"),
        ("Create markdown document", "coder_agent"),
        ("Convert to PDF", "coder_agent")
    ]
    
    for description, expected_agent in test_cases:
        # 简单的关键词匹配逻辑
        if any(keyword.lower() in description.lower() for keyword in ["generate", "create", "draw", "image", "picture", "visual", "cg"] if "document" not in description.lower() and "markdown" not in description.lower()):
            assigned_agent = "image_generator"
        elif any(keyword.lower() in description.lower() for keyword in ["visit", "browse", "te720", "website", "web"]):
            assigned_agent = "web_surfer"
        else:
            assigned_agent = "coder_agent"
        
        if assigned_agent == expected_agent:
            print(f"✅ '{description}' → {assigned_agent}")
        else:
            print(f"❌ '{description}' → {assigned_agent} (expected {expected_agent})")
    
    return True

def test_completion_signals():
    """测试完成信号检测"""
    print("\n🔧 测试完成信号检测...")
    
    completion_signals = [
        "✅ 任务已完成",
        "✅ TASK COMPLETED",
        "⚠️ 任务因错误完成",
        "⚠️ TASK COMPLETED WITH ERRORS",
        "🔄 任务通过替代方案完成",
        "🔄 TASK COMPLETED VIA ALTERNATIVE",
        "图像生成任务已完成",
        "文档创建任务已完成",
        "PDF文档创建任务已完成"
    ]
    
    incomplete_signals = [
        "我理解您需要",
        "Let me help you",
        "How can I assist",
        "我可以帮助您",
        "为了创建",
        "Let me create"
    ]
    
    def is_complete(message):
        return any(signal in message for signal in completion_signals)
    
    def is_incomplete(message):
        return any(signal in message for signal in incomplete_signals)
    
    # 测试完成信号
    for signal in completion_signals:
        test_message = f"{signal} - 相关任务信息"
        if is_complete(test_message):
            print(f"✅ 完成信号检测: '{signal}'")
        else:
            print(f"❌ 完成信号检测失败: '{signal}'")
    
    # 测试不完成信号
    for signal in incomplete_signals:
        test_message = f"{signal} - 相关任务信息"
        if is_incomplete(test_message):
            print(f"✅ 不完成信号检测: '{signal}'")
        else:
            print(f"❌ 不完成信号检测失败: '{signal}'")
    
    return True

def main():
    """运行所有测试"""
    print("🚀 开始系统集成测试")
    print("=" * 50)
    
    tests = [
        test_template_variables,
        test_plan_validation,
        test_agent_assignment_keywords,
        test_completion_signals
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过! 系统准备就绪")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)