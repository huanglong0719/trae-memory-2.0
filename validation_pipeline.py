#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多维度验证管道 - 基于 EvoMap 的验证机制
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    score: float
    validator_name: str
    issues: List[str] = None
    similar_memories: List = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.similar_memories is None:
            self.similar_memories = []


class ValidationPipeline:
    """多维度验证管道"""
    
    def __init__(self, store=None):
        """
        初始化验证管道
        
        Args:
            store: MemoryStore 实例
        """
        self.validators = [
            ContentValidator(),
            CodeValidator(),
            UniquenessValidator(store),
            FactValidator(),
        ]
    
    def validate(self, memory: Dict) -> List[ValidationResult]:
        """
        执行完整验证流程
        
        Args:
            memory: 记忆字典
            
        Returns:
            所有验证器的结果列表
        """
        results = []
        
        for validator in self.validators:
            result = validator.validate(memory)
            results.append(result)
        
        return results
    
    def is_valid(self, memory: Dict, threshold: float = 0.6) -> bool:
        """
        判断记忆是否通过验证
        
        Args:
            memory: 记忆字典
            threshold: 通过阈值
            
        Returns:
            是否通过验证
        """
        results = self.validate(memory)
        return all(r.passed for r in results)
    
    def get_total_score(self, results: List[ValidationResult]) -> float:
        """计算综合评分"""
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)


class ContentValidator:
    """内容验证器"""
    
    MIN_LENGTH = 30
    MIN_TITLE_LENGTH = 5
    
    def validate(self, memory: Dict) -> ValidationResult:
        """验证内容质量"""
        issues = []
        score = 1.0
        
        content = memory.get('content', '')
        title = memory.get('title', '')
        
        # 1. 最小长度检查
        if len(content) < self.MIN_LENGTH:
            issues.append(f"内容过短（{len(content)}字符，至少{self.MIN_LENGTH}字符）")
            score -= 0.3
        
        # 2. 标题完整性
        if not title or len(title) < self.MIN_TITLE_LENGTH:
            issues.append(f"标题不完整（{len(title) if title else 0}字符，至少{self.MIN_TITLE_LENGTH}字符）")
            score -= 0.2
        
        # 3. 代码块完整性
        if '```' in content:
            code_blocks = content.count('```')
            if code_blocks % 2 != 0:
                issues.append("代码块未闭合（``` 数量为奇数）")
                score -= 0.2
        
        # 4. 空内容检查
        if not content.strip():
            issues.append("内容为空")
            score -= 1.0
        
        return ValidationResult(
            passed=score >= 0.6,
            score=max(score, 0.0),
            validator_name="ContentValidator",
            issues=issues
        )


class CodeValidator:
    """代码验证器"""
    
    def validate(self, memory: Dict) -> ValidationResult:
        """验证代码正确性"""
        content = memory.get('content', '')
        
        if '```' not in content:
            return ValidationResult(
                passed=True,
                score=1.0,
                validator_name="CodeValidator",
                issues=[]
            )
        
        issues = []
        score = 1.0
        
        # 提取代码块
        code_blocks = self._extract_code_blocks(content)
        
        for code in code_blocks:
            lang = code['language']
            source = code['source']
            
            # Python 语法检查
            if lang == 'python':
                try:
                    compile(source, '<string>', 'exec')
                except SyntaxError as e:
                    issues.append(f"Python 语法错误：{e}")
                    score -= 0.4
        
        return ValidationResult(
            passed=score >= 0.6,
            score=max(score, 0.0),
            validator_name="CodeValidator",
            issues=issues
        )
    
    def _extract_code_blocks(self, content: str) -> List[Dict]:
        """提取代码块"""
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        return [
            {'language': m[0] or 'text', 'source': m[1]}
            for m in matches
        ]


class UniquenessValidator:
    """唯一性验证器"""
    
    SIMILARITY_THRESHOLD_HIGH = 0.9
    SIMILARITY_THRESHOLD_MEDIUM = 0.8
    
    def __init__(self, store=None):
        """
        初始化唯一性验证器
        
        Args:
            store: MemoryStore 实例
        """
        self.store = store
    
    def validate(self, memory: Dict) -> ValidationResult:
        """检查是否重复"""
        if not self.store:
            return ValidationResult(
                passed=True,
                score=1.0,
                validator_name="UniquenessValidator",
                issues=[]
            )
        
        issues = []
        score = 1.0
        similar_memories = []
        
        # 搜索相似记忆
        title = memory.get('title', '')
        category = memory.get('category')
        memory_id = memory.get('id')
        
        if title and hasattr(self.store, 'search_memories'):
            similar = self.store.search_memories(
                title,
                category=category,
                limit=5,
                use_semantic=True
            )
            
            # 排除自己
            similar = [m for m in similar if m.get('id') != memory_id]
            
            if similar:
                # 检查最高相似度
                max_similarity = max(m.get('semantic_score', 0) for m in similar)
                
                if max_similarity > self.SIMILARITY_THRESHOLD_HIGH:
                    issues.append(f"发现高度相似记忆 (相似度：{max_similarity:.2f})")
                    score -= 0.5
                    similar_memories = similar[:3]
                elif max_similarity > self.SIMILARITY_THRESHOLD_MEDIUM:
                    issues.append("建议检查是否重复（中度相似）")
                    score -= 0.2
                    similar_memories = similar[:3]
        
        return ValidationResult(
            passed=score >= 0.6,
            score=max(score, 0.0),
            validator_name="UniquenessValidator",
            issues=issues,
            similar_memories=similar_memories
        )


class FactValidator:
    """事实验证器"""
    
    UNCERTAINTY_WORDS = [
        '可能', '也许', '大概', '或许',
        'maybe', 'perhaps', 'possibly', 'might'
    ]
    
    def validate(self, memory: Dict) -> ValidationResult:
        """验证事实准确性"""
        content = memory.get('content', '').lower()
        title = memory.get('title', '').lower()
        text = content + ' ' + title
        
        issues = []
        
        # 检查不确定性词汇
        uncertainty_count = sum(
            1 for word in self.UNCERTAINTY_WORDS 
            if word in text
        )
        
        if uncertainty_count > 3:
            issues.append(f"包含较多不确定性表述（{uncertainty_count}处），建议验证准确性")
        
        # 不强制阻止，只给提示
        score = 0.8 if uncertainty_count == 0 else 0.6
        
        return ValidationResult(
            passed=True,  # 总是通过，只给提示
            score=score,
            validator_name="FactValidator",
            issues=issues
        )
