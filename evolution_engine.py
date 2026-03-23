#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进化引擎 - 记忆自我进化机制
"""

from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime


class MutationType(Enum):
    """突变类型"""
    REPAIR = "repair"      # 修复
    OPTIMIZE = "optimize"  # 优化
    INNOVATE = "innovate"  # 创新


class EvolutionEngine:
    """进化引擎"""
    
    def __init__(self, store, gdi_scorer, validation_pipeline, knowledge_graph):
        """
        初始化进化引擎
        
        Args:
            store: MemoryStore 实例
            gdi_scorer: GDIScorer 实例
            validation_pipeline: ValidationPipeline 实例
            knowledge_graph: KnowledgeGraph 实例
        """
        self.store = store
        self.gdi_scorer = gdi_scorer
        self.validation_pipeline = validation_pipeline
        self.knowledge_graph = knowledge_graph
    
    def detect_mutation_opportunity(self, memory: Dict, context: Dict = None) -> Optional[MutationType]:
        """
        检测突变机会
        
        Args:
            memory: 记忆字典
            context: 上下文信息
            
        Returns:
            突变类型，无机会返回 None
        """
        context = context or {}
        
        # 1. 基于用户反馈检测
        feedback = context.get('feedback')
        if feedback == 'negative' or feedback == 'downvote':
            return MutationType.REPAIR
        
        # 2. 基于 GDI 评分检测
        gdi_result = self.gdi_scorer.calculate_gdi(memory)
        gdi_score = gdi_result.get('gdi_score', 0.5)
        
        if gdi_score < 0.4:
            return MutationType.OPTIMIZE
        
        # 3. 基于验证问题检测
        validation_results = self.validation_pipeline.validate(memory)
        failed_validations = [r for r in validation_results if not r.passed]
        
        if failed_validations:
            return MutationType.REPAIR
        
        # 4. 基于新场景检测
        if context.get('is_new_scenario', False):
            return MutationType.INNOVATE
        
        # 5. 基于查询复杂度检测
        if context.get('query_complexity', 0) > 0.8:
            return MutationType.OPTIMIZE
        
        return None
    
    def generate_mutation(self, memory: Dict, mutation_type: MutationType) -> Dict:
        """
        生成变异版本
        
        Args:
            memory: 原始记忆
            mutation_type: 突变类型
            
        Returns:
            变异后的记忆字典
        """
        if mutation_type == MutationType.REPAIR:
            return self._repair_mutation(memory)
        elif mutation_type == MutationType.OPTIMIZE:
            return self._optimize_mutation(memory)
        elif mutation_type == MutationType.INNOVATE:
            return self._innovate_mutation(memory)
        
        return memory.copy()
    
    def _repair_mutation(self, memory: Dict) -> Dict:
        """修复型突变"""
        mutated = memory.copy()
        
        # 获取验证问题
        validation_results = self.validation_pipeline.validate(memory)
        issues = []
        for result in validation_results:
            issues.extend(result.issues)
        
        # 添加修复说明
        if issues:
            mutated['content'] = memory.get('content', '') + '\n\n---\n**修复说明**: ' + '; '.join(issues)
        
        return mutated
    
    def _optimize_mutation(self, memory: Dict) -> Dict:
        """优化型突变"""
        mutated = memory.copy()
        
        # 获取质量改进建议
        suggestions = self.gdi_scorer.get_quality_suggestions(memory)
        
        # 添加优化说明
        if suggestions:
            mutated['content'] = memory.get('content', '') + '\n\n---\n**优化建议**: \n' + '\n'.join(
                f"- {s}" for s in suggestions
            )
        
        return mutated
    
    def _innovate_mutation(self, memory: Dict) -> Dict:
        """创新型突变"""
        mutated = memory.copy()
        
        # 添加创新标记
        mutated['content'] = memory.get('content', '') + '\n\n---\n**创新扩展**: 此记忆已扩展到新的应用场景'
        
        return mutated
    
    def select_and_inherit(self, original: Dict, mutant: Dict) -> Dict:
        """
        选择与继承
        
        Args:
            original: 原始记忆
            mutant: 变异版本
            
        Returns:
            被选择的记忆
        """
        # 验证变异版本
        validation_result = self.validation_pipeline.validate(mutant)
        passed = all(r.passed for r in validation_result)
        
        if not passed:
            return original
        
        # 计算 GDI 评分
        original_gdi = self.gdi_scorer.calculate_gdi(original)
        mutant_gdi = self.gdi_scorer.calculate_gdi(mutant)
        
        # 如果变异版本更优，创建继承关系
        if mutant_gdi['gdi_score'] > original_gdi['gdi_score']:
            # 在数据库中创建新记忆
            if hasattr(self.store, 'derive_memory'):
                new_id = self.store.derive_memory(
                    original['id'],
                    {
                        'title': mutant.get('title', original['title']),
                        'content': mutant.get('content', original['content']),
                    }
                )
                
                if new_id:
                    mutant['id'] = new_id
                    mutant['generation'] = original.get('generation', 1) + 1
                    return mutant
        
        return original
    
    def trigger_evolution(self, memory_id: int, context: Dict = None) -> Optional[int]:
        """
        触发进化流程
        
        Args:
            memory_id: 记忆 ID
            context: 上下文信息
            
        Returns:
            新记忆 ID（如果有进化）
        """
        # 获取原始记忆
        if hasattr(self.store, 'get_memory'):
            memory = self.store.get_memory(memory_id)
        else:
            # 简单实现：从数据库读取
            import sqlite3
            conn = sqlite3.connect(self.store.db_path if hasattr(self.store, 'db_path') else self.store)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            memory = dict(row)
        
        # 检测突变机会
        mutation_type = self.detect_mutation_opportunity(memory, context)
        
        if not mutation_type:
            return None
        
        # 生成变异
        mutant = self.generate_mutation(memory, mutation_type)
        
        # 选择与继承
        selected = self.select_and_inherit(memory, mutant)
        
        if selected['id'] != memory_id:
            return selected['id']
        
        return None


class EvolutionEvent:
    """进化事件记录"""
    
    def __init__(self, db_path: str):
        """
        初始化进化事件记录器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_table()
    
    def _init_table(self):
        """初始化事件表"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evolution_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_event(self, memory_id: int, event_type: str, event_data: Dict) -> bool:
        """
        记录进化事件
        
        Args:
            memory_id: 记忆 ID
            event_type: 事件类型
            event_data: 事件数据
            
        Returns:
            是否成功记录
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            import json
            cursor.execute('''
                INSERT INTO evolution_events 
                (memory_id, event_type, event_data)
                VALUES (?, ?, ?)
            ''', (memory_id, event_type, json.dumps(event_data, ensure_ascii=False)))
            conn.commit()
            return True
        except Exception as e:
            print(f"记录进化事件失败：{e}")
            return False
        finally:
            conn.close()
    
    def get_events(self, memory_id: int, limit: int = 10) -> List[Dict]:
        """
        获取记忆的进化历史
        
        Args:
            memory_id: 记忆 ID
            limit: 返回数量
            
        Returns:
            事件列表
        """
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM evolution_events
                WHERE memory_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (memory_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取进化事件失败：{e}")
            return []
        finally:
            conn.close()
