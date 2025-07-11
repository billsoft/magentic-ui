#!/usr/bin/env python3
"""
MUNAS风格的任务管理演示
展示通用多任务agent平台的输出管理能力
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from magentic_ui.utils.task_output_manager import get_task_output_manager, create_task_session

def demo_task_output_management():
    """演示任务输出管理功能"""
    print("🤖 MUNAS风格多任务Agent平台 - 任务输出管理演示")
    print("=" * 60)
    
    # 获取任务输出管理器
    manager = get_task_output_manager()
    
    # 创建不同类型的任务会话
    tasks = [
        ("360度相机产品介绍生成", "product_introduction"),
        ("网站分析与竞品研究", "web_research"),
        ("技术文档自动生成", "document_generation"),
        ("数据可视化图表制作", "data_visualization"),
        ("多语言翻译与本地化", "translation")
    ]
    
    print("📋 创建任务会话:")
    sessions = []
    for task_desc, task_type in tasks:
        session = create_task_session(task_desc, task_type)
        sessions.append(session)
        print(f"  ✅ {session.session_id}: {task_desc}")
        print(f"     📁 输出目录: {session.output_dir}")
    
    print(f"\n📊 当前任务统计:")
    stats = manager.get_session_stats()
    print(f"  - 总任务数: {stats['total_sessions']}")
    print(f"  - 活跃任务: {stats['active_sessions']}")
    print(f"  - 任务类型分布:")
    for task_type, count in stats['task_types'].items():
        print(f"    • {task_type}: {count}")
    
    print(f"\n🗂️ 目录结构:")
    print("task_outputs/")
    print("├── active/          # 进行中的任务")
    print("│   ├── product_introduction_xxxxx/")
    print("│   │   ├── inputs/")
    print("│   │   ├── intermediates/")
    print("│   │   ├── outputs/")
    print("│   │   └── logs/")
    print("│   └── web_research_yyyyy/")
    print("├── completed/       # 已完成的任务")
    print("├── archived/        # 归档的任务")
    print("└── sessions.json    # 会话记录")
    
    print(f"\n🎯 **MUNAS风格特性**:")
    print("• 🔄 多任务并发执行")
    print("• 📁 自动化输出目录管理")
    print("• 🏷️ 任务类型分类和统计")
    print("• 🕐 会话生命周期管理")
    print("• 🧹 自动清理和归档")
    print("• 📊 任务执行监控")
    
    return sessions

def demo_task_lifecycle():
    """演示任务生命周期"""
    print("\n🔄 任务生命周期演示")
    print("-" * 40)
    
    manager = get_task_output_manager()
    
    # 模拟完成第一个任务
    active_sessions = manager.get_active_sessions()
    if active_sessions:
        session = active_sessions[0]
        print(f"📝 完成任务: {session.session_id}")
        
        # 模拟生成一些输出文件
        outputs_dir = session.output_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        
        # 创建示例输出文件
        (outputs_dir / "result.md").write_text("# 任务结果\n这是生成的文档内容")
        (outputs_dir / "data.json").write_text('{"status": "completed", "result": "success"}')
        
        # 完成任务
        final_outputs = {
            "result_file": "outputs/result.md",
            "data_file": "outputs/data.json",
            "status": "success"
        }
        manager.complete_task_session(session.session_id, final_outputs)
        
        print(f"  ✅ 任务已移动至completed目录")
        print(f"  📄 生成文件: {list(final_outputs.keys())}")
    
    # 显示更新后的统计
    print(f"\n📊 更新后的统计:")
    stats = manager.get_session_stats()
    print(f"  - 活跃任务: {stats['active_sessions']}")
    print(f"  - 已完成: {stats['completed_sessions']}")

def demo_cleanup_and_maintenance():
    """演示清理和维护功能"""
    print("\n🧹 清理和维护演示")
    print("-" * 40)
    
    manager = get_task_output_manager()
    
    print("🗑️ 清理孤立的会话目录...")
    manager.cleanup_failed_sessions()
    
    print("📦 归档旧的已完成任务...")
    manager.archive_old_sessions(days_old=7)
    
    print("✅ 维护操作完成")

def main():
    """主函数"""
    try:
        # 演示任务输出管理
        sessions = demo_task_output_management()
        
        # 演示任务生命周期
        demo_task_lifecycle()
        
        # 演示清理和维护
        demo_cleanup_and_maintenance()
        
        print("\n🎉 MUNAS风格任务管理演示完成!")
        print("\n💡 **核心优势**:")
        print("• 解决了固定目录名称的问题")
        print("• 支持多任务并发执行")
        print("• 自动化的生命周期管理")
        print("• 灵活的任务类型扩展")
        print("• 完整的会话追踪和统计")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()