#!/usr/bin/env python3
"""
后台任务功能测试脚本 - 8081端口
测试前后端解耦功能
"""

import asyncio
import json
import time
import requests
import websockets
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleBackgroundTaskTester:
    def __init__(self):
        self.base_url = "http://localhost:8081"
        self.ws_url = "ws://localhost:8081"
        self.user_email = "test@example.com"
        
    def create_session(self):
        """创建测试会话"""
        session_data = {
            "name": f"Background Test - {int(time.time())}",
            "team_id": None,
            "user_id": self.user_email
        }
        
        response = requests.post(
            f"{self.base_url}/api/sessions/",
            json=session_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') and result.get('data'):
                session_id = result['data'].get('id')
                logger.info(f"✅ 创建会话成功: {session_id}")
                return session_id
            else:
                logger.error(f"❌ 响应格式错误: {result}")
                return None
        else:
            logger.error(f"❌ 创建会话失败: {response.status_code} - {response.text}")
            return None
    
    def create_run(self, session_id):
        """为会话创建run"""
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
            run_id = None
            if result.get('data', {}).get('run_id'):
                run_id = result['data']['run_id']
            elif result.get('run_id'):
                run_id = result['run_id']
                
            logger.info(f"✅ 创建Run成功: {run_id}")
            return run_id
        else:
            logger.error(f"❌ 创建Run失败: {response.status_code} - {response.text}")
            return None
    
    async def start_task_via_websocket(self, run_id):
        """通过WebSocket启动任务"""
        ws_url = f"{self.ws_url}/api/ws/runs/{run_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("✅ WebSocket连接成功")
                
                # 发送启动任务消息 - 改为适合web_surfer的搜索任务
                start_msg = {
                    "type": "start",
                    "task": "请帮我搜索一下OpenAI GPT-4的最新信息，这是一个后台任务测试。",
                    "team_config": {"dummy": "config"},  # 提供非空配置以通过条件检查
                    "settings_config": {}
                }
                await websocket.send(json.dumps(start_msg))
                logger.info("📤 发送启动任务消息")
                
                # 接收初始消息确认任务开始
                message_count = 0
                task_started = False
                
                while message_count < 10:  # 增加等待消息数量
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=8.0)
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')
                        status = data.get('status', 'unknown')
                        logger.info(f"📨 收到消息 {message_count + 1}: {msg_type} (status: {status})")
                        
                        # 检查任务是否开始
                        if msg_type == 'system' and status == 'active':
                            task_started = True
                            logger.info("🎯 任务已开始运行")
                        
                        # 如果收到message类型，说明代理在工作
                        if msg_type == 'message':
                            logger.info("🤖 代理正在处理任务...")
                            
                        # 等待一段时间让任务运行
                        if task_started and message_count >= 3:
                            logger.info("✂️ 提前断开连接测试后台持续")
                            break
                        
                        message_count += 1
                    except asyncio.TimeoutError:
                        logger.info("⏰ 等待消息超时")
                        break
                    except json.JSONDecodeError:
                        logger.warning("⚠️ 收到无效JSON")
                        message_count += 1
                
                logger.info("🔌 断开WebSocket连接（模拟用户关闭浏览器）")
                return task_started
                
        except Exception as e:
            logger.error(f"❌ WebSocket操作失败: {e}")
            return False
    
    async def test_reconnect(self, run_id):
        """测试重连功能"""
        ws_url = f"{self.ws_url}/api/ws/runs/{run_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                logger.info("🔄 尝试重连WebSocket")
                
                # 等待重连确认
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"📨 重连后收到: {msg_type}")
                    return True
                except asyncio.TimeoutError:
                    logger.warning("⏰ 重连后无响应")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 重连测试失败: {e}")
            return False
    
    def check_runs(self, session_id):
        """检查运行状态"""
        response = requests.get(f"{self.base_url}/api/sessions/{session_id}/runs/?user_id={self.user_email}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"📄 运行状态响应: {result}")
            
            # 解析runs数据
            runs = []
            if result.get('data', {}).get('runs'):
                runs = result['data']['runs']
            
            active_runs = [r for r in runs if r.get('status') in ['active', 'awaiting_input', 'paused']]
            logger.info(f"📊 总运行数: {len(runs)}, 活跃运行数: {len(active_runs)}")
            
            # 显示每个运行的详细状态
            for i, run in enumerate(runs):
                logger.info(f"🔍 运行 {i+1}: ID={run.get('id')}, 状态={run.get('status')}")
            
            return len(active_runs) > 0
        else:
            logger.error(f"❌ 检查运行状态失败: {response.status_code} - {response.text}")
            return False
    
    async def run_test(self):
        """运行测试"""
        logger.info("🧪 开始后台任务测试")
        
        # 1. 创建会话
        session_id = self.create_session()
        if not session_id:
            return False
        
        # 2. 创建run
        run_id = self.create_run(session_id)
        if not run_id:
            return False
        
        # 3. 通过WebSocket启动任务
        task_started = await self.start_task_via_websocket(run_id)
        
        # 4. 等待后台运行
        logger.info("⏳ 等待后台任务运行...")
        await asyncio.sleep(10)
        
        # 5. 检查任务状态
        has_active_tasks = self.check_runs(session_id)
        
        # 6. 测试重连
        reconnect_success = await self.test_reconnect(run_id)
        
        logger.info("=" * 60)
        logger.info("📋 测试结果:")
        logger.info(f"🎯 任务启动: {'✅' if task_started else '❌'}")
        logger.info(f"🔄 后台持续: {'✅' if has_active_tasks else '❌'}")
        logger.info(f"🔗 重连功能: {'✅' if reconnect_success else '❌'}")
        logger.info("=" * 60)
        
        return task_started and has_active_tasks and reconnect_success

async def main():
    tester = SimpleBackgroundTaskTester()
    success = await tester.run_test()
    
    if success:
        print("🎉 后台任务测试通过！前后端解耦功能正常工作。")
    else:
        print("❌ 后台任务测试失败，需要检查实现。")

if __name__ == "__main__":
    asyncio.run(main()) 