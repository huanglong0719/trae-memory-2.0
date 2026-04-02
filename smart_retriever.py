#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能记忆检索器 - 多层次检索策略
优先项目记忆，支持跨项目全局检索
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class SmartMemoryRetriever:
    """
    智能记忆检索器
    
    检索策略：
    1. 项目记忆优先 - 先检索当前项目
    2. 全局记忆补充 - 跨项目检索所有相关记忆
    3. 相关性排序 - 按相关度排序结果
    4. 上下文增强 - 结合会话上下文
    """
    
    def __init__(self, integrated_manager=None):
        """
        初始化智能检索器
        
        Args:
            integrated_manager: IntegratedMemoryManager 实例
        """
        self.manager = integrated_manager
    
    def search(self, query: str, scope: str = 'auto', 
               limit: int = 10) -> Dict:
        """
        智能检索记忆
        
        Args:
            query: 检索关键词
            scope: 检索范围 ('project', 'global', 'auto')
            limit: 结果限制
            
        Returns:
            检索结果字典
        """
        if scope == 'auto':
            results = self._auto_search(query, limit)
        elif scope == 'project':
            results = self._project_search(query, limit)
        else:
            results = self._global_search(query, limit)
        
        return results
    
    def _auto_search(self, query: str, limit: int) -> Dict:
        """
        自动检索策略
        
        优先级：
        1. 当前项目记忆
        2. 相关项目记忆
        3. 全局记忆
        
        Args:
            query: 检索关键词
            limit: 结果限制
            
        Returns:
            检索结果
        """
        results = {
            'query': query,
            'project_results': [],
            'global_results': [],
            'total': 0,
            'strategy': 'auto'
        }
        
        project_limit = limit // 2
        project_results = self._project_search(query, project_limit)
        results['project_results'] = project_results.get('results', [])
        
        remaining = limit - len(results['project_results'])
        if remaining > 0:
            global_results = self._global_search(query, remaining)
            results['global_results'] = global_results.get('results', [])
        
        results['total'] = len(results['project_results']) + len(results['global_results'])
        
        return results
    
    def _project_search(self, query: str, limit: int) -> Dict:
        """
        项目记忆检索
        
        Args:
            query: 检索关键词
            limit: 结果限制
            
        Returns:
            检索结果
        """
        results = {
            'query': query,
            'results': [],
            'total': 0,
            'scope': 'project'
        }
        
        if not self.manager:
            return results
        
        current_project = self.manager.registry.get_current_project()
        if not current_project:
            return results
        
        project_id = current_project['id']
        manager = self.manager._get_project_manager(project_id)
        
        if not manager:
            return results
        
        memory = manager.load_project_memory()
        
        searchable_fields = {
            'description': memory.get('description', ''),
            'tech_stack': ' '.join(memory.get('tech_stack', [])),
            'dependencies': ' '.join(memory.get('dependencies', [])),
            'code_style': memory.get('code_style', ''),
            'test_framework': memory.get('test_framework', ''),
            'issues': ' '.join(memory.get('issues', [])),
            'decisions': ' '.join(memory.get('decisions', [])),
        }
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        matched_results = []
        
        for field, content in searchable_fields.items():
            if not content:
                continue
            
            content_lower = content.lower()
            
            if query_lower in content_lower:
                relevance = self._calculate_relevance(query, content)
                
                matched_results.append({
                    'source': 'project',
                    'project_id': project_id,
                    'project_name': current_project['name'],
                    'field': field,
                    'content': content[:200],
                    'relevance': relevance,
                    'match_type': 'exact' if query_lower in content_lower else 'partial'
                })
        
        matched_results.sort(key=lambda x: x['relevance'], reverse=True)
        results['results'] = matched_results[:limit]
        results['total'] = len(matched_results)
        
        return results
    
    def _global_search(self, query: str, limit: int) -> Dict:
        """
        全局记忆检索
        
        Args:
            query: 检索关键词
            limit: 结果限制
            
        Returns:
            检索结果（仅返回相关记忆）
        """
        results = {
            'query': query,
            'results': [],
            'total': 0,
            'scope': 'global'
        }
        
        if not self.manager:
            return results
        
        all_results = []
        
        for project_id, project in self.manager.registry.projects.items():
            manager = self.manager._get_project_manager(project_id)
            if not manager:
                continue
            
            memory = manager.load_project_memory()
            
            searchable_fields = {
                'description': memory.get('description', ''),
                'tech_stack': ' '.join(memory.get('tech_stack', [])),
                'dependencies': ' '.join(memory.get('dependencies', [])),
                'issues': ' '.join(memory.get('issues', [])),
                'decisions': ' '.join(memory.get('decisions', [])),
            }
            
            query_lower = query.lower()
            
            for field, content in searchable_fields.items():
                if not content:
                    continue
                
                content_lower = content.lower()
                
                if query_lower in content_lower:
                    relevance = self._calculate_relevance(query, content)
                    
                    is_current = (project_id == self.manager.registry.current_project_id)
                    
                    all_results.append({
                        'source': 'global',
                        'project_id': project_id,
                        'project_name': project['name'],
                        'field': field,
                        'content': content[:200],
                        'relevance': relevance * (1.2 if is_current else 1.0),
                        'match_type': 'exact',
                        'is_current_project': is_current
                    })
        
        all_results.sort(key=lambda x: x['relevance'], reverse=True)
        results['results'] = all_results[:limit]
        results['total'] = len(all_results)
        
        return results
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """
        计算相关性分数
        
        Args:
            query: 查询词
            content: 内容
            
        Returns:
            相关性分数 (0-1)
        """
        query_lower = query.lower()
        content_lower = content.lower()
        
        score = 0.0
        
        if query_lower in content_lower:
            score += 0.5
            
            positions = []
            start = 0
            while True:
                pos = content_lower.find(query_lower, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            if positions:
                first_pos = positions[0]
                max_pos = len(content_lower)
                position_score = 1.0 - (first_pos / max_pos)
                score += position_score * 0.2
                
                frequency_score = min(len(positions) * 0.1, 0.3)
                score += frequency_score
        
        query_terms = set(query_lower.split())
        content_terms = set(content_lower.split())
        
        if query_terms:
            overlap = len(query_terms & content_terms)
            term_score = overlap / len(query_terms) * 0.2
            score += term_score
        
        return min(score, 1.0)
    
    def get_context_aware_results(self, query: str, 
                                   session_context: List[Dict] = None,
                                   limit: int = 10) -> Dict:
        """
        获取上下文感知的检索结果
        
        Args:
            query: 查询词
            session_context: 会话上下文
            limit: 结果限制
            
        Returns:
            检索结果
        """
        results = self.search(query, scope='auto', limit=limit)
        
        if session_context:
            context_terms = self._extract_context_terms(session_context)
            
            for result in results.get('project_results', []):
                context_boost = self._calculate_context_boost(
                    result['content'], 
                    context_terms
                )
                result['relevance'] = min(result['relevance'] + context_boost * 0.1, 1.0)
                result['context_boost'] = context_boost
            
            for result in results.get('global_results', []):
                context_boost = self._calculate_context_boost(
                    result['content'], 
                    context_terms
                )
                result['relevance'] = min(result['relevance'] + context_boost * 0.1, 1.0)
                result['context_boost'] = context_boost
            
            results['project_results'].sort(key=lambda x: x['relevance'], reverse=True)
            results['global_results'].sort(key=lambda x: x['relevance'], reverse=True)
        
        return results
    
    def _extract_context_terms(self, session_context: List[Dict]) -> set:
        """
        从会话上下文提取关键词
        
        Args:
            session_context: 会话上下文
            
        Returns:
            关键词集合
        """
        terms = set()
        
        for turn in session_context[-5:]:
            user_msg = turn.get('user_message', '')
            ai_response = turn.get('ai_response', '')
            
            combined = f"{user_msg} {ai_response}"
            
            words = re.findall(r'\b\w{3,}\b', combined.lower())
            terms.update(words)
        
        return terms
    
    def _calculate_context_boost(self, content: str, context_terms: set) -> float:
        """
        计算上下文增强分数
        
        Args:
            content: 内容
            context_terms: 上下文关键词
            
        Returns:
            增强分数
        """
        content_terms = set(content.lower().split())
        
        if not context_terms:
            return 0.0
        
        overlap = len(content_terms & context_terms)
        return overlap / len(context_terms)
    
    def suggest_related(self, query: str, limit: int = 5) -> List[str]:
        """
        建议相关搜索词
        
        Args:
            query: 原始查询
            limit: 建议数量
            
        Returns:
            相关搜索词列表
        """
        suggestions = []
        
        if not self.manager:
            return suggestions
        
        all_terms = set()
        
        for project_id in self.manager.registry.projects:
            manager = self.manager._get_project_manager(project_id)
            if not manager:
                continue
            
            memory = manager.load_project_memory()
            
            for field in ['tech_stack', 'dependencies', 'issues', 'decisions']:
                items = memory.get(field, [])
                if isinstance(items, list):
                    for item in items:
                        words = re.findall(r'\b\w{3,}\b', str(item).lower())
                        all_terms.update(words)
        
        query_lower = query.lower()
        
        for term in all_terms:
            if term != query_lower and query_lower in term:
                suggestions.append(term)
            elif term != query_lower and term in query_lower:
                suggestions.append(term)
        
        return suggestions[:limit]
    
    def get_search_stats(self) -> Dict:
        """
        获取检索统计信息
        
        Returns:
            统计字典
        """
        stats = {
            'total_projects': 0,
            'total_memories': 0,
            'searchable_fields': [
                'description', 'tech_stack', 'dependencies',
                'issues', 'decisions', 'code_style'
            ]
        }
        
        if not self.manager:
            return stats
        
        stats['total_projects'] = len(self.manager.registry.projects)
        
        for project_id in self.manager.registry.projects:
            manager = self.manager._get_project_manager(project_id)
            if manager:
                memory = manager.load_project_memory()
                stats['total_memories'] += len([
                    v for v in memory.values() 
                    if v and not isinstance(v, (list, dict))
                ])
        
        return stats


def main():
    """测试函数"""
    from integrated_memory_manager import IntegratedMemoryManager
    
    print("=" * 60)
    print("智能记忆检索测试")
    print("=" * 60)
    
    imm = IntegratedMemoryManager(auto_detect=False)
    retriever = SmartMemoryRetriever(imm)
    
    print("\n📊 检索统计:")
    stats = retriever.get_search_stats()
    print(f"   总项目数: {stats['total_projects']}")
    print(f"   可搜索字段: {', '.join(stats['searchable_fields'])}")
    
    print("\n🔍 测试项目检索:")
    result = retriever.search("Python", scope='project', limit=5)
    print(f"   查询: {result['query']}")
    print(f"   结果数: {result['total']}")
    
    if result['results']:
        print("   匹配结果:")
        for i, r in enumerate(result['results'][:3], 1):
            print(f"     {i}. [{r['field']}] {r['content'][:50]}...")
            print(f"        相关性: {r['relevance']:.3f}")
    
    print("\n🔍 测试全局检索:")
    result = retriever.search("记忆", scope='global', limit=5)
    print(f"   查询: {result['query']}")
    print(f"   结果数: {result['total']}")
    
    if result['results']:
        print("   匹配结果:")
        for i, r in enumerate(result['results'][:3], 1):
            print(f"     {i}. [{r['project_name']}] {r['content'][:50]}...")
            print(f"        相关性: {r['relevance']:.3f}")
    
    print("\n🔍 测试自动检索:")
    result = retriever.search("Python", scope='auto', limit=10)
    print(f"   查询: {result['query']}")
    print(f"   项目结果: {len(result['project_results'])} 条")
    print(f"   全局结果: {len(result['global_results'])} 条")
    print(f"   总计: {result['total']} 条")
    
    print("\n💡 相关搜索建议:")
    suggestions = retriever.suggest_related("Python")
    for s in suggestions:
        print(f"   - {s}")


if __name__ == '__main__':
    main()
