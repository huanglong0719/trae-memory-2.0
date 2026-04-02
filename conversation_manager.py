#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话历史管理器 - 追踪完整对话上下文
支持对话压缩和重播
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ConversationManager:
    """
    对话历史管理器
    
    功能：
    - 追踪完整对话上下文
    - 支持对话压缩和摘要
    - 会话管理和持久化
    - 对话重播功能
    """
    
    def __init__(self, db_path: str = None, max_turns: int = 12):
        """
        初始化对话管理器
        
        Args:
            db_path: 数据库路径
            max_turns: 最大保留轮数（超过后压缩）
        """
        if db_path is None:
            home_dir = str(Path.home())
            db_path = str(Path(home_dir) / ".trae" / "memory" / "trae_memory.db")
        
        self.db_path = db_path
        self.max_turns = max_turns
        self.current_session_id = None
        
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                total_turns INTEGER DEFAULT 0,
                summary TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                turn_number INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                tools_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_turns_session 
            ON conversation_turns(session_id, turn_number)
        ''')
        
        conn.commit()
        conn.close()
    
    def start_session(self, project_path: str = None) -> int:
        """
        开始新会话
        
        Args:
            project_path: 项目路径
            
        Returns:
            会话 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (project_path, started_at)
            VALUES (?, datetime('now'))
        ''', (project_path,))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.current_session_id = session_id
        print(f"✅ 开始新会话 #{session_id}")
        return session_id
    
    def end_session(self, session_id: int = None) -> bool:
        """
        结束会话
        
        Args:
            session_id: 会话 ID，默认为当前会话
            
        Returns:
            是否成功结束
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions 
            SET ended_at = datetime('now')
            WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
        if self.current_session_id == session_id:
            self.current_session_id = None
        
        print(f"✅ 结束会话 #{session_id}")
        return True
    
    def add_turn(self, user_msg: str, ai_response: str, 
                 tools_used: List[str] = None, session_id: int = None) -> int:
        """
        添加一轮对话
        
        Args:
            user_msg: 用户消息
            ai_response: AI 响应
            tools_used: 使用的工具列表
            session_id: 会话 ID，默认为当前会话
            
        Returns:
            对话轮次 ID
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            session_id = self.start_session()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM conversation_turns WHERE session_id = ?
        ''', (session_id,))
        turn_number = cursor.fetchone()[0] + 1
        
        cursor.execute('''
            INSERT INTO conversation_turns 
            (session_id, turn_number, user_message, ai_response, tools_used, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (session_id, turn_number, user_msg, ai_response, 
              json.dumps(tools_used or [], ensure_ascii=False)))
        
        turn_id = cursor.lastrowid
        
        cursor.execute('''
            UPDATE sessions SET total_turns = total_turns + 1 WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
        return turn_id
    
    def get_context(self, limit: int = None, session_id: int = None) -> List[Dict]:
        """
        获取对话上下文
        
        Args:
            limit: 限制轮数
            session_id: 会话 ID，默认为当前会话
            
        Returns:
            对话列表
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return []
        
        limit = limit or self.max_turns
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM conversation_turns 
            WHERE session_id = ?
            ORDER BY turn_number DESC
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        turns = []
        for row in reversed(rows):
            turn = dict(row)
            if turn['tools_used']:
                turn['tools_used'] = json.loads(turn['tools_used'])
            turns.append(turn)
        
        return turns
    
    def get_full_history(self, session_id: int = None) -> List[Dict]:
        """
        获取完整对话历史
        
        Args:
            session_id: 会话 ID，默认为当前会话
            
        Returns:
            完整对话列表
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM conversation_turns 
            WHERE session_id = ?
            ORDER BY turn_number ASC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        turns = []
        for row in rows:
            turn = dict(row)
            if turn['tools_used']:
                turn['tools_used'] = json.loads(turn['tools_used'])
            turns.append(turn)
        
        return turns
    
    def compact_history(self, session_id: int = None) -> Dict:
        """
        压缩历史对话
        
        Args:
            session_id: 会话 ID，默认为当前会话
            
        Returns:
            压缩结果
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return {'success': False, 'message': '无活动会话'}
        
        turns = self.get_full_history(session_id)
        
        if len(turns) <= self.max_turns:
            return {'success': True, 'message': '无需压缩', 'turns': len(turns)}
        
        old_turns = turns[:-self.max_turns]
        recent_turns = turns[-self.max_turns:]
        
        summary = self._generate_summary(old_turns)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions SET summary = ? WHERE id = ?
        ''', (summary, session_id))
        
        for turn in old_turns:
            cursor.execute('''
                DELETE FROM conversation_turns WHERE id = ?
            ''', (turn['id'],))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f'压缩完成，保留最近 {self.max_turns} 轮',
            'compressed_turns': len(old_turns),
            'summary': summary
        }
    
    def _generate_summary(self, turns: List[Dict]) -> str:
        """
        生成对话摘要
        
        Args:
            turns: 对话列表
            
        Returns:
            摘要文本
        """
        if not turns:
            return ""
        
        topics = set()
        tools_used = set()
        key_points = []
        
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
            
            if len(user_msg) > 20:
                first_sentence = user_msg.split('。')[0]
                if len(first_sentence) > 10:
                    key_points.append(first_sentence[:50])
        
        summary_parts = [f"共 {len(turns)} 轮对话"]
        
        if topics:
            summary_parts.append(f"主题：{', '.join(topics)}")
        
        if tools_used:
            summary_parts.append(f"使用工具：{', '.join(tools_used)}")
        
        if key_points:
            summary_parts.append("关键点：")
            for i, point in enumerate(key_points[:3], 1):
                summary_parts.append(f"  {i}. {point}")
        
        return '\n'.join(summary_parts)
    
    def get_session_info(self, session_id: int = None) -> Optional[Dict]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID，默认为当前会话
            
        Returns:
            会话信息字典
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return None
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sessions WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """
        列出最近的会话
        
        Args:
            limit: 限制数量
            
        Returns:
            会话列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sessions 
            ORDER BY started_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def search_conversations(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索对话内容
        
        Args:
            keyword: 关键词
            limit: 限制数量
            
        Returns:
            匹配的对话列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ct.*, s.project_path
            FROM conversation_turns ct
            JOIN sessions s ON ct.session_id = s.id
            WHERE ct.user_message LIKE ? OR ct.ai_response LIKE ?
            ORDER BY ct.created_at DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            if result['tools_used']:
                result['tools_used'] = json.loads(result['tools_used'])
            results.append(result)
        
        return results
    
    def export_session(self, session_id: int = None, format: str = 'json') -> str:
        """
        导出会话
        
        Args:
            session_id: 会话 ID，默认为当前会话
            format: 导出格式 (json/markdown)
            
        Returns:
            导出内容
        """
        session_id = session_id or self.current_session_id
        if not session_id:
            return ""
        
        session_info = self.get_session_info(session_id)
        turns = self.get_full_history(session_id)
        
        if format == 'json':
            export_data = {
                'session': session_info,
                'turns': turns
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        
        elif format == 'markdown':
            lines = [
                f"# 会话 #{session_id}",
                "",
                f"**开始时间：** {session_info.get('started_at', 'N/A')}",
                f"**总轮数：** {session_info.get('total_turns', 0)}",
                "",
            ]
            
            if session_info.get('summary'):
                lines.extend([
                    "## 摘要",
                    "",
                    session_info['summary'],
                    ""
                ])
            
            lines.append("## 对话记录")
            lines.append("")
            
            for turn in turns:
                lines.append(f"### 第 {turn['turn_number']} 轮")
                lines.append("")
                lines.append(f"**用户：** {turn['user_message']}")
                lines.append("")
                lines.append(f"**AI：** {turn['ai_response']}")
                
                if turn.get('tools_used'):
                    lines.append("")
                    lines.append(f"**使用工具：** {', '.join(turn['tools_used'])}")
                
                lines.append("")
                lines.append("---")
                lines.append("")
            
            return '\n'.join(lines)
        
        return ""


def main():
    """测试函数"""
    import sys
    
    cm = ConversationManager()
    
    print("=" * 60)
    print("对话历史管理器测试")
    print("=" * 60)
    
    session_id = cm.start_session()
    
    cm.add_turn(
        user_msg="如何使用 Python 读取 JSON 文件？",
        ai_response="可以使用 json.load() 方法读取 JSON 文件...",
        tools_used=['Read', 'Write']
    )
    
    cm.add_turn(
        user_msg="遇到编码错误怎么办？",
        ai_response="可以指定 encoding 参数，例如 encoding='utf-8'...",
        tools_used=['Read']
    )
    
    cm.add_turn(
        user_msg="谢谢，问题解决了",
        ai_response="不客气！如果还有其他问题，随时问我。"
    )
    
    print("\n📋 当前会话信息：")
    info = cm.get_session_info()
    print(f"  会话 ID: {info['id']}")
    print(f"  开始时间: {info['started_at']}")
    print(f"  总轮数: {info['total_turns']}")
    
    print("\n📝 对话上下文：")
    context = cm.get_context()
    for turn in context:
        print(f"\n  第 {turn['turn_number']} 轮:")
        print(f"    用户: {turn['user_message'][:50]}...")
        print(f"    AI: {turn['ai_response'][:50]}...")
    
    print("\n📄 导出为 Markdown：")
    print(cm.export_session(format='markdown')[:500] + "...")
    
    cm.end_session()
    
    print("\n📚 最近会话列表：")
    sessions = cm.list_sessions(limit=5)
    for s in sessions:
        print(f"  #{s['id']} - {s['started_at']} ({s['total_turns']} 轮)")


if __name__ == '__main__':
    main()
