"""
增强工作流程测试脚本
"""

import asyncio
import os
import tempfile
from pathlib import Path
from loguru import logger
import sys

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from magentic_ui.agents._integrated_workflow_manager import IntegratedWorkflowManager
from magentic_ui.agents._enhanced_workflow_coordinator import EnhancedWorkflowCoordinator
from magentic_ui.agents._enhanced_material_manager import EnhancedMaterialManager
from magentic_ui.types import Plan, PlanStep

async def test_material_manager():
    """测试素材管理器"""
    logger.info("🧪 测试素材管理器")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = EnhancedMaterialManager(Path(temp_dir))
        
        # 测试存储文本素材
        text_content = "这是一个测试文档\n\n## 标题\n\n内容测试"
        material_id = await manager.store_text(
            content=text_content,
            step_index=0,
            agent_name="test_agent",
            type="markdown",
            filename="test.md"
        )
        
        logger.info(f"✅ 文本素材已存储: {material_id}")
        
        # 测试获取素材
        material = await manager.get_material(material_id)
        assert material is not None
        assert material.type == "markdown"
        
        # 测试获取素材内容
        content = await manager.get_material_content(material_id)
        assert content == text_content
        
        logger.info("✅ 素材管理器测试通过")

async def test_workflow_coordinator():
    """测试工作流程协调器"""
    logger.info("🧪 测试工作流程协调器")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        coordinator = EnhancedWorkflowCoordinator(Path(temp_dir))
        
        # 创建测试计划
        plan = Plan(
            task="测试任务",
            steps=[
                PlanStep(
                    title="步骤1",
                    details="测试步骤1的详情",
                    agent_name="test_agent1"
                ),
                PlanStep(
                    title="步骤2",
                    details="测试步骤2的详情",
                    agent_name="test_agent2"
                )
            ]
        )
        
        # 初始化工作流程
        coordinator.initialize_workflow(plan)
        
        # 测试获取当前步骤
        current_step = coordinator.get_current_step()
        assert current_step is not None
        assert current_step.index == 0
        
        # 测试开始步骤
        coordinator.start_step()
        assert current_step.status == "in_progress"
        
        # 测试完成步骤
        coordinator.complete_step(result="步骤1完成")
        assert current_step.status == "completed"
        
        # 测试移动到下一步
        next_step = coordinator.get_current_step()
        assert next_step is not None
        assert next_step.index == 1
        
        logger.info("✅ 工作流程协调器测试通过")

async def test_message_analysis():
    """测试消息分析功能"""
    logger.info("🧪 测试消息分析")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        coordinator = EnhancedWorkflowCoordinator(Path(temp_dir))
        
        # 测试不同类型的消息
        test_messages = [
            ("✅ 当前步骤已完成", True, False),
            ("任务完成了", True, False),
            ("整个任务已完成", False, True),
            ("步骤失败", False, False),
            ("生成了图像", False, False),
        ]
        
        for message, expected_step, expected_task in test_messages:
            analysis = coordinator.analyze_agent_message(message, "test_agent")
            assert analysis['step_completed'] == expected_step
            assert analysis['task_completed'] == expected_task
            
        logger.info("✅ 消息分析测试通过")

def test_workflow_manager_initialization():
    """测试工作流程管理器初始化"""
    logger.info("🧪 测试工作流程管理器初始化")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = IntegratedWorkflowManager(Path(temp_dir), {})
        
        # 测试基本属性
        assert manager.work_dir == Path(temp_dir)
        assert manager.coordinator is not None
        assert manager.material_manager is not None
        assert len(manager.enhanced_agents) == 0
        
        logger.info("✅ 工作流程管理器初始化测试通过")

async def test_complete_workflow():
    """测试完整的工作流程"""
    logger.info("🧪 测试完整工作流程")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = IntegratedWorkflowManager(Path(temp_dir), {})
        
        # 创建简单的测试计划
        plan = Plan(
            task="简单测试任务",
            steps=[
                PlanStep(
                    title="测试步骤",
                    details="执行简单的测试操作",
                    agent_name="test_agent"
                )
            ]
        )
        
        # 启动工作流程
        manager.start_workflow(plan)
        
        # 检查工作流程状态
        status = manager.get_workflow_status()
        assert status['total_steps'] == 1
        assert status['current_step'] == 0
        assert status['should_continue'] is True
        
        # 模拟完成步骤
        manager.coordinator.complete_step(result="测试完成")
        
        # 检查最终状态
        final_status = manager.get_workflow_status()
        assert final_status['completed_steps'] == 1
        assert final_status['should_continue'] is False
        
        logger.info("✅ 完整工作流程测试通过")

async def test_error_handling():
    """测试错误处理"""
    logger.info("🧪 测试错误处理")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = IntegratedWorkflowManager(Path(temp_dir), {})
        
        plan = Plan(
            task="错误测试任务",
            steps=[
                PlanStep(
                    title="测试错误步骤",
                    details="测试错误处理",
                    agent_name="test_agent"
                )
            ]
        )
        
        manager.start_workflow(plan)
        
        # 测试步骤失败
        manager.coordinator.fail_step(error="测试错误")
        
        current_step = manager.coordinator.get_current_step()
        assert current_step.status == "failed"
        assert current_step.error == "测试错误"
        
        # 测试强制完成
        manager.force_complete_current_step("手动完成")
        
        # 由于步骤已经失败，强制完成应该不会改变状态
        # 或者需要重新实现这个逻辑
        
        logger.info("✅ 错误处理测试通过")

async def main():
    """主测试函数"""
    logger.info("🚀 开始增强工作流程测试")
    
    test_functions = [
        test_material_manager,
        test_workflow_coordinator,
        test_message_analysis,
        test_workflow_manager_initialization,
        test_complete_workflow,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            passed += 1
        except Exception as e:
            logger.error(f"❌ 测试失败 {test_func.__name__}: {e}")
            failed += 1
    
    logger.info(f"📊 测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！")
    else:
        logger.error(f"❌ {failed} 个测试失败")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())