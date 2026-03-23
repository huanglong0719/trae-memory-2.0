#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDI 评分器 - Global Desirability Index
基于 EvoMap 理念的记忆质量评估系统
"""

import re
from datetime import datetime
from typing import Dict, List


class GDIScorer:
    """
    GDI 评分器
    
    综合考虑四个维度：
    - 内在质量 (35%): 内容长度、结构完整性、代码示例、标签丰富度、可读性
    - 使用指标 (30%): 访问频率、复用率、最近使用
    - 社交信号 (20%): 用户反馈、点赞标记
    - 新鲜度 (15%): 基于创建和更新时间
    """
    
    WEIGHTS = {
        'intrinsic': 0.35,
        'usage': 0.30,
        'social': 0.20,
        'freshness': 0.15
    }
    
    def __init__(self, store=None):
        """
        初始化 GDI 评分器
        
        Args:
            store: MemoryStore 实例（用于获取引用计数等）
        """
        self.store = store
    
    def calculate_gdi(self, memory: Dict) -> Dict[str, float]:
        """
        计算 GDI 综合评分
        
        Args:
            memory: 记忆字典（包含所有字段）
            
        Returns:
            包含各维度评分和综合评分的字典
        """
        intrinsic = self._calculate_intrinsic_quality(memory)
        usage = self._calculate_usage_metrics(memory)
        social = self._calculate_social_signals(memory)
        freshness = self._calculate_freshness(memory)
        
        gdi = (
            intrinsic * self.WEIGHTS['intrinsic'] +
            usage * self.WEIGHTS['usage'] +
            social * self.WEIGHTS['social'] +
            freshness * self.WEIGHTS['freshness']
        )
        
        return {
            'gdi_score': round(gdi, 3),
            'gdi_intrinsic': round(intrinsic, 3),
            'gdi_usage': round(usage, 3),
            'gdi_social': round(social, 3),
            'gdi_freshness': round(freshness, 3)
        }
    
    def _calculate_intrinsic_quality(self, memory: Dict) -> float:
        """
        内在质量评分 (0-1)
        
        评估维度：
        - 内容长度 (10%)
        - 结构完整性 (30%)
        - 代码示例 (20%)
        - 标签丰富度 (20%)
        - 可读性 (20%)
        """
        score = 0.0
        content = memory.get('content', '')
        title = memory.get('title', '')
        tags = memory.get('tags', [])
        
        # 1. 内容长度评分 (10%)
        content_len = len(content)
        if content_len >= 200:
            score += 0.10
        elif content_len >= 100:
            score += 0.07
        elif content_len >= 50:
            score += 0.05
        
        # 2. 结构完整性 (30%)
        # 标题质量 (15%)
        if title and len(title) >= 10:
            score += 0.15
        elif title and len(title) >= 5:
            score += 0.08
        
        # 多段落结构 (15%)
        if '\n' in content and content.count('\n') >= 2:
            score += 0.15
        
        # 3. 代码示例 (20%)
        if '```' in content:
            code_blocks = content.count('```') // 2
            if code_blocks >= 1:
                score += 0.15
            if code_blocks >= 2:
                score += 0.05
        elif re.search(r'\b(def |class |import |from |if |for |while )\b', content):
            score += 0.08
        
        # 4. 标签丰富度 (20%)
        if isinstance(tags, list):
            tag_count = len(tags)
            if tag_count >= 3:
                score += 0.20
            elif tag_count >= 2:
                score += 0.15
            elif tag_count >= 1:
                score += 0.10
        
        # 5. 可读性 - 中日韩字符比例 (20%)
        cjk_ratio = self._count_cjk_chars(content) / max(len(content), 1)
        if 0.3 <= cjk_ratio <= 0.8:
            score += 0.20
        elif 0.2 <= cjk_ratio < 0.3 or 0.8 < cjk_ratio <= 0.9:
            score += 0.10
        
        return min(score, 1.0)
    
    def _calculate_usage_metrics(self, memory: Dict) -> float:
        """
        使用指标评分 (0-1)
        
        评估维度：
        - 访问频率 (40%)
        - 复用率 (30%)
        - 最近使用 (30%)
        """
        score = 0.0
        
        # 1. 访问频率 (40%)
        access_count = memory.get('access_count', 0)
        access_score = min(access_count / 20, 1.0)
        score += access_score * 0.40
        
        # 2. 复用率 - 被引用次数 (30%)
        if self.store:
            reuse_count = self._count_references(memory.get('id'))
            reuse_score = min(reuse_count / 5, 1.0)
            score += reuse_score * 0.30
        else:
            score += 0.15
        
        # 3. 最近使用 (30%)
        last_accessed = memory.get('last_accessed')
        if last_accessed:
            try:
                if isinstance(last_accessed, str):
                    last_access_time = datetime.fromisoformat(last_accessed)
                else:
                    last_access_time = last_access_time
                
                days_since_access = (datetime.now() - last_access_time).days
                recency_score = max(0, 1 - days_since_access / 30)
                score += recency_score * 0.30
            except:
                pass
        
        return min(score, 1.0)
    
    def _calculate_social_signals(self, memory: Dict) -> float:
        """
        社交信号评分 (0-1)
        注：当前版本为预留接口
        """
        return 0.5
    
    def _calculate_freshness(self, memory: Dict) -> float:
        """
        新鲜度评分 (0-1)
        """
        created_at = memory.get('created_at')
        updated_at = memory.get('updated_at')
        
        reference_date = None
        if updated_at:
            try:
                if isinstance(updated_at, str):
                    reference_date = datetime.fromisoformat(updated_at)
            except:
                pass
        
        if not reference_date and created_at:
            try:
                if isinstance(created_at, str):
                    reference_date = datetime.fromisoformat(created_at)
            except:
                pass
        
        if not reference_date:
            return 0.5
        
        age_days = (datetime.now() - reference_date).days
        
        if age_days <= 30:
            return 1.0
        elif age_days <= 90:
            return 1.0 - (age_days - 30) / 120
        else:
            return 0.3
    
    def _count_cjk_chars(self, text: str) -> int:
        """统计中日韩字符数量"""
        return sum(
            1 for c in text 
            if '\u4e00' <= c <= '\u9fff' or
               '\u3040' <= c <= '\u30ff' or
               '\uac00' <= c <= '\ud7af'
        )
    
    def _count_references(self, memory_id: int) -> int:
        """统计记忆被引用次数"""
        if not self.store:
            return 0
        return 0
    
    def get_quality_level(self, gdi_score: float) -> str:
        """根据 GDI 分数获取质量等级"""
        if gdi_score >= 0.8:
            return "优秀"
        elif gdi_score >= 0.6:
            return "良好"
        elif gdi_score >= 0.4:
            return "一般"
        elif gdi_score >= 0.2:
            return "较差"
        else:
            return "差"
    
    def get_quality_suggestions(self, memory: Dict) -> List[str]:
        """获取质量改进建议"""
        suggestions = []
        content = memory.get('content', '')
        title = memory.get('title', '')
        tags = memory.get('tags', [])
        
        if len(content) < 50:
            suggestions.append("内容过短，建议补充详细说明或示例")
        
        if not title or len(title) < 10:
            suggestions.append("标题不够具体，建议使用更描述性的标题")
        
        if ('def ' in content or 'import ' in content) and '```' not in content:
            suggestions.append("包含代码但未使用代码块，建议用 ``` 包裹代码")
        
        if not tags or len(tags) < 2:
            suggestions.append("标签较少，建议添加 2-3 个相关标签便于检索")
        
        if '\n' not in content:
            suggestions.append("内容为单一段落，建议分段提高可读性")
        
        return suggestions
