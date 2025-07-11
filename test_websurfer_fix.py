#!/usr/bin/env python3
"""
WebSurfer AttributeError 修复验证测试
"""

def test_websurfer_attributes():
    """测试WebSurfer的novnc_port和playwright_port属性"""
    try:
        from src.magentic_ui.agents import WebSurfer
        from src.magentic_ui.tools.playwright.browser.vnc_docker_playwright_browser import VncDockerPlaywrightBrowser
        from pathlib import Path

        print("🧪 测试WebSurfer属性访问...")
        
        # 创建浏览器资源
        browser = VncDockerPlaywrightBrowser(bind_dir=Path('/tmp'))
        
        # 创建WebSurfer实例
        websurfer = WebSurfer(
            name='test_websurfer',
            model_client=None,  # 测试用
            browser=browser
        )
        
        # 测试属性存在
        assert hasattr(websurfer, 'novnc_port'), "❌ WebSurfer缺少novnc_port属性"
        assert hasattr(websurfer, 'playwright_port'), "❌ WebSurfer缺少playwright_port属性"
        
        # 测试属性值
        novnc_port = websurfer.novnc_port
        playwright_port = websurfer.playwright_port
        
        print(f"✅ novnc_port: {novnc_port}")
        print(f"✅ playwright_port: {playwright_port}")
        
        # 测试TeamManager逻辑
        participants = [websurfer]
        for agent in participants:
            if isinstance(agent, WebSurfer):
                # 这是导致AttributeError的代码行
                port1 = agent.novnc_port
                port2 = agent.playwright_port
                print(f"✅ TeamManager逻辑测试通过: {port1}, {port2}")
        
        print("🎉 所有测试通过！AttributeError已修复！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_websurfer_attributes()
    exit(0 if success else 1)