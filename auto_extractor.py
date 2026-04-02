#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动记忆提取器 - 从对话中自动提取关键信息
支持基于规则和 LLM 增强的提取
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime


class AutoMemoryExtractor:
    """
    自动记忆提取器
    
    功能：
    - 从对话中自动提取记忆
    - 支持基于规则的提取
    - 可选 LLM 增强
    - 置信度计算
    - 去重机制
    """
    
    EXTRACTION_PATTERNS = {
        'error': {
            'patterns': [
                r'错误[：:]\s*(.+?)(?:\n|$)',
                r'问题[：:]\s*(.+?)(?:\n|$)',
                r'报错[：:]\s*(.+?)(?:\n|$)',
                r'失败[：:]\s*(.+?)(?:\n|$)',
                r'异常[：:]\s*(.+?)(?:\n|$)',
            ],
            'confidence_base': 0.7,
            'keywords': ['错误', '问题', '报错', '失败', '异常', 'bug', 'error']
        },
        'solution': {
            'patterns': [
                r'解决[：:]\s*(.+?)(?:\n|$)',
                r'修复[：:]\s*(.+?)(?:\n|$)',
                r'方法[：:]\s*(.+?)(?:\n|$)',
                r'方案[：:]\s*(.+?)(?:\n|$)',
            ],
            'confidence_base': 0.8,
            'keywords': ['解决', '修复', '方法', '方案', 'solution', 'fix']
        },
        'preference': {
            'patterns': [
                r'我喜欢(.+?)(?:\n|$)',
                r'我习惯(.+?)(?:\n|$)',
                r'请使用(.+?)(?:\n|$)',
                r'偏好[：:]\s*(.+?)(?:\n|$)',
            ],
            'confidence_base': 0.8,
            'keywords': ['喜欢', '习惯', '偏好', '请使用', 'prefer']
        },
        'rule': {
            'patterns': [
                r'规范[：:]\s*(.+?)(?:\n|$)',
                r'要求[：:]\s*(.+?)(?:\n|$)',
                r'必须(.+?)(?:\n|$)',
                r'禁止(.+?)(?:\n|$)',
                r'约定[：:]\s*(.+?)(?:\n|$)',
                r'项目规范[：:]\s*(.+?)(?:\n|$)',
                r'代码规范[：:]\s*(.+?)(?:\n|$)',
            ],
            'confidence_base': 0.9,
            'keywords': ['规范', '要求', '必须', '禁止', '约定', 'rule', '项目规范', '代码规范']
        },
        'fact': {
            'patterns': [
                r'事实[：:]\s*(.+?)(?:\n|$)',
                r'注意[：:]\s*(.+?)(?:\n|$)',
                r'提示[：:]\s*(.+?)(?:\n|$)',
                r'说明[：:]\s*(.+?)(?:\n|$)',
            ],
            'confidence_base': 0.7,
            'keywords': ['事实', '注意', '提示', '说明', 'fact', 'note']
        }
    }
    
    SKIP_PATTERNS = [
        r'^(好的|收到|明白|谢谢|了解|清楚)',
        r'^(你好|您好|在吗|嗨)',
        r'^(是|否|对|错|嗯|哦)',
        r'^.{0,15}$',
    ]
    
    def __init__(self, memory_store=None, llm_client=None):
        """
        初始化自动记忆提取器
        
        Args:
            memory_store: MemoryStore 实例（可选，用于去重）
            llm_client: LLM 客户端（可选，用于增强提取）
        """
        self.store = memory_store
        self.llm_client = llm_client
    
    def extract_from_conversation(self, conversation: List[Dict]) -> List[Dict]:
        """
        从对话中提取记忆
        
        Args:
            conversation: 对话列表
            
        Returns:
            提取的记忆列表
        """
        if not self.should_extract(conversation):
            return []
        
        all_memories = []
        
        for turn in conversation:
            user_msg = turn.get('user_message', '')
            ai_response = turn.get('ai_response', '')
            
            turn_memories = self._extract_from_turn(user_msg, ai_response, turn)
            all_memories.extend(turn_memories)
        
        unique_memories = self._deduplicate(all_memories)
        
        return unique_memories
    
    def _extract_from_turn(self, user_msg: str, ai_response: str, turn: Dict) -> List[Dict]:
        """
        从单轮对话提取记忆
        
        Args:
            user_msg: 用户消息
            ai_response: AI 响应
            turn: 对话轮次信息
            
        Returns:
            提取的记忆列表
        """
        memories = []
        
        combined_text = f"{user_msg}\n{ai_response}"
        
        for category, config in self.EXTRACTION_PATTERNS.items():
            category_memories = self._extract_by_category(
                combined_text, 
                category, 
                config
            )
            memories.extend(category_memories)
        
        if '错误' in user_msg or '问题' in user_msg:
            if '解决' in ai_response or '方法' in ai_response:
                memory = self._extract_error_solution(user_msg, ai_response, turn)
                if memory:
                    memories.append(memory)
        
        for memory in memories:
            memory['source'] = 'auto_extract'
            memory['extracted_at'] = datetime.now().isoformat()
            if turn.get('session_id'):
                memory['session_id'] = turn['session_id']
        
        return memories
    
    def _extract_by_category(self, text: str, category: str, config: Dict) -> List[Dict]:
        """
        按类别提取记忆
        
        Args:
            text: 文本内容
            category: 类别
            config: 配置信息
            
        Returns:
            提取的记忆列表
        """
        memories = []
        
        for pattern in config['patterns']:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                content = match.group(1).strip()
                
                if len(content) < 10:
                    continue
                
                if self._is_noise(content):
                    continue
                
                confidence = self._calculate_confidence(content, config['confidence_base'])
                
                title = self._generate_title(category, content)
                
                memory = {
                    'category': category,
                    'title': title,
                    'content': content,
                    'confidence': confidence,
                    'tags': self._extract_tags(content, category)
                }
                
                memories.append(memory)
        
        return memories
    
    def _extract_error_solution(self, user_msg: str, ai_response: str, turn: Dict) -> Optional[Dict]:
        """
        提取错误-解决方案对
        
        Args:
            user_msg: 用户消息
            ai_response: AI 响应
            turn: 对话轮次信息
            
        Returns:
            提取的记忆或 None
        """
        error_match = re.search(r'(错误|问题|报错)[：:]\s*(.+?)(?:\n|$)', user_msg)
        if not error_match:
            return None
        
        error_desc = error_match.group(2).strip()
        
        solution_patterns = [
            r'(解决|方法|方案)[：:]\s*(.+?)(?:\n\n|\Z)',
            r'(可以使用|建议|推荐)(.+?)(?:\n\n|\Z)',
        ]
        
        solution = None
        for pattern in solution_patterns:
            solution_match = re.search(pattern, ai_response, re.DOTALL)
            if solution_match:
                solution = solution_match.group(2).strip()
                break
        
        if not solution:
            return None
        
        content = f"问题：{error_desc}\n\n解决方案：{solution}"
        
        return {
            'category': 'error',
            'title': f"解决：{error_desc[:30]}",
            'content': content,
            'confidence': 0.85,
            'tags': ['错误解决', '踩坑']
        }
    
    def _calculate_confidence(self, content: str, base_confidence: float) -> float:
        """
        计算置信度
        
        Args:
            content: 内容
            base_confidence: 基础置信度
            
        Returns:
            置信度分数
        """
        confidence = base_confidence
        
        if len(content) >= 50:
            confidence += 0.05
        if len(content) >= 100:
            confidence += 0.05
        
        if re.search(r'\d+', content):
            confidence += 0.03
        
        if re.search(r'```[\s\S]*?```|`[^`]+`', content):
            confidence += 0.05
        
        if re.search(r'^[-•*]\s', content, re.MULTILINE):
            confidence += 0.02
        
        return min(confidence, 1.0)
    
    def _generate_title(self, category: str, content: str) -> str:
        """
        生成标题
        
        Args:
            category: 类别
            content: 内容
            
        Returns:
            标题
        """
        category_titles = {
            'error': '错误记录',
            'solution': '解决方案',
            'preference': '用户偏好',
            'rule': '项目规范',
            'fact': '事实记录'
        }
        
        prefix = category_titles.get(category, '记忆')
        
        first_line = content.split('\n')[0]
        
        if len(first_line) > 40:
            title = f"{prefix}：{first_line[:37]}..."
        else:
            title = f"{prefix}：{first_line}"
        
        return title
    
    def _extract_tags(self, content: str, category: str) -> List[str]:
        """
        提取标签
        
        Args:
            content: 内容
            category: 类别
            
        Returns:
            标签列表
        """
        tags = [category]
        
        tech_keywords = {
            'python': ['python', 'pip', 'django', 'flask', 'numpy', 'pandas'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis'],
            'git': ['git', 'github', 'commit', 'branch', 'merge'],
            'docker': ['docker', 'container', 'kubernetes', 'k8s'],
        }
        
        content_lower = content.lower()
        for tech, keywords in tech_keywords.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(tech)
        
        return tags[:5]
    
    def _is_noise(self, text: str) -> bool:
        """
        检查是否为噪音
        
        Args:
            text: 文本
            
        Returns:
            是否为噪音
        """
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, text.strip()):
                return True
        return False
    
    def _deduplicate(self, memories: List[Dict]) -> List[Dict]:
        """
        去重
        
        Args:
            memories: 记忆列表
            
        Returns:
            去重后的记忆列表
        """
        unique_memories = []
        seen_content = set()
        
        for memory in memories:
            content_key = memory['content'][:100].lower()
            
            if content_key in seen_content:
                continue
            
            if self.store and hasattr(self.store, 'search_memories'):
                existing = self.store.search_memories(memory['content'][:50], limit=1)
                if existing and self._is_similar(memory['content'], existing[0].get('content', '')):
                    continue
            
            seen_content.add(content_key)
            unique_memories.append(memory)
        
        return unique_memories
    
    def _is_similar(self, text1: str, text2: str) -> bool:
        """
        检查文本相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            是否相似
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union)
        
        return similarity > 0.8
    
    def should_extract(self, conversation: List[Dict]) -> bool:
        """
        判断是否需要提取
        
        Args:
            conversation: 对话列表
            
        Returns:
            是否需要提取
        """
        if not conversation:
            return False
        
        for turn in conversation:
            user_msg = turn.get('user_message', '')
            if any(kw in user_msg for kw in ['规范', '要求', '必须', '禁止', '错误', '问题', '偏好', '喜欢']):
                return True
        
        total_length = sum(
            len(turn.get('user_message', '')) + len(turn.get('ai_response', ''))
            for turn in conversation
        )
        
        if total_length < 50:
            return False
        
        return True
    
    def extract_facts(self, text: str) -> List[str]:
        """
        提取事实信息
        
        Args:
            text: 文本
            
        Returns:
            事实列表
        """
        facts = []
        
        patterns = [
            r'事实[：:]\s*(.+?)(?:\n|$)',
            r'注意[：:]\s*(.+?)(?:\n|$)',
            r'提示[：:]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                fact = match.group(1).strip()
                if len(fact) >= 10:
                    facts.append(fact)
        
        return facts
    
    def extract_preferences(self, text: str) -> List[str]:
        """
        提取用户偏好
        
        Args:
            text: 文本
            
        Returns:
            偏好列表
        """
        preferences = []
        
        patterns = [
            r'我喜欢(.+?)(?:\n|$)',
            r'我习惯(.+?)(?:\n|$)',
            r'偏好[：:]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                pref = match.group(1).strip()
                if len(pref) >= 5:
                    preferences.append(pref)
        
        return preferences
    
    def extract_errors(self, text: str) -> List[Dict]:
        """
        提取错误和解决方案
        
        Args:
            text: 文本
            
        Returns:
            错误列表
        """
        errors = []
        
        error_pattern = r'(错误|问题|报错)[：:]\s*(.+?)(?:\n|$)'
        solution_pattern = r'(解决|方法|方案)[：:]\s*(.+?)(?:\n|$)'
        
        error_matches = list(re.finditer(error_pattern, text, re.MULTILINE))
        solution_matches = list(re.finditer(solution_pattern, text, re.MULTILINE))
        
        for i, error_match in enumerate(error_matches):
            error_desc = error_match.group(2).strip()
            
            solution = None
            if i < len(solution_matches):
                solution = solution_matches[i].group(2).strip()
            
            errors.append({
                'error': error_desc,
                'solution': solution
            })
        
        return errors
    
    def extract_rules(self, text: str) -> List[str]:
        """
        提取项目规范
        
        Args:
            text: 文本
            
        Returns:
            规范列表
        """
        rules = []
        
        patterns = [
            r'规范[：:]\s*(.+?)(?:\n|$)',
            r'要求[：:]\s*(.+?)(?:\n|$)',
            r'必须(.+?)(?:\n|$)',
            r'禁止(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                rule = match.group(1).strip()
                if len(rule) >= 5:
                    rules.append(rule)
        
        return rules


def main():
    """测试函数"""
    test_conversation = [
        {
            'turn_number': 1,
            'user_message': '我在使用 Python 读取 JSON 文件时遇到了编码错误',
            'ai_response': '''遇到编码错误可以尝试以下解决方法：

解决：在打开文件时指定 encoding 参数

```python
import json

with open('file.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
```

注意：如果文件是 GBK 编码，需要使用 encoding='gbk' ''',
            'session_id': 1
        },
        {
            'turn_number': 2,
            'user_message': '我喜欢使用 4 个空格缩进，而不是 Tab',
            'ai_response': '好的，我会记住你的偏好。使用 4 个空格缩进是 Python 的官方推荐风格（PEP 8）。',
            'session_id': 1
        },
        {
            'turn_number': 3,
            'user_message': '项目规范：所有函数必须添加文档字符串',
            'ai_response': '已记录项目规范。添加文档字符串是很好的实践，可以使用 docstring 自动生成文档。',
            'session_id': 1
        }
    ]
    
    extractor = AutoMemoryExtractor()
    
    print("=" * 60)
    print("自动记忆提取测试")
    print("=" * 60)
    
    memories = extractor.extract_from_conversation(test_conversation)
    
    print(f"\n✅ 提取到 {len(memories)} 条记忆：\n")
    
    for i, memory in enumerate(memories, 1):
        print(f"📝 记忆 #{i}")
        print(f"   类别：{memory['category']}")
        print(f"   标题：{memory['title']}")
        print(f"   内容：{memory['content'][:80]}...")
        print(f"   置信度：{memory['confidence']:.2f}")
        print(f"   标签：{', '.join(memory['tags'])}")
        print()


if __name__ == '__main__':
    main()
