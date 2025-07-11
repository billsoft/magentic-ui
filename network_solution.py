#!/usr/bin/env python3
"""
🔧 Magentic-UI 网络连接解决方案
自动诊断和修复网络连接问题
"""

import asyncio
import aiohttp
import os
from typing import Dict, Any

class NetworkSolutionManager:
    def __init__(self):
        self.config_files = {
            "stable": "config_stable.yaml",
            "original": "config.yaml"
        }
        
    async def test_api_endpoint(self, base_url: str, api_key: str, timeout: int = 10) -> bool:
        """测试API端点是否可用"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(f"{base_url}/models", headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def diagnose_network(self) -> Dict[str, Any]:
        """诊断网络连接状况"""
        print("🔍 开始网络连接诊断...")
        
        # 获取环境变量
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        results = {
            "openrouter_available": False,
            "openai_available": False,
            "basic_internet": False,
            "recommended_config": "stable"
        }
        
        # 测试基础网络连接
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.google.com", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    results["basic_internet"] = response.status == 200
        except:
            results["basic_internet"] = False
        
        print(f"✅ 基础网络连接: {'正常' if results['basic_internet'] else '异常'}")
        
        # 测试 OpenRouter
        if openrouter_key:
            results["openrouter_available"] = await self.test_api_endpoint(
                "https://openrouter.ai/api/v1", openrouter_key
            )
            print(f"🔗 OpenRouter API: {'可用' if results['openrouter_available'] else '不可用'}")
        else:
            print("⚠️ 未找到 OPENROUTER_API_KEY")
        
        # 测试 OpenAI
        if openai_key:
            results["openai_available"] = await self.test_api_endpoint(
                "https://api.openai.com/v1", openai_key
            )
            print(f"🤖 OpenAI API: {'可用' if results['openai_available'] else '不可用'}")
        else:
            print("⚠️ 未找到 OPENAI_API_KEY")
        
        return results
    
    def create_optimal_config(self, diagnosis: Dict[str, Any]) -> str:
        """根据诊断结果创建最优配置"""
        if diagnosis["openrouter_available"]:
            return self.create_openrouter_config()
        elif diagnosis["openai_available"]:
            return self.create_openai_config()
        else:
            return self.create_offline_config()
    
    def create_openrouter_config(self) -> str:
        """创建OpenRouter配置"""
        return """# 🔧 优化的 OpenRouter 配置
model_config: &client
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: openai/gpt-3.5-turbo
    api_key: $OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
    timeout: 180.0
    max_retries: 8
    model_info:
      vision: false
      function_calling: true
      json_output: false

orchestrator_client: *client
coder_client: *client
web_surfer_client: *client
file_surfer_client: *client
action_guard_client: *client

# 简化配置以提高稳定性
cooperative_planning: true
autonomous_execution: false
max_actions_per_step: 3
multiple_tools_per_call: false
max_turns: 20
approval_policy: auto-conservative
browser_headless: true
action_guard_enabled: false
"""
    
    def create_openai_config(self) -> str:
        """创建OpenAI配置"""
        return """# 🔧 优化的 OpenAI 配置
model_config: &client
  provider: autogen_ext.models.openai.OpenAIChatCompletionClient
  config:
    model: gpt-3.5-turbo
    api_key: $OPENAI_API_KEY
    timeout: 180.0
    max_retries: 8
    model_info:
      vision: false
      function_calling: true
      json_output: false

orchestrator_client: *client
coder_client: *client
web_surfer_client: *client
file_surfer_client: *client
action_guard_client: *client

# 简化配置以提高稳定性
cooperative_planning: true
autonomous_execution: false
max_actions_per_step: 3
multiple_tools_per_call: false
max_turns: 20
approval_policy: auto-conservative
browser_headless: true
action_guard_enabled: false
"""
    
    def create_offline_config(self) -> str:
        """创建离线/本地模型配置"""
        return """# 🔧 离线模式配置 (需要本地Ollama)
model_config: &client
  provider: autogen_ext.models.ollama.OllamaChatCompletionClient
  config:
    model: qwen2.5:14b
    host: http://localhost:11434
    timeout: 300.0
    max_retries: 3
    model_info:
      vision: false
      function_calling: true
      json_output: false

orchestrator_client: *client
coder_client: *client
web_surfer_client: *client
file_surfer_client: *client
action_guard_client: *client

# 离线模式配置
cooperative_planning: true
autonomous_execution: false
max_actions_per_step: 2
multiple_tools_per_call: false
max_turns: 15
approval_policy: auto-conservative
browser_headless: true
action_guard_enabled: false
"""
    
    async def apply_solution(self) -> bool:
        """应用解决方案"""
        print("\n🔧 开始应用网络连接解决方案...")
        
        # 诊断网络
        diagnosis = await self.diagnose_network()
        
        # 创建优化配置
        optimal_config = self.create_optimal_config(diagnosis)
        
        # 保存配置文件
        config_path = "config_optimized.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(optimal_config)
        
        print(f"\n✅ 已创建优化配置文件: {config_path}")
        
        # 给出使用建议
        if diagnosis["openrouter_available"]:
            print("🎯 推荐使用 OpenRouter API (最稳定)")
            print(f"启动命令: python load_env.py --config {config_path} --port 8081")
        elif diagnosis["openai_available"]:
            print("🎯 推荐使用 OpenAI API")
            print(f"启动命令: python load_env.py --config {config_path} --port 8081")
        else:
            print("🎯 推荐使用本地 Ollama 模型")
            print("请先安装 Ollama: https://ollama.ai/")
            print("然后运行: ollama pull qwen2.5:14b")
            print(f"最后启动: python load_env.py --config {config_path} --port 8081")
        
        return True

async def main():
    print("🚀 Magentic-UI 网络连接解决方案")
    print("=" * 50)
    
    manager = NetworkSolutionManager()
    success = await manager.apply_solution()
    
    if success:
        print("\n✅ 解决方案已成功应用!")
        print("🎉 您现在可以使用优化后的配置启动 Magentic-UI")
    else:
        print("\n❌ 解决方案应用失败，请检查网络连接")

if __name__ == "__main__":
    asyncio.run(main()) 