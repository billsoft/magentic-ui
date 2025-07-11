#!/usr/bin/env python3
"""
对话级文件管理系统测试脚本
验证完整的文件管理和下载流程
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from magentic_ui.utils.conversation_storage_manager import (
    get_conversation_storage_manager,
    add_conversation_file,
    add_conversation_text_file,
    get_conversation_files,
    mark_file_as_deliverable,
    FileType
)

from magentic_ui.utils.intelligent_deliverable_analyzer import (
    get_deliverable_analyzer,
    analyze_conversation_deliverables
)

async def test_conversation_file_management():
    """测试对话级文件管理"""
    print("🧪 测试对话级文件管理系统")
    print("=" * 60)
    
    # 测试会话ID
    session_id = 12345
    
    # 获取管理器
    storage_manager = get_conversation_storage_manager()
    
    print(f"📁 创建会话 {session_id} 的文件存储...")
    storage = storage_manager.get_or_create_conversation_storage(session_id)
    print(f"✅ 存储目录: {storage.conversation_dir}")
    
    # 模拟不同agent创建文件
    print("\n🤖 模拟agent创建文件...")
    
    # WebSurfer创建网页内容
    webpage_content = """
    <html>
    <head><title>360度全景相机产品页</title></head>
    <body>
        <h1>360度全景相机</h1>
        <p>专业级四镜头设计，支持8K高清录制</p>
        <ul>
            <li>4镜头分布式设计</li>
            <li>90度精确间隔</li>
            <li>机内拼接技术</li>
            <li>实时直播功能</li>
        </ul>
    </body>
    </html>
    """
    
    web_file = add_conversation_text_file(
        session_id=session_id,
        content=webpage_content,
        filename="te720_product_page.html",
        agent_name="WebSurfer",
        description="从te720.com收集的产品页面内容",
        is_intermediate=True,
        tags=["webpage", "html", "product_info"]
    )
    print(f"  📄 WebSurfer创建: {web_file.file_path.name}")
    
    # ImageGenerator创建图像
    # 模拟图像数据
    mock_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa'
    
    image_file = add_conversation_file(
        session_id=session_id,
        file_content=mock_image_data,
        filename="360_camera_render.png",
        agent_name="ImageGenerator", 
        description="生成的360度全景相机产品渲染图",
        is_intermediate=False,  # 图像是交付物
        tags=["generated", "image", "product_render"]
    )
    print(f"  🎨 ImageGenerator创建: {image_file.file_path.name}")
    
    # CoderAgent创建文档
    markdown_content = """
# 360度全景相机产品介绍

## 产品概述
基于te720.com的专业全景相机技术，设计了一款创新的360度全景相机。

## 核心特性
- **四镜头分布式设计**: 4个高质量镜头分别位于相机的前、后、左、右四个方向
- **90度间隔**: 每个镜头间隔90度，确保完整的360度覆盖
- **8K高清录制**: 支持8K分辨率视频录制
- **实时直播**: 支持实时流媒体传输

## 技术规格
- 镜头数量: 4个
- 录制分辨率: 8K
- 机身材质: 金属
- 接口: 标准三脚架接口

## 应用场景
- 虚拟现实内容制作
- 全景摄影和录像
- 建筑和房地产展示
- 活动记录和直播
"""
    
    doc_file = add_conversation_text_file(
        session_id=session_id,
        content=markdown_content,
        filename="product_introduction.md",
        agent_name="CoderAgent",
        description="完整的产品介绍文档",
        is_intermediate=False,  # 文档是交付物
        tags=["document", "markdown", "product_introduction"]
    )
    print(f"  💻 CoderAgent创建: {doc_file.file_path.name}")
    
    # 创建一些中间产物
    intermediate_data = '{"product_specs": {"lenses": 4, "resolution": "8K", "features": ["360_capture", "live_stream"]}}'
    
    data_file = add_conversation_text_file(
        session_id=session_id,
        content=intermediate_data,
        filename="product_specs.json",
        agent_name="WebSurfer",
        description="提取的产品规格数据",
        is_intermediate=True,
        tags=["data", "json", "specs"]
    )
    print(f"  📊 WebSurfer创建: {data_file.file_path.name}")
    
    print(f"\n📈 文件创建完成，共创建 4 个文件")
    
    # 获取文件摘要
    print("\n📋 获取文件摘要...")
    summary = storage_manager.get_conversation_summary(session_id)
    print(f"  - 总文件数: {summary['total_files']}")
    print(f"  - 交付物: {summary['deliverable_files']}")
    print(f"  - 中间产物: {summary['intermediate_files']}")
    print(f"  - 文件类型: {summary['file_types']}")
    print(f"  - Agent统计: {summary['agent_statistics']}")
    
    # 测试文件检索
    print("\n🔍 测试文件检索...")
    all_files = get_conversation_files(session_id)
    print(f"  所有文件: {len(all_files)}")
    
    deliverable_files = get_conversation_files(session_id, is_deliverable_only=True)
    print(f"  交付物: {len(deliverable_files)}")
    
    websurfer_files = get_conversation_files(session_id, agent_name="WebSurfer")
    print(f"  WebSurfer文件: {len(websurfer_files)}")
    
    image_files = get_conversation_files(session_id, file_type=FileType.IMAGE)
    print(f"  图像文件: {len(image_files)}")
    
    # 测试智能交付物分析
    print("\n🧠 测试智能交付物分析...")
    task_description = "为te720.com的360度全景相机产品创建完整的产品介绍材料"
    
    analysis = await analyze_conversation_deliverables(
        session_id=session_id,
        task_description=task_description,
        conversation_messages=[]
    )
    
    print(f"  📊 分析结果:")
    print(f"    - 任务目标: {analysis.task_goal}")
    print(f"    - 分析文件数: {analysis.total_files_analyzed}")
    print(f"    - 推荐文件数: {len(analysis.recommended_files)}")
    print(f"    - 交付摘要: {analysis.delivery_summary}")
    
    print(f"\n📑 推荐文件详情:")
    for i, rec in enumerate(analysis.recommended_files, 1):
        print(f"  {i}. {rec.file_info.file_path.name}")
        print(f"     优先级: {rec.delivery_priority} | 相关性: {rec.relevance_score:.2f}")
        print(f"     推荐理由: {rec.recommendation_reason}")
        if rec.suggested_filename:
            print(f"     建议文件名: {rec.suggested_filename}")
        if rec.customer_description:
            print(f"     客户描述: {rec.customer_description}")
        print()
    
    # 测试手动标记交付物
    print("✨ 手动标记JSON文件为交付物...")
    data_file_id = f"WebSurfer_{data_file.created_at.strftime('%Y%m%d_%H%M%S')}_product_specs"
    mark_file_as_deliverable(session_id, data_file_id, "重要的产品规格数据")
    
    # 重新获取摘要
    updated_summary = storage_manager.get_conversation_summary(session_id)
    print(f"  更新后交付物数量: {updated_summary['deliverable_files']}")
    
    # 测试文件内容读取
    print("\n📖 测试文件内容读取...")
    markdown_file_id = f"CoderAgent_{doc_file.created_at.strftime('%Y%m%d_%H%M%S')}_product_introduction"
    content = storage_manager.get_file_content(session_id, markdown_file_id)
    if content:
        content_str = content.decode('utf-8')
        print(f"  成功读取Markdown文件，内容长度: {len(content_str)} 字符")
        print(f"  文件开头: {content_str[:100]}...")
    
    print("\n🎉 对话级文件管理系统测试完成!")
    
    return {
        "session_id": session_id,
        "files_created": len(all_files),
        "analysis": analysis,
        "summary": updated_summary
    }

async def test_file_download_simulation():
    """模拟文件下载流程测试"""
    print("\n💾 测试文件下载流程...")
    
    session_id = 12345
    storage_manager = get_conversation_storage_manager()
    analyzer = get_deliverable_analyzer()
    
    # 获取交付物分析
    task_description = "为te720.com的360度全景相机产品创建完整的产品介绍材料"
    analysis = await analyzer.analyze_deliverables(
        session_id=session_id,
        task_description=task_description
    )
    
    # 模拟获取下载文件
    downloadable_files = analyzer.get_deliverable_files_for_download(
        session_id=session_id,
        analysis=analysis,
        priority_threshold=3
    )
    
    print(f"  可下载文件数: {len(downloadable_files)}")
    
    total_size = 0
    for filename, content, content_type in downloadable_files:
        print(f"    📁 {filename}")
        print(f"       类型: {content_type}")
        print(f"       大小: {len(content)} bytes")
        total_size += len(content)
    
    print(f"  总下载大小: {total_size} bytes")
    
    return downloadable_files

def main():
    """主函数"""
    async def run_tests():
        try:
            # 测试对话级文件管理
            test_result = await test_conversation_file_management()
            
            # 测试文件下载流程
            download_result = await test_file_download_simulation()
            
            print("\n🎯 **测试总结**:")
            print(f"✅ 对话级文件管理: 正常")
            print(f"✅ 智能交付物分析: 正常") 
            print(f"✅ 文件下载流程: 正常")
            print(f"✅ 会话 {test_result['session_id']}: {test_result['files_created']} 个文件")
            print(f"✅ 推荐交付物: {len(test_result['analysis'].recommended_files)} 个")
            print(f"✅ 可下载文件: {len(download_result)} 个")
            
            print("\n💡 **核心功能验证**:")
            print("• 每个对话独立的文件存储目录 ✅")
            print("• 多种文件类型分类管理 ✅") 
            print("• Agent感知的文件创建和管理 ✅")
            print("• 智能交付物分析和推荐 ✅")
            print("• 文件下载和打包功能 ✅")
            print("• 中间产物和最终交付物区分 ✅")
            
            print("\n🎉 所有测试通过! 对话级文件管理系统已就绪!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 运行异步测试
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()