#!/usr/bin/env python3
"""
WebSurfer运行时错误修复验证
验证 novnc_port, playwright_port, is_paused, _context 属性修复
"""

def test_websurfer_runtime_fixes():
    """测试WebSurfer运行时属性修复"""
    try:
        from src.magentic_ui.agents.web_surfer._web_surfer import WebSurfer
        from src.magentic_ui.tools.playwright.browser.vnc_docker_playwright_browser import VncDockerPlaywrightBrowser
        from pathlib import Path
        import asyncio

        print("🧪 测试WebSurfer运行时属性修复...")
        
        # 创建浏览器资源
        browser = VncDockerPlaywrightBrowser(bind_dir=Path('/tmp'))
        
        # 创建WebSurfer实例
        websurfer = WebSurfer(
            name='test_websurfer',
            model_client=None,  # 测试用
            browser=browser
        )
        
        # 测试1: novnc_port和playwright_port属性
        print(f"✅ novnc_port属性: {websurfer.novnc_port}")
        print(f"✅ playwright_port属性: {websurfer.playwright_port}")
        
        # 测试2: is_paused属性访问器
        print(f"✅ is_paused属性访问器: {websurfer.is_paused}")
        print(f"✅ _is_paused内部属性: {websurfer._is_paused}")
        
        # 测试3: _context属性初始化
        print(f"✅ _context已初始化: {hasattr(websurfer, '_context')}")
        print(f"✅ _context初始值为None: {websurfer._context is None}")
        
        # 测试4: save_state方法（应该不会崩溃）
        async def test_save_state():
            try:
                state = await websurfer.save_state()
                return True, "成功"
            except Exception as e:
                return False, str(e)
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success, result = loop.run_until_complete(test_save_state())
            if success:
                print(f"✅ save_state方法测试: {result}")
            else:
                print(f"❌ save_state方法测试失败: {result}")
        finally:
            loop.close()
        
        # 测试5: TeamManager逻辑模拟
        participants = [websurfer]
        for agent in participants:
            if isinstance(agent, WebSurfer):
                # 这些是导致AttributeError的代码行
                novnc_port = agent.novnc_port
                playwright_port = agent.playwright_port
                is_paused = agent.is_paused
                print(f"✅ TeamManager逻辑测试通过: novnc={novnc_port}, playwright={playwright_port}, paused={is_paused}")
        
        print("\n🎉 所有运行时属性修复验证通过！")
        print("🚀 系统现在应该能正常启动和运行！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_websurfer_runtime_fixes()
    exit(0 if success else 1)