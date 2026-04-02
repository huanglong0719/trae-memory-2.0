#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
置信度评估器 - 记忆质量评估系统
评估记忆的可信度和质量等级
"""

import re
from datetime import datetime
from typing import Dict, List, Optional


class ConfidenceEvaluator:
    """
    置信度评估器
    
    评估维度：
    - 来源可信度 (25%): 记忆来源的可靠性
    - 内容质量 (30%): 内容的完整性、结构化程度
    - 一致性 (20%): 与已有记忆的一致性
    - 时效性 (15%): 记忆的新鲜程度
    - 验证状态 (10%): 是否经过验证
    """
    
    WEIGHTS = {
        'source': 0.25,
        'content': 0.30,
        'consistency': 0.20,
        'freshness': 0.15,
        'validation': 0.10
    }
    
    QUALITY_LEVELS = {
        (0.9, 1.0): '优秀',
        (0.75, 0.9): '良好',
        (0.6, 0.75): '合格',
        (0.4, 0.6): '待改进',
        (0.0, 0.4): '低质量'
    }
    
    SOURCE_SCORES = {
        'user_explicit': 0.95,
        'user_confirmed': 0.90,
        'project_file': 0.85,
        'auto_extract_high': 0.75,
        'auto_extract_medium': 0.60,
        'auto_extract_low': 0.50,
        'inferred': 0.40,
        'unknown': 0.30
    }
    
    NOISE_PATTERNS = [
        r'^(好的|收到|明白|谢谢|了解|清楚)',
        r'^(你好|您好|在吗|嗨)',
        r'^(是|否|对|错|嗯|哦)',
        r'^.{0,10}$',
    ]
    
    def __init__(self, store=None):
        """
        初始化置信度评估器
        
        Args:
            store: MemoryStore 实例（可选，用于一致性检查）
        """
        self.store = store
    
    def evaluate(self, memory: Dict) -> float:
        """
        评估记忆置信度
        
        Args:
            memory: 记忆字典
            
        Returns:
            置信度分数 (0-1)
        """
        scores = []
        
        source_score = self._evaluate_source(memory)
        scores.append(source_score * self.WEIGHTS['source'])
        
        content_score = self._evaluate_content_quality(memory.get('content', ''))
        scores.append(content_score * self.WEIGHTS['content'])
        
        consistency_score = self._evaluate_consistency(memory)
        scores.append(consistency_score * self.WEIGHTS['consistency'])
        
        freshness_score = self._evaluate_freshness(memory)
        scores.append(freshness_score * self.WEIGHTS['freshness'])
        
        validation_score = self._evaluate_validation_status(memory)
        scores.append(validation_score * self.WEIGHTS['validation'])
        
        return sum(scores)
    
    def evaluate_batch(self, memories: List[Dict]) -> List[Dict]:
        """
        批量评估记忆
        
        Args:
            memories: 记忆列表
            
        Returns:
            评估结果列表
        """
        results = []
        for memory in memories:
            result = self.get_quality_report(memory)
            results.append(result)
        return results
    
    def get_quality_report(self, memory: Dict) -> Dict:
        """
        获取质量报告
        
        Args:
            memory: 记忆字典
            
        Returns:
            质量报告字典
        """
        confidence = self.evaluate(memory)
        
        return {
            'memory_id': memory.get('id'),
            'title': memory.get('title', 'N/A'),
            'confidence': round(confidence, 3),
            'quality_level': self._get_quality_level(confidence),
            'details': {
                'source': round(self._evaluate_source(memory), 3),
                'content': round(self._evaluate_content_quality(memory.get('content', '')), 3),
                'consistency': round(self._evaluate_consistency(memory), 3),
                'freshness': round(self._evaluate_freshness(memory), 3),
                'validation': round(self._evaluate_validation_status(memory), 3)
            },
            'suggestions': self._get_improvement_suggestions(memory, confidence)
        }
    
    def _evaluate_source(self, memory: Dict) -> float:
        """
        评估来源可信度
        
        Args:
            memory: 记忆字典
            
        Returns:
            来源分数 (0-1)
        """
        source = memory.get('source', 'unknown')
        return self.SOURCE_SCORES.get(source, 0.30)
    
    def _evaluate_content_quality(self, content: str) -> float:
        """
        评估内容质量
        
        Args:
            content: 内容字符串
            
        Returns:
            内容质量分数 (0-1)
        """
        if not content:
            return 0.0
        
        score = 0.3
        
        content_len = len(content)
        if 50 <= content_len <= 1000:
            score += 0.2
        elif 1000 < content_len <= 2000:
            score += 0.15
        elif content_len > 2000:
            score += 0.1
        
        if re.search(r'\d+', content):
            score += 0.1
        
        if re.search(r'```[\s\S]*?```|`[^`]+`', content):
            score += 0.1
        
        if re.search(r'^[-•*]\s', content, re.MULTILINE):
            score += 0.1
        
        if re.search(r'^#+\s', content, re.MULTILINE):
            score += 0.1
        
        if not self._contains_noise(content):
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_consistency(self, memory: Dict) -> float:
        """
        评估一致性
        
        Args:
            memory: 记忆字典
            
        Returns:
            一致性分数 (0-1)
        """
        if not self.store:
            return 0.7
        
        if not memory.get('id'):
            return 0.8
        
        try:
            if hasattr(self.store, 'find_related_memories'):
                related = self.store.find_related_memories(memory['id'])
            else:
                return 0.7
            
            contradictions = 0
            for rel in related[:10]:
                if self._is_contradiction(memory, rel):
                    contradictions += 1
            
            if contradictions == 0:
                return 1.0
            elif contradictions == 1:
                return 0.7
            else:
                return 0.4
        except Exception:
            return 0.7
    
    def _evaluate_freshness(self, memory: Dict) -> float:
        """
        评估时效性
        
        Args:
            memory: 记忆字典
            
        Returns:
            时效性分数 (0-1)
        """
        created_at = memory.get('created_at')
        if not created_at:
            return 0.5
        
        try:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif isinstance(created_at, datetime):
                pass
            else:
                return 0.5
            
            days_old = (datetime.now(created_at.tzinfo) - created_at).days if created_at.tzinfo else (datetime.now() - created_at).days
            
            if days_old <= 7:
                return 1.0
            elif days_old <= 30:
                return 0.9
            elif days_old <= 90:
                return 0.7
            elif days_old <= 365:
                return 0.5
            else:
                return 0.3
        except Exception:
            return 0.5
    
    def _evaluate_validation_status(self, memory: Dict) -> float:
        """
        评估验证状态
        
        Args:
            memory: 记忆字典
            
        Returns:
            验证状态分数 (0-1)
        """
        if memory.get('verified'):
            return 0.9
        
        if memory.get('validation_status') == 'passed':
            return 0.8
        elif memory.get('validation_status') == 'pending':
            return 0.5
        elif memory.get('validation_status') == 'failed':
            return 0.3
        
        return 0.5
    
    def _get_quality_level(self, confidence: float) -> str:
        """
        获取质量等级
        
        Args:
            confidence: 置信度分数
            
        Returns:
            质量等级字符串
        """
        for (low, high), level in self.QUALITY_LEVELS.items():
            if low <= confidence < high:
                return level
        return '低质量'
    
    def _contains_noise(self, content: str) -> bool:
        """
        检查是否包含噪音
        
        Args:
            content: 内容字符串
            
        Returns:
            是否包含噪音
        """
        for pattern in self.NOISE_PATTERNS:
            if re.match(pattern, content.strip()):
                return True
        return False
    
    def _is_contradiction(self, mem1: Dict, mem2: Dict) -> bool:
        """
        检查两个记忆是否矛盾
        
        Args:
            mem1: 记忆1
            mem2: 记忆2
            
        Returns:
            是否矛盾
        """
        contradiction_keywords = ['不', '非', '错误', '禁止', '不要', '避免']
        
        content1 = mem1.get('content', '').lower()
        content2 = mem2.get('content', '').lower()
        
        for keyword in contradiction_keywords:
            if keyword in content1 and keyword not in content2:
                return True
            if keyword in content2 and keyword not in content1:
                return True
        
        return False
    
    def _get_improvement_suggestions(self, memory: Dict, confidence: float) -> List[str]:
        """
        获取改进建议
        
        Args:
            memory: 记忆字典
            confidence: 置信度分数
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        if confidence < 0.6:
            suggestions.append("置信度较低，建议补充更多详细信息")
        
        content = memory.get('content', '')
        if len(content) < 50:
            suggestions.append("内容过短，建议补充详细说明或示例")
        
        if not memory.get('title') or len(memory.get('title', '')) < 10:
            suggestions.append("标题不够具体，建议使用更描述性的标题")
        
        if re.search(r'```[\s\S]*?```|`[^`]+`', content):
            if not re.search(r'```\w+', content):
                suggestions.append("代码块未指定语言，建议添加语言标识（如 ```python）")
        
        if not memory.get('tags') or len(memory.get('tags', [])) < 2:
            suggestions.append("标签较少，建议添加 2-3 个相关标签便于检索")
        
        if not re.search(r'\n\n', content):
            suggestions.append("内容为单一段落，建议分段提高可读性")
        
        if not memory.get('source'):
            suggestions.append("未标记来源，建议标记记忆来源以提高可信度")
        
        return suggestions


def main():
    """测试函数"""
    test_memories = [
        {
            'id': 1,
            'title': 'Python 函数定义指南',
            'content': '''
在 Python 中定义函数的最佳实践：

1. 使用有意义的函数名
2. 添加文档字符串
3. 使用类型注解

```python
def calculate_sum(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b
```

注意事项：
- 避免使用单字母函数名
- 函数应该只做一件事
- 保持函数简短（不超过 50 行）
            ''',
            'tags': ['python', '函数', '最佳实践'],
            'source': 'user_explicit',
            'created_at': datetime.now().isoformat(),
            'verified': True
        },
        {
            'id': 2,
            'title': '测试',
            'content': '内容太短',
            'tags': [],
            'source': 'unknown',
            'created_at': '2025-01-01T00:00:00'
        },
        {
            'id': 3,
            'title': 'React Hooks 使用规范',
            'content': '''
React Hooks 最佳实践：

## 基本规则
- 只在顶层调用 Hooks
- 只在 React 函数中调用 Hooks

## 常用 Hooks
1. useState - 状态管理
2. useEffect - 副作用处理
3. useContext - 上下文访问

## 示例代码
```javascript
const [count, setCount] = useState(0);

useEffect(() => {
    document.title = `Count: ${count}`;
}, [count]);
```
            ''',
            'tags': ['react', 'hooks', 'frontend'],
            'source': 'project_file',
            'created_at': datetime.now().isoformat(),
            'validation_status': 'passed'
        }
    ]
    
    evaluator = ConfidenceEvaluator()
    
    print("=" * 60)
    print("置信度评估测试")
    print("=" * 60)
    
    for memory in test_memories:
        report = evaluator.get_quality_report(memory)
        
        print(f"\n📝 记忆 #{report['memory_id']}: {report['title']}")
        print(f"   置信度：{report['confidence']:.3f} ({report['quality_level']})")
        print(f"   详细评分：")
        for key, value in report['details'].items():
            print(f"     - {key}: {value:.3f}")
        
        if report['suggestions']:
            print(f"   改进建议：")
            for i, suggestion in enumerate(report['suggestions'], 1):
                print(f"     {i}. {suggestion}")


if __name__ == '__main__':
    main()
