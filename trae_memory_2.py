#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae Memory 2.0 - 集成模块
融合 EvoMap 理念的完整实现
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional

# 导入 Trae Memory 2.0 组件
from gdi_scorer import GDIScorer
from validation_pipeline import ValidationPipeline
from knowledge_graph import KnowledgeGraph
from evolution_engine import EvolutionEngine, EvolutionEvent


class TraeMemory2:
    """
    Trae Memory 2.0 集成类
    
    在原有 Trae Memory 基础上，增加：
    - GDI 评分系统
    - 多维度验证管道
    - 知识图谱管理
    - 进化引擎
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化 Trae Memory 2.0
        
        Args:
            db_path: 数据库路径
        """
        if db_path is None:
            home_dir = str(Path.home())
            db_path = str(Path(home_dir) / ".trae" / "memory" / "trae_memory.db")
        
        self.db_path = db_path
        
        # 初始化组件
        self.gdi_scorer = GDIScorer()
        self.validation_pipeline = ValidationPipeline()
        self.knowledge_graph = KnowledgeGraph(db_path)
        self.evolution_events = EvolutionEvent(db_path)
        
        # 进化引擎（需要 store 实例）
        self.evolution_engine = None
    
    def set_store(self, store):
        """
        设置 MemoryStore 实例
        
        Args:
            store: MemoryStore 实例
        """
        from memory_store import MemoryStore
        self.store = store
        self.gdi_scorer = GDIScorer(store)
        self.validation_pipeline = ValidationPipeline(store)
        self.evolution_engine = EvolutionEngine(
            store,
            self.gdi_scorer,
            self.validation_pipeline,
            self.knowledge_graph
        )
    
    def add_memory(self, category: str, title: str, content: str, 
                   tags: List[str] = None, **kwargs) -> Optional[int]:
        """
        添加记忆（带验证）
        
        Args:
            category: 分类
            title: 标题
            content: 内容
            tags: 标签列表
            **kwargs: 其他参数
            
        Returns:
            记忆 ID，失败返回 None
        """
        memory = {
            'category': category,
            'title': title,
            'content': content,
            'tags': tags or [],
            **kwargs
        }
        
        # 1. 验证
        validation_results = self.validation_pipeline.validate(memory)
        passed = all(r.passed for r in validation_results)
        
        if not passed:
            print("⚠️  记忆未通过验证:")
            for result in validation_results:
                if not result.passed:
                    for issue in result.issues:
                        print(f"   - {issue}")
            return None
        
        # 2. 添加到数据库
        if hasattr(self, 'store') and hasattr(self.store, 'add_memory'):
            memory_id = self.store.add_memory(
                category=category,
                title=title,
                content=content,
                tags=tags,
                **kwargs
            )
        else:
            # 直接数据库操作
            memory_id = self._add_memory_direct(category, title, content, tags, **kwargs)
        
        if memory_id:
            # 3. 计算 GDI 评分
            self._update_gdi_score(memory_id)
            
            # 4. 记录进化事件
            self.evolution_events.record_event(
                memory_id,
                'created',
                {'title': title, 'category': category}
            )
        
        return memory_id
    
    def update_memory(self, memory_id: int, **kwargs) -> bool:
        """
        更新记忆（触发进化检测）
        
        Args:
            memory_id: 记忆 ID
            **kwargs: 更新字段
            
        Returns:
            是否成功更新
        """
        # 获取原记忆
        memory = self._get_memory(memory_id)
        if not memory:
            return False
        
        # 更新内容
        for key, value in kwargs.items():
            memory[key] = value
        
        # 验证
        validation_results = self.validation_pipeline.validate(memory)
        passed = all(r.passed for r in validation_results)
        
        if not passed:
            print("⚠️  更新未通过验证:")
            for result in validation_results:
                if not result.passed:
                    for issue in result.issues:
                        print(f"   - {issue}")
            return False
        
        # 执行更新
        if hasattr(self, 'store') and hasattr(self.store, 'update_memory'):
            success = self.store.update_memory(memory_id, **kwargs)
        else:
            success = self._update_memory_direct(memory_id, **kwargs)
        
        if success:
            # 更新 GDI 评分
            self._update_gdi_score(memory_id)
            
            # 记录进化事件
            self.evolution_events.record_event(
                memory_id,
                'updated',
                kwargs
            )
        
        return success
    
    def get_memory_quality(self, memory_id: int) -> Dict:
        """
        获取记忆质量报告
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            质量报告字典
        """
        memory = self._get_memory(memory_id)
        if not memory:
            return {}
        
        # GDI 评分
        gdi_result = self.gdi_scorer.calculate_gdi(memory)
        
        # 验证结果
        validation_results = self.validation_pipeline.validate(memory)
        
        # 改进建议
        suggestions = self.gdi_scorer.get_quality_suggestions(memory)
        
        # 相关记忆
        related = self.knowledge_graph.find_related(memory_id, depth=1)
        
        return {
            'memory_id': memory_id,
            'title': memory.get('title'),
            'gdi_score': gdi_result['gdi_score'],
            'gdi_details': gdi_result,
            'quality_level': self.gdi_scorer.get_quality_level(gdi_result['gdi_score']),
            'validation_passed': all(r.passed for r in validation_results),
            'validation_issues': [
                issue for r in validation_results 
                for issue in (r.issues or [])
            ],
            'suggestions': suggestions,
            'related_count': len(related)
        }
    
    def derive_memory(self, parent_id: int, title: str, content: str, 
                      tags: List[str] = None) -> Optional[int]:
        """
        从父记忆派生新记忆
        
        Args:
            parent_id: 父记忆 ID
            title: 新标题
            content: 新内容
            tags: 标签列表
            
        Returns:
            新记忆 ID
        """
        new_id = self.knowledge_graph.derive_memory(
            parent_id,
            {
                'title': title,
                'content': content,
                'tags': tags or []
            }
        )
        
        if new_id:
            # 更新 GDI 评分
            self._update_gdi_score(new_id)
            
            # 记录进化事件
            self.evolution_events.record_event(
                new_id,
                'derived',
                {'parent_id': parent_id, 'title': title}
            )
        
        return new_id
    
    def _add_memory_direct(self, category: str, title: str, content: str, 
                          tags: List[str] = None, **kwargs) -> Optional[int]:
        """直接数据库操作添加记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO memories 
                (category, title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (category, title, content, json.dumps(tags or [])))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"添加记忆失败：{e}")
            return None
        finally:
            conn.close()
    
    def _update_memory_direct(self, memory_id: int, **kwargs) -> bool:
        """直接数据库操作更新记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if 'tags' in kwargs and isinstance(kwargs['tags'], list):
                kwargs['tags'] = json.dumps(kwargs['tags'])
            
            set_clause = ', '.join(f"{k} = ?" for k in kwargs.keys())
            values = list(kwargs.values()) + [memory_id]
            
            cursor.execute(f'''
                UPDATE memories 
                SET {set_clause}, updated_at = datetime('now')
                WHERE id = ?
            ''', values)
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"更新记忆失败：{e}")
            return False
        finally:
            conn.close()
    
    def _get_memory(self, memory_id: int) -> Optional[Dict]:
        """获取记忆"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def _update_gdi_score(self, memory_id: int):
        """更新 GDI 评分"""
        memory = self._get_memory(memory_id)
        if not memory:
            return
        
        gdi_result = self.gdi_scorer.calculate_gdi(memory)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE memories 
                SET gdi_score = ?,
                    gdi_intrinsic = ?,
                    gdi_usage = ?,
                    gdi_social = ?,
                    gdi_freshness = ?
                WHERE id = ?
            ''', (
                gdi_result['gdi_score'],
                gdi_result['gdi_intrinsic'],
                gdi_result['gdi_usage'],
                gdi_result['gdi_social'],
                gdi_result['gdi_freshness'],
                memory_id
            ))
            conn.commit()
        except Exception as e:
            print(f"更新 GDI 评分失败：{e}")
        finally:
            conn.close()


# 便捷函数
def create_memory_2(db_path: str = None) -> TraeMemory2:
    """创建 Trae Memory 2.0 实例"""
    return TraeMemory2(db_path)
