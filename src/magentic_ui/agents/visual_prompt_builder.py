"""
AI绘图提示词构建器
用于从用户任务中智能提取绘图需求并构建高质量的AI绘图提示词
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

class VisualType(Enum):
    """视觉内容类型枚举"""
    LOGO = "logo"
    ILLUSTRATION = "illustration"
    DIAGRAM = "diagram"
    INFOGRAPHIC = "infographic"
    CONCEPT_ART = "concept_art"
    CHART = "chart"
    ICON = "icon"
    BANNER = "banner"
    POSTER = "poster"
    PRODUCT = "product"  # 新增：产品图类型
    PHOTO = "photo"      # 新增：照片类型
    UNKNOWN = "unknown"

class VisualStyle(Enum):
    """视觉风格枚举"""
    MINIMALIST = "minimalist"
    MODERN = "modern"
    VINTAGE = "vintage"
    PROFESSIONAL = "professional"
    ARTISTIC = "artistic"
    TECHNICAL = "technical"
    PLAYFUL = "playful"
    ELEGANT = "elegant"
    BOLD = "bold"
    CLEAN = "clean"

@dataclass
class VisualRequest:
    """视觉请求数据结构"""
    visual_type: VisualType
    subject: str
    style: Optional[VisualStyle] = None
    colors: List[str] = field(default_factory=list)
    dimensions: Optional[str] = None
    additional_elements: List[str] = field(default_factory=list)
    context: str = ""
    technical_requirements: List[str] = field(default_factory=list)

class VisualPromptBuilder:
    """AI绘图提示词构建器"""
    
    # 关键词映射
    VISUAL_TYPE_KEYWORDS = {
        VisualType.LOGO: ["logo", "标志", "商标", "品牌标识", "brand", "identity"],
        VisualType.ILLUSTRATION: ["illustration", "插画", "插图", "画", "绘画", "drawing", "艺术"],
        VisualType.DIAGRAM: ["diagram", "图表", "流程图", "架构图", "示意图", "flowchart", "architecture"],
        VisualType.INFOGRAPHIC: ["infographic", "信息图", "数据图", "可视化", "visualization"],
        VisualType.CONCEPT_ART: ["concept", "概念", "设计稿", "原画", "concept art"],
        VisualType.ICON: ["icon", "图标", "符号", "symbol"],
        VisualType.BANNER: ["banner", "横幅", "广告", "宣传"],
        VisualType.POSTER: ["poster", "海报", "宣传画"],
        VisualType.PRODUCT: ["product", "产品", "相机", "camera", "设备", "device", "机器", "machine", "工具", "tool", "商品", "物品", "item", "笔记本", "notebook", "laptop", "电脑", "computer", "手机", "phone", "tablet", "平板"],
        VisualType.PHOTO: ["photo", "照片", "拍摄", "摄影", "photograph", "picture", "image", "拍照"],
    }
    
    STYLE_KEYWORDS = {
        VisualStyle.MINIMALIST: ["minimalist", "简约", "简洁", "clean", "simple"],
        VisualStyle.MODERN: ["modern", "现代", "contemporary", "时尚"],
        VisualStyle.VINTAGE: ["vintage", "复古", "怀旧", "retro", "classic"],
        VisualStyle.PROFESSIONAL: ["professional", "专业", "商务", "business", "corporate"],
        VisualStyle.ARTISTIC: ["artistic", "艺术", "creative", "创意"],
        VisualStyle.TECHNICAL: ["technical", "技术", "工程", "engineering"],
        VisualStyle.PLAYFUL: ["playful", "有趣", "fun", "cute", "可爱"],
        VisualStyle.ELEGANT: ["elegant", "优雅", "sophisticated", "精致"],
        VisualStyle.BOLD: ["bold", "大胆", "striking", "dramatic"],
    }
    
    COLOR_PATTERNS = [
        r"(?:颜色|color|colours?)[：:]\s*([^。，,\n]+)",
        r"(?:使用|用|with|in)\s*([红蓝绿黄紫橙黑白灰pink|blue|red|green|yellow|purple|orange|black|white|gray|grey|gold|silver|brown|navy|teal|coral|crimson|azure|lime|magenta|cyan|maroon|olive|aqua|fuchsia|salmon|khaki|violet|indigo|turquoise|beige|tan|plum|rose|mint|lavender|peach|ivory|jade|ruby|emerald|sapphire|amber|bronze|copper|platinum|pearl|snow|cream|vanilla|chocolate|coffee|caramel|honey|mustard|sage|forest|ocean|sky|sunset|dawn|aurora|rainbow]+(?:\s*[和与,&+]\s*[红蓝绿黄紫橙黑白灰pink|blue|red|green|yellow|purple|orange|black|white|gray|grey|gold|silver|brown|navy|teal|coral|crimson|azure|lime|magenta|cyan|maroon|olive|aqua|fuchsia|salmon|khaki|violet|indigo|turquoise|beige|tan|plum|rose|mint|lavender|peach|ivory|jade|ruby|emerald|sapphire|amber|bronze|copper|platinum|pearl|snow|cream|vanilla|chocolate|coffee|caramel|honey|mustard|sage|forest|ocean|sky|sunset|dawn|aurora|rainbow]+)*)",
        r"([红蓝绿黄紫橙黑白灰pink|blue|red|green|yellow|purple|orange|black|white|gray|grey|gold|silver|brown|navy|teal|coral|crimson|azure|lime|magenta|cyan|maroon|olive|aqua|fuchsia|salmon|khaki|violet|indigo|turquoise|beige|tan|plum|rose|mint|lavender|peach|ivory|jade|ruby|emerald|sapphire|amber|bronze|copper|platinum|pearl|snow|cream|vanilla|chocolate|coffee|caramel|honey|mustard|sage|forest|ocean|sky|sunset|dawn|aurora|rainbow]+)(?:色|调|系)"
    ]
    
    def __init__(self):
        """初始化提示词构建器"""
        pass
    
    def analyze_visual_request(self, user_input: str) -> VisualRequest:
        """分析用户输入，提取视觉请求信息"""
        user_input_lower = user_input.lower()
        
        # 检测视觉类型
        visual_type = self._detect_visual_type(user_input_lower)
        
        # 提取主题
        subject = self._extract_subject(user_input, visual_type)
        
        # 检测风格
        style = self._detect_style(user_input_lower)
        
        # 提取颜色
        colors = self._extract_colors(user_input)
        
        # 提取尺寸信息
        dimensions = self._extract_dimensions(user_input)
        
        # 提取额外元素
        additional_elements = self._extract_additional_elements(user_input, visual_type)
        
        # 提取技术要求
        technical_requirements = self._extract_technical_requirements(user_input)
        
        return VisualRequest(
            visual_type=visual_type,
            subject=subject,
            style=style,
            colors=colors,
            dimensions=dimensions,
            additional_elements=additional_elements,
            context=user_input,
            technical_requirements=technical_requirements
        )
    
    def _detect_visual_type(self, text: str) -> VisualType:
        """检测视觉内容类型"""
        for visual_type, keywords in self.VISUAL_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return visual_type
        return VisualType.UNKNOWN
    
    def _detect_style(self, text: str) -> Optional[VisualStyle]:
        """检测视觉风格"""
        for style, keywords in self.STYLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return style
        return None
    
    def _extract_subject(self, text: str, visual_type: VisualType) -> str:
        """提取主题内容"""
        # 产品类型的特殊处理
        if visual_type == VisualType.PRODUCT:
            # 专门针对产品的提取模式
            product_patterns = [
                r"(\d+\s*镜头[^，,。\n]*?相机)",  # "4镜头全景相机"
                r"([^，,。\n]*?相机)",             # "全景相机"
                r"([^，,。\n]*?笔记本[^，,。\n]*?电脑)", # "现代风格的笔记本电脑"
                r"([^，,。\n]*?笔记本)",           # "笔记本"
                r"([^，,。\n]*?电脑)",             # "电脑"
                r"([^，,。\n]*?手机)",             # "手机"
                r"([^，,。\n]*?设备)",             # "设备"
                r"([^，,。\n]*?产品)",             # "产品"
            ]
            
            for pattern in product_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    subject = matches[0].strip()
                    # 清理常见的无用词
                    subject = re.sub(r"^(一个|一台|一部|一款|the|a|an)\s*", "", subject, flags=re.IGNORECASE)
                    subject = re.sub(r"(的|图|图片|图像|照片|picture|image|photo)$", "", subject, flags=re.IGNORECASE)
                    return subject.strip()
        
        # Logo类型特殊处理
        if visual_type == VisualType.LOGO:
            logo_patterns = [
                r"(?:为|给|of|for)\s*([^的，,。\n]+?)(?:的|做|设计|创建|制作)",
                r"(?:logo|标志|商标)\s*(?:为|给|of|for)?\s*([^的，,。\n]+)",
                r"(?:品牌|公司|店铺|商店)\s*(?:名称|叫|是)?\s*[：:\"']([^\"'：:，,。\n]+)[\"']?",
            ]
            
            for pattern in logo_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    return matches[0].strip()
        
        # 通用主题提取模式
        general_patterns = [
            r"(?:画|绘制|创建|设计|制作|draw|create|design|make)\s*(?:一个|一幅|一张|a|an)?\s*([^的，,。\n]+?)(?:的|图|图片|图像|photo)?",
                r"(?:关于|about|of)\s*([^的，,。\n]+)",
            r"(?:换|生成|generate)\s*(?:一个|一张|一幅|a|an)?\s*([^的，,。\n]+?)(?:的|图|图片|图像|photo)?",
        ]
        
        for pattern in general_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                subject = matches[0].strip()
                # 清理常见的无用词
                subject = re.sub(r"^(一个|一台|一部|一款|the|a|an)\s*", "", subject, flags=re.IGNORECASE)
                subject = re.sub(r"(的|图|图片|图像|照片|picture|image|photo)$", "", subject, flags=re.IGNORECASE)
                return subject.strip()
        
        # 如果以上都没匹配到，尝试提取关键实体
        # 查找数字+物品的组合
        entity_patterns = [
            r"(\d+\s*[镜头]+[^，,。\n]*?[相机]+)",
            r"([^，,。\n]*?[笔记本电脑手机平板相机设备产品工具]+)",
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        # 最后：返回简化的文本
        cleaned_text = re.sub(r"(请|帮我|为我|给我|help|please)", "", text, flags=re.IGNORECASE).strip()
        return cleaned_text[:30] + "..." if len(cleaned_text) > 30 else cleaned_text
    
    def _extract_colors(self, text: str) -> List[str]:
        """提取颜色信息"""
        colors = []
        for pattern in self.COLOR_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    colors.extend([color.strip() for color in match if color.strip()])
                else:
                    colors.append(match.strip())
        
        # 去重并返回
        return list(set(colors))
    
    def _extract_dimensions(self, text: str) -> Optional[str]:
        """提取尺寸信息"""
        dimension_patterns = [
            r"(\d+\s*[x×]\s*\d+)(?:\s*(?:px|像素|pixel))?",
            r"(?:尺寸|大小|size)[：:]\s*([^，,。\n]+)",
            r"(\d+)\s*[x×]\s*(\d+)",
        ]
        
        for pattern in dimension_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"{matches[0][0]}x{matches[0][1]}"
                else:
                    return matches[0].strip()
        
        return None
    
    def _extract_additional_elements(self, text: str, visual_type: VisualType) -> List[str]:
        """提取额外元素"""
        elements = []
        
        # 根据视觉类型提取相关元素
        if visual_type == VisualType.LOGO:
            logo_elements = ["图标", "文字", "符号", "icon", "text", "symbol", "字体", "font"]
            for element in logo_elements:
                if element in text.lower():
                    elements.append(element)
        
        # 通用元素提取
        element_patterns = [
            r"(?:包含|包括|添加|加上|with|include|add)\s*([^，,。\n]+)",
            r"(?:元素|element)[：:]\s*([^，,。\n]+)",
        ]
        
        for pattern in element_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            elements.extend([match.strip() for match in matches])
        
        return list(set(elements))
    
    def _extract_technical_requirements(self, text: str) -> List[str]:
        """提取技术要求"""
        requirements = []
        
        tech_patterns = [
            r"(?:格式|format)[：:]\s*([^，,。\n]+)",
            r"(?:分辨率|resolution)[：:]\s*([^，,。\n]+)",
            r"(?:质量|quality)[：:]\s*([^，,。\n]+)",
            r"(?:要求|requirement)[：:]\s*([^，,。\n]+)",
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            requirements.extend([match.strip() for match in matches])
        
        return requirements
    
    def build_ai_drawing_prompt(self, visual_request: VisualRequest) -> str:
        """构建AI绘图提示词"""
        prompt_parts = []
        
        # 检测是否包含中文
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in visual_request.subject)
        
        if has_chinese:
            # 中文优化的提示词构建
            if visual_request.visual_type == VisualType.PRODUCT:
                prompt_parts.append(f"高质量的{visual_request.subject}产品图")
            elif visual_request.visual_type == VisualType.PHOTO:
                prompt_parts.append(f"专业拍摄的{visual_request.subject}照片")
            elif visual_request.visual_type == VisualType.ILLUSTRATION:
                prompt_parts.append(f"精美的{visual_request.subject}插画")
            else:
                prompt_parts.append(f"精美的{visual_request.subject}设计")
                
            # 风格 (中文)
            if visual_request.style:
                style_map = {
                    "professional": "专业风格",
                    "modern": "现代风格", 
                    "minimalist": "简约风格",
                    "artistic": "艺术风格",
                    "technical": "技术风格",
                    "elegant": "优雅风格",
                    "bold": "大胆风格"
                }
                style_text = style_map.get(visual_request.style.value, f"{visual_request.style.value}风格")
                prompt_parts.append(style_text)
            
            # 技术要求后缀 (中英混合以确保AI理解)
            quality_suffix = "high quality, professional photography, detailed, sharp focus, good composition, product photography lighting"
            
        else:
            # 英文提示词构建
            if visual_request.visual_type != VisualType.UNKNOWN:
                prompt_parts.append(f"High-quality {visual_request.visual_type.value} of {visual_request.subject}")
            else:
                prompt_parts.append(f"High-quality image of {visual_request.subject}")
        
        # 风格
        if visual_request.style:
            prompt_parts.append(f"in {visual_request.style.value} style")
        
            # 技术要求后缀
            quality_suffix = "professional, detailed, sharp focus, good composition"
        
        # 通用元素处理
        if visual_request.colors:
            color_str = ", ".join(visual_request.colors)
            prompt_parts.append(f"colors: {color_str}")
        
        if visual_request.additional_elements:
            elements_str = ", ".join(visual_request.additional_elements)
            prompt_parts.append(f"including: {elements_str}")
        
        if visual_request.dimensions:
            prompt_parts.append(f"resolution: {visual_request.dimensions}")
        
        if visual_request.technical_requirements:
            tech_str = ", ".join(visual_request.technical_requirements)
            prompt_parts.append(f"requirements: {tech_str}")
        
        # 组合提示词
        main_prompt = ", ".join(prompt_parts)
        full_prompt = f"{main_prompt}, {quality_suffix}"
        
        return full_prompt
    
    def should_use_ai_drawing(self, visual_request: VisualRequest) -> bool:
        """判断是否应该使用AI绘图而不是代码绘图"""
        # AI绘图适用的类型
        ai_suitable_types = [
            VisualType.LOGO,
            VisualType.ILLUSTRATION,
            VisualType.CONCEPT_ART,
            VisualType.ICON,
            VisualType.BANNER,
            VisualType.POSTER,
            VisualType.PRODUCT,  # 新增：产品图适用AI绘图
            VisualType.PHOTO,    # 新增：照片适用AI绘图
        ]
        
        # 代码绘图适用的类型
        code_suitable_types = [
            VisualType.CHART,
            VisualType.DIAGRAM,  # 技术图表更适合代码生成
        ]
        
        # 检查是否包含数据相关关键词
        data_keywords = ["数据", "统计", "图表", "chart", "graph", "plot", "data", "statistics", "可视化"]
        has_data_context = any(keyword in visual_request.context.lower() for keyword in data_keywords)
        
        # 决策逻辑
        if visual_request.visual_type in ai_suitable_types and not has_data_context:
            return True
        elif visual_request.visual_type in code_suitable_types or has_data_context:
            return False
        else:
            # 对于未知类型，根据上下文判断
            return not has_data_context
    
    def analyze_and_build_prompt(self, user_input: str) -> Tuple[bool, str, VisualRequest]:
        """分析用户输入并构建提示词
        
        Returns:
            Tuple[bool, str, VisualRequest]: (是否使用AI绘图, 提示词, 视觉请求对象)
        """
        visual_request = self.analyze_visual_request(user_input)
        should_use_ai = self.should_use_ai_drawing(visual_request)
        
        if should_use_ai:
            prompt = self.build_ai_drawing_prompt(visual_request)
        else:
            # 为代码绘图构建技术提示词
            prompt = self._build_code_visualization_prompt(visual_request)
        
        return should_use_ai, prompt, visual_request
    
    def _build_code_visualization_prompt(self, visual_request: VisualRequest) -> str:
        """为代码可视化构建提示词"""
        prompt_parts = []
        
        prompt_parts.append("Create a data visualization")
        
        if visual_request.subject:
            prompt_parts.append(f"showing {visual_request.subject}")
        
        if visual_request.colors:
            color_str = ", ".join(visual_request.colors)
            prompt_parts.append(f"using color scheme: {color_str}")
        
        # 添加matplotlib特定的指令
        prompt_parts.append("using matplotlib with proper styling, labels, and legends")
        prompt_parts.append("save the plot as high-resolution PNG file")
        
        if visual_request.technical_requirements:
            tech_str = ", ".join(visual_request.technical_requirements)
            prompt_parts.append(f"meeting requirements: {tech_str}")
        
        return ". ".join(prompt_parts)

# 全局实例
visual_prompt_builder = VisualPromptBuilder() 