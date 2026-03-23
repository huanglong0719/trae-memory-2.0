#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱管理器 - 记忆关系管理与继承链
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional


class KnowledgeGraph:
    """知识图谱管理器"""
    
    # 关系类型定义
    RELATION_DERIVES_FROM = "derives_from"  # 派生自
    RELATION_REFERENCES = "references"      # 引用
    RELATION_CONTRADICTS = "contradicts"    # 矛盾
    RELATION_EXTENDS = "extends"            # 扩展
    RELATION_REPLACES = "replaces"          # 替代
    RELATION_RELATED_TO = "related_to"      # 相关
    
    def __init__(self, db_path: str):
        """
        初始化知识图谱
        
        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        self._init_graph_tables()
    
    def _init_graph_tables(self):
        """初始化图谱表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 关系表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES memories(id),
                FOREIGN KEY (target_id) REFERENCES memories(id),
                UNIQUE(source_id, target_id, relation_type)
            )
        ''')
        
        # 关系类型索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_relations 
            ON memory_relations(source_id, target_id, relation_type)
        ''')
        
        # 添加 memories 表的新列（如果不存在）
        self._add_columns_if_needed(cursor)
        
        conn.commit()
        conn.close()
    
    def _add_columns_if_needed(self, cursor):
        """添加新列到 memories 表"""
        cursor.execute("PRAGMA table_info(memories)")
        columns = {row[1] for row in cursor.fetchall()}
        
        new_columns = {
            'gdi_score': 'REAL DEFAULT 0.5',
            'gdi_intrinsic': 'REAL DEFAULT 0.5',
            'gdi_usage': 'REAL DEFAULT 0.5',
            'gdi_social': 'REAL DEFAULT 0.5',
            'gdi_freshness': 'REAL DEFAULT 0.5',
            'parent_id': 'INTEGER REFERENCES memories(id)',
            'generation': 'INTEGER DEFAULT 1',
            'validation_status': 'TEXT DEFAULT \'pending\''
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE memories ADD COLUMN {col_name} {col_type}')
                except Exception as e:
                    pass  # 列已存在或其他错误
    
    def add_relation(self, source_id: int, target_id: int, relation_type: str) -> bool:
        """
        添加记忆关系
        
        Args:
            source_id: 源记忆 ID
            target_id: 目标记忆 ID
            relation_type: 关系类型
            
        Returns:
            是否成功添加
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO memory_relations 
                (source_id, target_id, relation_type)
                VALUES (?, ?, ?)
            ''', (source_id, target_id, relation_type))
            conn.commit()
            return True
        except Exception as e:
            print(f"添加关系失败：{e}")
            return False
        finally:
            conn.close()
    
    def find_related(self, memory_id: int, depth: int = 2) -> List[Dict]:
        """
        查找相关记忆（支持多跳）
        
        Args:
            memory_id: 起始记忆 ID
            depth: 搜索深度
            
        Returns:
            相关记忆列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # 递归查询
            cursor.execute('''
                WITH RECURSIVE related AS (
                    SELECT source_id, target_id, relation_type, 1 as level
                    FROM memory_relations
                    WHERE source_id = ? OR target_id = ?
                    
                    UNION
                    
                    SELECT mr.source_id, mr.target_id, mr.relation_type, r.level + 1
                    FROM memory_relations mr
                    JOIN related r ON (
                        mr.source_id = r.target_id OR mr.target_id = r.source_id
                    )
                    WHERE r.level < ?
                )
                SELECT DISTINCT m.*, r.relation_type, r.level
                FROM related r
                JOIN memories m ON (
                    m.id = r.source_id OR m.id = r.target_id
                )
                WHERE m.id != ?
                ORDER BY r.level, m.gdi_score DESC
            ''', (memory_id, memory_id, depth, memory_id))
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(f"查找相关记忆失败：{e}")
            return []
        finally:
            conn.close()
    
    def get_inheritance_chain(self, memory_id: int) -> List[Dict]:
        """
        获取知识继承链
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            继承链列表（从祖先到后代）
        """
        chain = []
        current_id = memory_id
        visited = set()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            while current_id and current_id not in visited:
                visited.add(current_id)
                
                cursor.execute('''
                    SELECT m.*, r.relation_type
                    FROM memories m
                    LEFT JOIN memory_relations r ON m.id = r.source_id 
                        AND r.target_id = ? AND r.relation_type = 'derives_from'
                    WHERE m.id = ?
                ''', (current_id, current_id))
                
                row = cursor.fetchone()
                if row:
                    row_dict = dict(row)
                    chain.append(row_dict)
                    current_id = row_dict.get('parent_id')
                else:
                    break
            
            return list(reversed(chain))
        except Exception as e:
            print(f"获取继承链失败：{e}")
            return []
        finally:
            conn.close()
    
    def derive_memory(self, parent_id: int, modifications: Dict) -> Optional[int]:
        """
        从父记忆派生新记忆
        
        Args:
            parent_id: 父记忆 ID
            modifications: 修改内容
            
        Returns:
            新记忆 ID，失败返回 None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # 获取父记忆
            cursor.execute('SELECT * FROM memories WHERE id = ?', (parent_id,))
            parent = dict(cursor.fetchone())
            
            if not parent:
                print(f"父记忆不存在：{parent_id}")
                return None
            
            # 合并修改
            new_memory = {**parent, **modifications}
            new_memory['parent_id'] = parent_id
            new_memory['generation'] = parent.get('generation', 1) + 1
            new_memory['created_at'] = datetime.now()
            new_memory['updated_at'] = datetime.now()
            new_memory['access_count'] = 0
            new_memory['decay_score'] = 1.0
            new_memory['tier'] = 'working'
            
            # 插入新记忆
            cursor.execute('''
                INSERT INTO memories 
                (category, title, content, tags, project, priority, importance,
                 parent_id, generation, tier, decay_score, gdi_score,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_memory['category'], new_memory['title'], new_memory['content'],
                json.dumps(new_memory.get('tags', [])), new_memory.get('project'),
                new_memory['priority'], new_memory['importance'],
                parent_id, new_memory['generation'], new_memory['tier'],
                new_memory['decay_score'], 0.5,
                new_memory['created_at'], new_memory['updated_at']
            ))
            
            new_id = cursor.lastrowid
            
            # 添加继承关系
            cursor.execute('''
                INSERT INTO memory_relations 
                (source_id, target_id, relation_type)
                VALUES (?, ?, 'derives_from')
            ''', (new_id, parent_id))
            
            conn.commit()
            return new_id
        except Exception as e:
            print(f"派生记忆失败：{e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_relations(self, memory_id: int, relation_type: str = None) -> List[Dict]:
        """
        获取记忆的所有关系
        
        Args:
            memory_id: 记忆 ID
            relation_type: 关系类型过滤（可选）
            
        Returns:
            关系列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if relation_type:
                cursor.execute('''
                    SELECT mr.*, 
                           m1.title as source_title,
                           m2.title as target_title
                    FROM memory_relations mr
                    JOIN memories m1 ON mr.source_id = m1.id
                    JOIN memories m2 ON mr.target_id = m2.id
                    WHERE (mr.source_id = ? OR mr.target_id = ?)
                      AND mr.relation_type = ?
                ''', (memory_id, memory_id, relation_type))
            else:
                cursor.execute('''
                    SELECT mr.*, 
                           m1.title as source_title,
                           m2.title as target_title
                    FROM memory_relations mr
                    JOIN memories m1 ON mr.source_id = m1.id
                    JOIN memories m2 ON mr.target_id = m2.id
                    WHERE (mr.source_id = ? OR mr.target_id = ?)
                ''', (memory_id, memory_id))
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            print(f"获取关系失败：{e}")
            return []
        finally:
            conn.close()
    
    def remove_relation(self, source_id: int, target_id: int, relation_type: str) -> bool:
        """
        移除记忆关系
        
        Args:
            source_id: 源记忆 ID
            target_id: 目标记忆 ID
            relation_type: 关系类型
            
        Returns:
            是否成功移除
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM memory_relations
                WHERE source_id = ? AND target_id = ? AND relation_type = ?
            ''', (source_id, target_id, relation_type))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"移除关系失败：{e}")
            return False
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 总关系数
            cursor.execute('SELECT COUNT(*) FROM memory_relations')
            total_relations = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute('''
                SELECT relation_type, COUNT(*) as count
                FROM memory_relations
                GROUP BY relation_type
            ''')
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 有关系的记忆数
            cursor.execute('''
                SELECT COUNT(DISTINCT source_id) + COUNT(DISTINCT target_id) 
                - COUNT(DISTINCT CASE WHEN source_id = target_id THEN source_id END)
                FROM memory_relations
            ''')
            connected_memories = cursor.fetchone()[0] or 0
            
            return {
                'total_relations': total_relations,
                'by_type': by_type,
                'connected_memories': connected_memories
            }
        except Exception as e:
            print(f"获取统计失败：{e}")
            return {}
        finally:
            conn.close()
