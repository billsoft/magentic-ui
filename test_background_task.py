#!/usr/bin/env python3
"""
后台任务功能测试脚本
测试前后端解耦功能：
1. 任务在WebSocket断开后继续运行
2. 重连机制正常工作
3. 状态持久化正确
"""

import asyncio
import json
import time
import requests
import websockets
from typing import Optional, Dict, Any, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackgroundTaskTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.user_email = "test@example.com"
        self.session_id: Optional[int] = None
        self.run_id: Optional[str] = None
        
    def create_test_session(self) -> int:
        """创建测试会话"""
        session_data = {
            "name": f"Background Task Test - {int(time.time())}",
            "team_id": None
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/sessions",
                json=session_data,
                params={"user_email": self.user_email},
                timeout=30
            )
            
            if response.status_code == 200:
                session = response.json()
                session_id = session.get('id')
                if session_id:
                    logger.info(f"Created test session: {session_id}")
                    return session_id
                else:
                    raise Exception("Session created but no ID returned")
            else:
                raise Exception(f"Failed to create session: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            raise Exception(f"Network error creating session: {e}")
    
    def start_long_running_task(self, session_id: int) -> str:
        """启动一个长时间运行的任务"""
        task_data = {
            "task": "请帮我分析一下Python编程的发展历史，并生成一个详细的报告。这个任务可能需要一些时间来完成。请同时创建一些图表来可视化Python的发展历程。",
            "team_id": None
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/sessions/{session_id}/run",
                json=task_data,
                params={"user_email": self.user_email},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                run_id = result.get('run_id')
                if run_id:
                    logger.info(f"Started long-running task: {run_id}")
                    return str(run_id)
                else:
                    raise Exception("Task started but no run_id returned")
            else:
                raise Exception(f"Failed to start task: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            raise Exception(f"Network error starting task: {e}")
    
    async def connect_and_disconnect(self, session_id: int, run_id: str) -> bool:
        """连接WebSocket然后断开，模拟用户关闭浏览器"""
        ws_url = f"{self.ws_url}/api/ws/{session_id}"
        
        try:
            async with websockets.connect(ws_url, timeout=10) as websocket:
                logger.info("Connected to WebSocket")
                
                # 发送重连消息
                reconnect_msg = {
                    "type": "reconnect", 
                    "run_id": run_id
                }
                await websocket.send(json.dumps(reconnect_msg))
                logger.info("Sent reconnect message")
                
                # 接收一些消息确认连接
                message_count = 0
                connection_confirmed = False
                
                while message_count < 5:  # 增加消息接收次数
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        logger.info(f"Received message {message_count + 1}: {msg_type}")
                        
                        # 检查是否收到任务相关的消息
                        if msg_type in ['message', 'system', 'result']:
                            connection_confirmed = True
                            
                        message_count += 1
                    except asyncio.TimeoutError:
                        logger.info("No more messages received")
                        break
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON message")
                        message_count += 1
                
                logger.info(f"Disconnecting WebSocket (received {message_count} messages)")
                return connection_confirmed
                
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def check_task_status(self, session_id: int) -> Dict[str, Any]:
        """检查任务状态"""
        try:
            response = requests.get(
                f"{self.base_url}/api/sessions/{session_id}/runs",
                timeout=10
            )
            
            if response.status_code == 200:
                runs = response.json()
                if isinstance(runs, list):
                    active_runs = [
                        run for run in runs 
                        if isinstance(run, dict) and run.get('status') in ['active', 'awaiting_input', 'paused']
                    ]
                    logger.info(f"Found {len(active_runs)} active runs out of {len(runs)} total")
                    return {
                        'total_runs': len(runs),
                        'active_runs': len(active_runs),
                        'runs': runs,
                        'success': True
                    }
                else:
                    logger.warning(f"Unexpected response format: {type(runs)}")
                    return {'success': False, 'error': 'Invalid response format'}
            else:
                logger.error(f"Failed to get runs: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Network error checking status: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_reconnect(self, session_id: int, run_id: str) -> bool:
        """测试重连功能"""
        ws_url = f"{self.ws_url}/api/ws/{session_id}"
        
        try:
            async with websockets.connect(ws_url, timeout=10) as websocket:
                logger.info("Reconnected to WebSocket")
                
                # 发送重连消息
                reconnect_msg = {
                    "type": "reconnect",
                    "run_id": run_id
                }
                await websocket.send(json.dumps(reconnect_msg))
                
                # 等待重连确认
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Reconnect response: {msg_type}")
                    
                    # 认为收到任何消息都表示重连成功
                    return True
                    
                except asyncio.TimeoutError:
                    logger.warning("No response to reconnect request within timeout")
                    return False
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON on reconnect")
                    return False
                    
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"Reconnect test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected reconnect error: {e}")
            return False
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """运行完整的测试流程"""
        logger.info("=== 开始后台任务功能测试 ===")
        
        test_results = {
            'session_id': None,
            'run_id': None,
            'background_persistence': False,
            'reconnect_success': False,
            'connection_success': False,
            'final_status': {},
            'error': None
        }
        
        try:
            # 1. 创建测试会话
            logger.info("Step 1: Creating test session...")
            self.session_id = self.create_test_session()
            test_results['session_id'] = self.session_id
            
            # 2. 启动长时间运行的任务
            logger.info("Step 2: Starting long-running task...")
            self.run_id = self.start_long_running_task(self.session_id)
            test_results['run_id'] = self.run_id
            
            # 3. 连接WebSocket然后断开
            logger.info("Step 3: Connect and disconnect WebSocket...")
            connection_success = await self.connect_and_disconnect(self.session_id, self.run_id)
            test_results['connection_success'] = connection_success
            
            # 4. 等待一段时间让任务在后台运行
            logger.info("Step 4: Waiting for task to run in background...")
            await asyncio.sleep(15)  # 增加等待时间
            
            # 5. 检查任务状态
            logger.info("Step 5: Checking task status...")
            status_result = self.check_task_status(self.session_id)
            
            if status_result.get('success', False):
                active_count = status_result.get('active_runs', 0)
                background_persistence = active_count > 0
                test_results['background_persistence'] = background_persistence
                
                if background_persistence:
                    logger.info("✅ Background task persistence test PASSED")
                else:
                    logger.warning("❌ Background task persistence test FAILED")
            else:
                logger.error(f"Failed to check status: {status_result.get('error', 'Unknown error')}")
            
            # 6. 测试重连功能
            logger.info("Step 6: Testing reconnect functionality...")
            reconnect_success = await self.test_reconnect(self.session_id, self.run_id)
            test_results['reconnect_success'] = reconnect_success
            
            if reconnect_success:
                logger.info("✅ Reconnect test PASSED")
            else:
                logger.warning("❌ Reconnect test FAILED")
            
            # 7. 最终状态检查
            logger.info("Step 7: Final status check...")
            final_status = self.check_task_status(self.session_id)
            test_results['final_status'] = final_status
            
            logger.info("=== 测试完成 ===")
            logger.info(f"Session ID: {self.session_id}")
            logger.info(f"Run ID: {self.run_id}")
            
            if final_status.get('success', False):
                logger.info(f"Total runs: {final_status.get('total_runs', 0)}")
                logger.info(f"Active runs: {final_status.get('active_runs', 0)}")
            
            return test_results
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            test_results['error'] = str(e)
            return test_results

def print_test_results(result: Dict[str, Any]) -> None:
    """打印测试结果"""
    print("\n" + "="*60)
    print("🧪 后台任务功能测试结果")
    print("="*60)
    
    if result.get('error'):
        print(f"❌ 测试失败: {result['error']}")
        return
    
    # 基本信息
    print(f"📋 会话ID: {result.get('session_id', 'N/A')}")
    print(f"🔄 运行ID: {result.get('run_id', 'N/A')}")
    print()
    
    # 测试项目结果
    print("📊 测试项目结果:")
    print("-" * 40)
    
    connection_success = result.get('connection_success', False)
    print(f"🔗 WebSocket连接: {'✅ 成功' if connection_success else '❌ 失败'}")
    
    background_persistence = result.get('background_persistence', False)
    print(f"🔧 后台任务持续: {'✅ 通过' if background_persistence else '❌ 失败'}")
    
    reconnect_success = result.get('reconnect_success', False)
    print(f"🔄 重连功能: {'✅ 通过' if reconnect_success else '❌ 失败'}")
    
    # 最终状态
    final_status = result.get('final_status', {})
    if final_status.get('success', False):
        total_runs = final_status.get('total_runs', 0)
        active_runs = final_status.get('active_runs', 0)
        print(f"📈 总运行数: {total_runs}")
        print(f"⚡ 活跃任务数: {active_runs}")
    
    print()
    
    # 总结
    passed_tests = sum([
        connection_success,
        background_persistence,
        reconnect_success
    ])
    
    print(f"🎯 测试通过率: {passed_tests}/3 ({passed_tests/3*100:.1f}%)")
    
    if passed_tests == 3:
        print("🎉 所有测试通过！前后端解耦功能正常工作。")
    elif passed_tests >= 2:
        print("⚠️ 大部分测试通过，但仍有改进空间。")
    else:
        print("💥 多项测试失败，需要检查后台任务实现。")
    
    print("="*60)

async def main():
    """主函数"""
    print("🚀 启动后台任务功能测试...")
    
    tester = BackgroundTaskTester()
    result = await tester.run_complete_test()
    
    print_test_results(result)

if __name__ == "__main__":
    asyncio.run(main()) 