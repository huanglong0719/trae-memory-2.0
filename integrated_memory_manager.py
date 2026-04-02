#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成记忆管理器 - 统一管理项目记忆和对话上下文
将对话上下文与项目关联保存
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class IntegratedMemoryManager:
    """
    集成记忆管理器
    
    功能：
    - 统一管理多项目记忆
    - 对话上下文与项目关联
    - 自动提取并保存到项目
    - 跨项目搜索
    - 自动检测新项目
    """
    
    def __init__(self, registry_path: str = None, auto_detect: bool = True):
        """
        初始化集成记忆管理器
        
        Args:
            registry_path: 注册表路径
            auto_detect: 是否自动检测新项目
        """
        from project_registry import ProjectRegistry
        from conversation_manager import ConversationManager
        from auto_extractor import AutoMemoryExtractor
        from confidence_evaluator import ConfidenceEvaluator
        
        self.registry = ProjectRegistry(registry_path)
        self.conversation_manager = ConversationManager()
        self.extractor = AutoMemoryExtractor()
        self.evaluator = ConfidenceEvaluator()
        self.auto_detect = auto_detect
        
        self._project_managers = {}
        
        if self.auto_detect:
            self._auto_detect_current_project()
    
    def _get_project_manager(self, project_id: str = None):
        """
        获取项目记忆管理器
        
        Args:
            project_id: 项目 ID
            
        Returns:
            ProjectMemoryManager 实例
        """
        if project_id is None:
            project_id = self.registry.current_project_id
        
        if project_id is None:
            return None
        
        if project_id not in self._project_managers:
            project = self.registry.get_project(project_id)
            if project:
                from project_memory import ProjectMemoryManager
                self._project_managers[project_id] = ProjectMemoryManager(project['path'])
        
        return self._project_managers.get(project_id)
    
    def _auto_detect_current_project(self):
        """
        自动检测当前工作目录对应的项目
        如果项目未注册，自动注册并创建记忆文件
        """
        from pathlib import Path
        
        current_path = str(Path.cwd())
        
        for project_id, project in self.registry.projects.items():
            if project['path'] == current_path:
                self.registry.switch_project(project_id)
                return
        
        project_indicators = [
            '.git', 'package.json', 'requirements.txt', 
            'pyproject.toml', 'Cargo.toml', 'go.mod',
            'pom.xml', 'build.gradle', '.trae'
        ]
        
        is_project = any(
            (Path(current_path) / indicator).exists() 
            for indicator in project_indicators
        )
        
        if is_project:
            print(f"🔍 检测到新项目: {Path(current_path).name}")
            project_id = self.register_project(current_path)
            print(f"✅ 已自动注册项目: {project_id}")
    
    def start_session(self, project_id: str = None) -> int:
        """
        开始项目会话
        
        Args:
            project_id: 项目 ID，默认为当前项目
            
        Returns:
            会话 ID
        """
        if project_id:
            self.registry.switch_project(project_id)
        
        current_project = self.registry.get_current_project()
        project_path = current_project['path'] if current_project else None
        
        session_id = self.conversation_manager.start_session(project_path)
        
        return session_id
    
    def add_conversation_turn(self, user_msg: str, ai_response: str,
                               tools_used: List[str] = None) -> Dict:
        """
        添加对话轮次并自动提取记忆
        
        Args:
            user_msg: 用户消息
            ai_response: AI 响应
            tools_used: 使用的工具列表
            
        Returns:
            处理结果
        """
        turn_id = self.conversation_manager.add_turn(
            user_msg, ai_response, tools_used
        )
        
        turn = {
            'turn_number': self.conversation_manager.get_context(limit=1)[-1].get('turn_number', 1),
            'user_message': user_msg,
            'ai_response': ai_response,
            'tools_used': tools_used,
            'session_id': self.conversation_manager.current_session_id
        }
        
        memories = self.extractor.extract_from_conversation([turn])
        
        saved_memories = []
        if memories:
            saved_memories = self._save_memories_to_project(memories)
        
        return {
            'turn_id': turn_id,
            'extracted_memories': len(memories),
            'saved_memories': len(saved_memories),
            'memories': saved_memories
        }
    
    def _save_memories_to_project(self, memories: List[Dict]) -> List[Dict]:
        """
        保存记忆到项目
        
        Args:
            memories: 记忆列表
            
        Returns:
            保存的记忆列表
        """
        saved = []
        
        manager = self._get_project_manager()
        if not manager:
            return saved
        
        project_memory = manager.load_project_memory()
        
        for memory in memories:
            report = self.evaluator.get_quality_report(memory)
            
            if report['confidence'] < 0.4:
                continue
            
            category = memory.get('category', 'fact')
            
            if category == 'rule':
                if 'decisions' not in project_memory:
                    project_memory['decisions'] = []
                project_memory['decisions'].append(memory['content'][:200])
            
            elif category == 'preference':
                if 'custom_preferences' not in project_memory:
                    project_memory['custom_preferences'] = {}
                project_memory['custom_preferences'][memory['title']] = memory['content']
            
            elif category == 'error':
                if 'issues' not in project_memory:
                    project_memory['issues'] = []
                issue_text = f"[{memory.get('title', '问题')}] {memory['content'][:150]}"
                if issue_text not in project_memory['issues']:
                    project_memory['issues'].append(issue_text)
            
            elif category == 'fact':
                if 'tech_stack' not in project_memory:
                    project_memory['tech_stack'] = []
                tags = memory.get('tags', [])
                for tag in tags:
                    if tag not in project_memory['tech_stack'] and len(project_memory['tech_stack']) < 10:
                        project_memory['tech_stack'].append(tag)
            
            saved.append({
                'category': category,
                'title': memory['title'],
                'confidence': report['confidence'],
                'saved_to': category
            })
        
        if saved:
            manager.save_project_memory(project_memory)
        
        return saved
    
    def end_session(self) -> Dict:
        """
        结束会话并保存摘要到项目
        
        Returns:
            结束结果
        """
        session_id = self.conversation_manager.current_session_id
        
        session_info = self.conversation_manager.get_session_info()
        turns = self.conversation_manager.get_full_history()
        
        self.conversation_manager.end_session()
        
        if turns:
            manager = self._get_project_manager()
            if manager:
                project_memory = manager.load_project_memory()
                
                summary = self._generate_session_summary(session_info, turns)
                
                if 'session_summaries' not in project_memory:
                    project_memory['session_summaries'] = []
                
                project_memory['session_summaries'].append({
                    'session_id': session_id,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'turns': len(turns),
                    'summary': summary
                })
                
                if len(project_memory['session_summaries']) > 10:
                    project_memory['session_summaries'] = project_memory['session_summaries'][-10:]
                
                manager.save_project_memory(project_memory)
        
        return {
            'session_id': session_id,
            'total_turns': len(turns),
            'saved': True
        }
    
    def _generate_session_summary(self, session_info: Dict, turns: List[Dict]) -> str:
        """
        生成会话摘要
        
        Args:
            session_info: 会话信息
            turns: 对话轮次
            
        Returns:
            摘要文本
        """
        topics = set()
        tools_used = set()
        
        for turn in turns:
            user_msg = turn.get('user_message', '')
            
            if '错误' in user_msg or '问题' in user_msg:
                topics.add('问题解决')
            if '如何' in user_msg or '怎么' in user_msg:
                topics.add('方法咨询')
            if '实现' in user_msg or '开发' in user_msg:
                topics.add('开发实现')
            
            if turn.get('tools_used'):
                tools_used.update(turn['tools_used'])
        
        parts = [f"共 {len(turns)} 轮对话"]
        
        if topics:
            parts.append(f"主题：{', '.join(topics)}")
        
        if tools_used:
            parts.append(f"使用工具：{', '.join(tools_used)}")
        
        return '；'.join(parts)
    
    def get_project_context(self, project_id: str = None) -> Dict:
        """
        获取项目上下文（记忆 + 最近对话）
        
        Args:
            project_id: 项目 ID
            
        Returns:
            上下文字典
        """
        manager = self._get_project_manager(project_id)
        
        project_memory = {}
        if manager:
            project_memory = manager.load_project_memory()
        
        recent_sessions = self._get_project_sessions(project_id, limit=3)
        
        return {
            'project_memory': project_memory,
            'recent_sessions': recent_sessions,
            'current_project': self.registry.get_current_project()
        }
    
    def _get_project_sessions(self, project_id: str = None, limit: int = 3) -> List[Dict]:
        """
        获取项目的最近会话
        
        Args:
            project_id: 项目 ID
            limit: 限制数量
            
        Returns:
            会话列表
        """
        project = self.registry.get_project(project_id)
        if not project:
            return []
        
        project_path = project['path']
        
        sessions = self.conversation_manager.list_sessions(limit=20)
        
        project_sessions = [
            s for s in sessions 
            if s.get('project_path') == project_path
        ][:limit]
        
        return project_sessions
    
    def switch_project(self, project_id: str) -> bool:
        """
        切换项目
        
        Args:
            project_id: 项目 ID
            
        Returns:
            是否成功
        """
        return self.registry.switch_project(project_id)
    
    def register_project(self, project_path: str, **kwargs) -> str:
        """
        注册新项目
        
        Args:
            project_path: 项目路径
            **kwargs: 其他参数
            
        Returns:
            项目 ID
        """
        project_id = self.registry.register_project(project_path, **kwargs)
        
        manager = self._get_project_manager(project_id)
        if manager:
            memory = manager.extract_from_project()
            manager.save_project_memory(memory)
        
        return project_id
    
    def list_projects(self) -> List[Dict]:
        """
        列出所有项目
        
        Returns:
            项目列表
        """
        return self.registry.list_projects()
    
    def search_across_projects(self, keyword: str) -> List[Dict]:
        """
        跨项目搜索
        
        Args:
            keyword: 关键词
            
        Returns:
            搜索结果
        """
        results = []
        
        for project_id in self.registry.projects:
            manager = self._get_project_manager(project_id)
            if not manager:
                continue
            
            memory = manager.load_project_memory()
            
            searchable = ' '.join([
                memory.get('description', ''),
                ' '.join(memory.get('tech_stack', [])),
                ' '.join(memory.get('dependencies', [])),
                ' '.join(memory.get('issues', [])),
                ' '.join(memory.get('decisions', []))
            ])
            
            if keyword.lower() in searchable.lower():
                project = self.registry.get_project(project_id)
                results.append({
                    'project_id': project_id,
                    'project_name': project['name'],
                    'project_path': project['path'],
                    'memory': memory
                })
        
        return results
    
    def export_project_memory(self, project_id: str = None, format: str = 'json') -> str:
        """
        导出项目记忆
        
        Args:
            project_id: 项目 ID
            format: 导出格式
            
        Returns:
            导出内容
        """
        manager = self._get_project_manager(project_id)
        if not manager:
            return ""
        
        memory = manager.load_project_memory()
        
        if format == 'json':
            return json.dumps(memory, indent=2, ensure_ascii=False)
        else:
            return manager.generate_memory_md(memory)
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        registry_stats = self.registry.get_stats()
        
        sessions = self.conversation_manager.list_sessions(limit=100)
        
        return {
            **registry_stats,
            'total_sessions': len(sessions),
            'project_managers_cached': len(self._project_managers)
        }
    
    def smart_search(self, query: str, scope: str = 'auto', 
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
        from smart_retriever import SmartMemoryRetriever
        
        retriever = SmartMemoryRetriever(self)
        return retriever.search(query, scope, limit)
    
    def search_project_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索当前项目记忆
        
        Args:
            query: 检索关键词
            limit: 结果限制
            
        Returns:
            搜索结果列表
        """
        result = self.smart_search(query, scope='project', limit=limit)
        return result.get('results', [])
    
    def search_all_memories(self, query: str, limit: int = 10) -> Dict:
        """
        跨项目搜索所有记忆
        
        Args:
            query: 检索关键词
            limit: 结果限制
            
        Returns:
            搜索结果字典
        """
        return self.smart_search(query, scope='auto', limit=limit)


def main():
    """测试函数"""
    print("=" * 60)
    print("集成记忆管理器测试")
    print("=" * 60)
    
    imm = IntegratedMemoryManager()
    
    print("\n📋 已注册项目:")
    projects = imm.list_projects()
    for p in projects:
        print(f"   - {p['name']} (ID: {p['id']})")
    
    if projects:
        project_id = projects[0]['id']
        imm.switch_project(project_id)
        print(f"\n✅ 切换到项目: {projects[0]['name']}")
    
    print("\n💬 开始会话...")
    session_id = imm.start_session()
    print(f"✅ 会话 ID: {session_id}")
    
    print("\n📝 添加对话...")
    result = imm.add_conversation_turn(
        user_msg="项目规范：所有 Python 文件必须添加类型注解",
        ai_response="好的，我会记住这个规范。类型注解可以提高代码可读性和 IDE 支持。",
        tools_used=['Read', 'Write']
    )
    print(f"✅ 提取记忆: {result['extracted_memories']} 条")
    print(f"✅ 保存记忆: {result['saved_memories']} 条")
    
    if result['memories']:
        print("\n📋 保存的记忆详情:")
        for mem in result['memories']:
            print(f"   - {mem['category']}: {mem['title']} (置信度: {mem['confidence']:.2f})")
    
    print("\n📊 项目上下文:")
    context = imm.get_project_context()
    print(f"   项目记忆: {len(context['project_memory'])} 个字段")
    print(f"   最近会话: {len(context['recent_sessions'])} 个")
    
    print("\n🔚 结束会话...")
    end_result = imm.end_session()
    print(f"✅ 会话结束: {end_result['total_turns']} 轮")
    
    print("\n📈 统计信息:")
    stats = imm.get_stats()
    print(f"   总项目数: {stats['total_projects']}")
    print(f"   总会话数: {stats['total_sessions']}")


if __name__ == '__main__':
    main()
