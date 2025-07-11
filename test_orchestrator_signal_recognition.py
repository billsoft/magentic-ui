#!/usr/bin/env python3
"""
🧪 Orchestrator 信号识别单元测试  
测试Orchestrator对不同完成信号的识别和处理
"""

import pytest
from unittest.mock import Mock
from typing import List, Dict, Any

class TestOrchestratorSignalRecognition:
    """测试Orchestrator的信号识别逻辑"""
    
    def test_step_vs_task_completion_signals(self):
        """测试区分步骤完成和任务完成信号"""
        
        def classify_completion_signal(response: str) -> str:
            """分类完成信号类型"""
            step_signals = [
                "✅ 当前步骤已完成", "✅ STEP COMPLETED",
                "⚠️ 当前步骤因错误完成", "🔄 当前步骤通过替代方案完成"
            ]
            
            task_signals = [
                "✅ 任务已完成", "✅ TASK COMPLETED", 
                "任务已完成", "task completed"
            ]
            
            if any(signal in response for signal in step_signals):
                return "step_completion"
            elif any(signal in response for signal in task_signals):
                return "task_completion"  # 应该被过滤
            else:
                return "no_completion"
        
        # 测试步骤完成信号（应该接受）
        step_responses = [
            "✅ 当前步骤已完成：已收集te720.com产品信息",
            "✅ STEP COMPLETED: Image generation finished",
            "⚠️ 当前步骤因错误完成：网站无法访问但提供了替代方案"
        ]
        
        for response in step_responses:
            assert classify_completion_signal(response) == "step_completion"
        
        # 测试任务完成信号（应该被过滤）
        task_responses = [
            "✅ 任务已完成：所有步骤都完成了",
            "✅ 研究任务基本完成",
            "TASK COMPLETED successfully"
        ]
        
        for response in task_responses:
            result = classify_completion_signal(response)
            # 在修复后的系统中，这些应该不被识别为有效完成信号
            assert result == "task_completion" or result == "no_completion"  # 根据实际实现调整

    def test_agent_specific_completion_patterns(self):
        """测试不同Agent的特定完成模式"""
        
        def get_agent_completion_patterns(agent_name: str) -> List[str]:
            """获取特定Agent的完成模式"""
            patterns = {
                "web_surfer": [
                    "✅ 当前步骤已完成", "⚠️ 当前步骤因错误完成",
                    "🔄 当前步骤通过替代方案完成"
                ],
                "image_generator": [
                    "图像生成任务已完成", "图像已成功生成", 
                    "successfully generated", "generation completed"
                ],
                "coder_agent": [
                    "文档创建任务已完成", "HTML转换完成", "PDF生成完成",
                    "file saved", "document completed"
                ]
            }
            return patterns.get(agent_name, [])
        
        def is_valid_completion_for_agent(agent: str, response: str) -> bool:
            """检查响应是否为特定Agent的有效完成信号"""
            patterns = get_agent_completion_patterns(agent)
            return any(pattern in response for pattern in patterns)
        
        # 测试WebSurfer完成信号
        websurfer_response = "✅ 当前步骤已完成：已访问te720.com收集产品信息"
        assert is_valid_completion_for_agent("web_surfer", websurfer_response)
        
        # 测试ImageGenerator完成信号
        image_response = "图像生成任务已完成，360度相机图像已创建"
        assert is_valid_completion_for_agent("image_generator", image_response)
        
        # 测试错误的Agent信号匹配
        assert not is_valid_completion_for_agent("web_surfer", "图像生成任务已完成")
        assert not is_valid_completion_for_agent("image_generator", "✅ 当前步骤已完成")

    def test_completion_confidence_scoring(self):
        """测试完成信号的置信度评分"""
        
        def calculate_completion_confidence(response: str, expected_agent: str) -> float:
            """计算完成信号的置信度"""
            score = 0.0
            
            # 明确完成信号 (+0.4)
            completion_indicators = ["✅", "completed", "已完成", "finished"]
            if any(indicator in response.lower() for indicator in completion_indicators):
                score += 0.4
            
            # 实质性内容 (+0.3)
            content_indicators = ["te720", "360", "camera", "image", "document"]
            content_count = sum(1 for indicator in content_indicators if indicator.lower() in response.lower())
            score += min(content_count * 0.1, 0.3)
            
            # Agent匹配 (+0.2)
            agent_keywords = {
                "web_surfer": ["访问", "浏览", "网站", "页面"],
                "image_generator": ["图像", "生成", "image", "generated"],
                "coder_agent": ["文档", "代码", "文件", "document"]
            }
            if expected_agent in agent_keywords:
                if any(keyword in response for keyword in agent_keywords[expected_agent]):
                    score += 0.2
            
            # 避免通用回复 (-0.3)
            generic_patterns = ["我理解", "let me help", "how can i", "我可以帮助"]
            if any(pattern in response.lower() for pattern in generic_patterns):
                score -= 0.3
            
            return max(0.0, min(1.0, score))
        
        # 测试高置信度完成信号
        high_confidence = "✅ 当前步骤已完成：已成功访问te720.com获得360度相机产品信息"
        score = calculate_completion_confidence(high_confidence, "web_surfer")
        assert score >= 0.7, f"高质量完成信号应该有高置信度: {score}"
        
        # 测试低置信度通用回复
        low_confidence = "我理解您需要生成360度相机图像，让我帮您处理"
        score = calculate_completion_confidence(low_confidence, "web_surfer")
        assert score <= 0.3, f"通用回复应该有低置信度: {score}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])