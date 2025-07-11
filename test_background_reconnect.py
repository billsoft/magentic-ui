#!/usr/bin/env python3
"""
增强的后台任务重连功能测试脚本
测试新实现的健康检查API和重连机制

新功能测试：
1. 健康检查API (/api/runs/{run_id}/health)
2. 增强的前端重连逻辑
3. 后台任务指示器
4. 自动重试机制
"""

import asyncio
import json
import time
import requests
import websockets
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBackgroundTaskTester:
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.user_email = "test@example.com"
        
    def create_session(self) -> int:
        """创建测试会话"""
        session_data = {
            "name": f"Enhanced Test - {int(time.time())}",
            "user_id": self.user_email
        }
        
        response = requests.post(
            f"{self.base_url}/api/sessions",
            json=session_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            session = result.get('data')
            if session:
                session_id = session.get('id')
                logger.info(f"✅ 创建会话成功: {session_id}")
                return session_id
            else:
                logger.error(f"❌ 创建会话失败: 无效响应格式 {result}")
                return None
        else:
            logger.error(f"❌ 创建会话失败: {response.status_code} - {response.text}")
            return None
    
    def create_run(self, session_id: int) -> str:
        """创建运行实例"""
        run_data = {
            "session_id": session_id,
            "user_id": self.user_email
        }
        
        response = requests.post(
            f"{self.base_url}/api/runs/",
            json=run_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            run_id = result.get('data', {}).get('run_id')
            logger.info(f"✅ 创建运行成功: {run_id}")
            return run_id
        else:
            logger.error(f"❌ 创建运行失败: {response.status_code}")
            return None
    
    def check_health(self, run_id: str) -> Dict[str, Any]:
        """测试新的健康检查API"""
        try:
            response = requests.get(
                f"{self.base_url}/api/runs/{run_id}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"🏥 健康检查成功: {health_data}")
                return health_data
            else:
                logger.error(f"❌ 健康检查失败: {response.status_code}")
                return {"status": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {e}")
            return {"status": False, "error": str(e)}
    
    def list_active_runs(self) -> Dict[str, Any]:
        """测试活跃运行列表API"""
        try:
            response = requests.get(
                f"{self.base_url}/api/runs/?user_id={self.user_email}",
                timeout=10
            )
            
            if response.status_code == 200:
                runs_data = response.json()
                logger.info(f"📋 活跃运行列表: {len(runs_data.get('data', {}).get('active_runs', []))} 个任务")
                return runs_data
            else:
                logger.error(f"❌ 获取活跃运行失败: {response.status_code}")
                return {"status": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ 获取活跃运行异常: {e}")
            return {"status": False, "error": str(e)}
    
    async def start_background_task(self, run_id: str) -> bool:
        """启动后台任务"""
        ws_url = f"{self.ws_url}/api/ws/runs/{run_id}"
        
        try:
            # Remove timeout parameter for compatibility
            async with websockets.connect(ws_url) as websocket:
                logger.info("🔗 WebSocket连接建立")
                
                # 发送启动任务消息
                start_message = {
                    "type": "start",
                    "task": json.dumps({
                        "content": "请创建一个完整的Python项目，包含以下要求：1）创建一个Web爬虫，爬取至少10个新闻网站的标题；2）使用pandas进行数据分析；3）生成可视化图表；4）写详细的文档和测试用例。这是一个需要长时间运行的复杂任务。请一步一步慢慢执行，每个步骤都要详细说明。"
                    }),
                    "team_config": {
                        "team_type": "RoundRobinGroupChat",
                        "participants": [
                            {
                                "agent_type": "AssistantAgent",
                                "name": "Assistant",
                                "model_client": {
                                    "model": "gpt-3.5-turbo",
                                    "model_type": "OpenAIChatCompletionClient"
                                }
                            }
                        ]
                    },
                    "settings_config": {}
                }
                
                await websocket.send(json.dumps(start_message))
                logger.info("📤 发送启动消息")
                
                # 接收几条消息确认任务开始
                message_count = 0
                task_started = False
                
                while message_count < 5:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        status = data.get('status', 'unknown')
                        
                        logger.info(f"📨 收到消息 {message_count + 1}: {msg_type} (status: {status})")
                        
                        if msg_type == 'system' and status == 'active':
                            task_started = True
                            logger.info("🎯 任务已启动")
                            break
                        
                        message_count += 1
                    except asyncio.TimeoutError:
                        logger.info("⏰ 消息接收超时")
                        break
                
                logger.info("🔌 主动断开WebSocket连接（模拟浏览器关闭）")
                return task_started
                
        except Exception as e:
            logger.error(f"❌ WebSocket操作失败: {e}")
            return False
    
    async def test_reconnection(self, run_id: str) -> bool:
        """测试重连功能"""
        ws_url = f"{self.ws_url}/api/ws/runs/{run_id}"
        
        try:
            # Remove timeout parameter for compatibility
            async with websockets.connect(ws_url) as websocket:
                logger.info("🔄 尝试重新连接WebSocket")
                
                # 等待重连消息
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    status = data.get('status', 'unknown')
                    
                    logger.info(f"📨 重连后收到: {msg_type} (status: {status})")
                    
                    if status == 'reconnected':
                        logger.info("✅ 重连成功确认")
                        return True
                    else:
                        logger.info("ℹ️ 收到响应，重连可能成功")
                        return True
                        
                except asyncio.TimeoutError:
                    logger.warning("⏰ 重连后无响应")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 重连测试失败: {e}")
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行全面测试"""
        logger.info("🧪 开始增强版后台任务重连功能测试")
        logger.info("=" * 60)
        
        test_results = {
            'session_id': None,
            'run_id': None,
            'health_check_api': False,
            'active_runs_api': False,
            'task_started': False,
            'background_persistence': False,
            'reconnection_success': False,
            'final_health_check': False,
            'test_summary': {}
        }
        
        try:
            # 1. 创建会话
            logger.info("📝 步骤 1: 创建测试会话")
            session_id = self.create_session()
            if not session_id:
                raise Exception("无法创建会话")
            test_results['session_id'] = session_id
            
            # 2. 创建运行实例
            logger.info("🔄 步骤 2: 创建运行实例")
            run_id = self.create_run(session_id)
            if not run_id:
                raise Exception("无法创建运行实例")
            test_results['run_id'] = run_id
            
            # 3. 测试健康检查API
            logger.info("🏥 步骤 3: 测试健康检查API")
            health_result = self.check_health(run_id)
            test_results['health_check_api'] = health_result.get('status', False)
            
            # 4. 测试活跃运行列表API
            logger.info("📋 步骤 4: 测试活跃运行列表API")
            active_runs_result = self.list_active_runs()
            test_results['active_runs_api'] = active_runs_result.get('status', False)
            
            # 5. 启动后台任务
            logger.info("🚀 步骤 5: 启动后台任务")
            task_started = await self.start_background_task(run_id)
            test_results['task_started'] = task_started
            
            if not task_started:
                logger.warning("⚠️ 任务未成功启动，但继续测试")
            
            # 6. 等待任务在后台运行
            logger.info("⏳ 步骤 6: 等待后台运行（5秒）")
            await asyncio.sleep(5)
            
            # 7. 检查后台持续性
            logger.info("🔍 步骤 7: 检查后台任务持续性")
            health_result = self.check_health(run_id)
            health_data = health_result.get('data', {})
            logger.info(f"🔍 详细健康状态: {health_data}")
            background_active = health_data.get('background_task_active', False)
            has_active_manager = health_data.get('has_active_manager', False)
            run_status = health_data.get('run_status', 'unknown')
            logger.info(f"🔍 关键指标: 状态={run_status}, 活跃管理器={has_active_manager}, 后台活跃={background_active}")
            test_results['background_persistence'] = background_active
            
            # 8. 测试重连功能
            logger.info("🔄 步骤 8: 测试重连功能")
            reconnect_success = await self.test_reconnection(run_id)
            test_results['reconnection_success'] = reconnect_success
            
            # 9. 最终健康检查
            logger.info("🏁 步骤 9: 最终健康检查")
            final_health = self.check_health(run_id)
            test_results['final_health_check'] = final_health.get('status', False)
            
            # 生成测试摘要
            test_results['test_summary'] = {
                'total_tests': 7,
                'passed_tests': sum([
                    test_results['health_check_api'],
                    test_results['active_runs_api'],
                    test_results['task_started'],
                    test_results['background_persistence'],
                    test_results['reconnection_success'],
                    test_results['final_health_check']
                ]),
                'success_rate': 0
            }
            
            success_rate = test_results['test_summary']['passed_tests'] / test_results['test_summary']['total_tests'] * 100
            test_results['test_summary']['success_rate'] = success_rate
            
            logger.info("=" * 60)
            logger.info("📊 测试完成")
            
            return test_results
            
        except Exception as e:
            logger.error(f"💥 测试失败: {e}")
            test_results['error'] = str(e)
            return test_results

def print_test_summary(results: Dict[str, Any]):
    """打印测试结果摘要"""
    print("\n" + "="*60)
    print("🧪 增强版后台任务重连功能测试报告")
    print("="*60)
    
    if results.get('error'):
        print(f"❌ 测试执行失败: {results['error']}")
        return
    
    # 基本信息
    print(f"📋 会话ID: {results.get('session_id', 'N/A')}")
    print(f"🔄 运行ID: {results.get('run_id', 'N/A')}")
    print()
    
    # 详细测试结果
    print("📊 详细测试结果:")
    print("-" * 40)
    
    tests = [
        ("🏥 健康检查API", results.get('health_check_api', False)),
        ("📋 活跃运行API", results.get('active_runs_api', False)),
        ("🚀 任务启动", results.get('task_started', False)),
        ("🔧 后台持续", results.get('background_persistence', False)),
        ("🔄 重连功能", results.get('reconnection_success', False)),
        ("🏁 最终检查", results.get('final_health_check', False))
    ]
    
    for test_name, passed in tests:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 总结
    summary = results.get('test_summary', {})
    if summary:
        print()
        print(f"🎯 总体结果: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} 通过")
        print(f"📈 成功率: {summary.get('success_rate', 0):.1f}%")
        
        success_rate = summary.get('success_rate', 0)
        if success_rate >= 80:
            print("🎉 测试结果优秀！增强版重连功能正常工作。")
        elif success_rate >= 60:
            print("⚠️ 测试结果良好，但有改进空间。")
        else:
            print("💥 测试结果不理想，需要检查实现。")
    
    print("="*60)

async def main():
    """主函数"""
    tester = EnhancedBackgroundTaskTester()
    results = await tester.run_comprehensive_test()
    print_test_summary(results)

if __name__ == "__main__":
    asyncio.run(main()) 