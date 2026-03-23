#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae Memory 2.0 CLI - 扩展命令行接口
"""

import sys
import json
import argparse
from pathlib import Path

# 导入新模块
from gdi_scorer import GDIScorer
from validation_pipeline import ValidationPipeline
from knowledge_graph import KnowledgeGraph
from evolution_engine import EvolutionEngine, EvolutionEvent


class MemoryCLI:
    """Trae Memory 2.0 CLI"""
    
    def __init__(self, db_path: str):
        """
        初始化 CLI
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        
        # 导入 MemoryStore
        try:
            from memory_store import MemoryStore
            self.store = MemoryStore(db_path)
        except ImportError:
            print("错误：找不到 memory_store 模块")
            sys.exit(1)
        
        # 初始化新组件
        self.gdi_scorer = GDIScorer(self.store)
        self.validation_pipeline = ValidationPipeline(self.store)
        self.knowledge_graph = KnowledgeGraph(db_path)
        self.evolution_engine = EvolutionEngine(
            self.store,
            self.gdi_scorer,
            self.validation_pipeline,
            self.knowledge_graph
        )
        self.evolution_events = EvolutionEvent(db_path)
    
    def cmd_gdi(self, memory_id: int):
        """显示 GDI 评分"""
        memory = self._get_memory(memory_id)
        
        if not memory:
            print(f"❌ 记忆 {memory_id} 不存在")
            return
        
        gdi_result = self.gdi_scorer.calculate_gdi(memory)
        
        print(f"\n📊 记忆 #{memory_id} 的 GDI 评分")
        print("=" * 50)
        print(f"标题：{memory.get('title', 'N/A')}")
        print(f"综合评分：{gdi_result['gdi_score']:.3f} ({self.gdi_scorer.get_quality_level(gdi_result['gdi_score'])})")
        print(f"  - 内在质量：{gdi_result['gdi_intrinsic']:.3f}")
        print(f"  - 使用指标：{gdi_result['gdi_usage']:.3f}")
        print(f"  - 社交信号：{gdi_result['gdi_social']:.3f}")
        print(f"  - 新鲜度：  {gdi_result['gdi_freshness']:.3f}")
        
        # 显示改进建议
        suggestions = self.gdi_scorer.get_quality_suggestions(memory)
        if suggestions:
            print(f"\n💡 改进建议:")
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")
    
    def cmd_validate(self, memory_id: int):
        """验证记忆质量"""
        memory = self._get_memory(memory_id)
        
        if not memory:
            print(f"❌ 记忆 {memory_id} 不存在")
            return
        
        results = self.validation_pipeline.validate(memory)
        
        print(f"\n✅ 记忆 #{memory_id} 的验证结果")
        print("=" * 50)
        print(f"标题：{memory.get('title', 'N/A')}")
        
        all_passed = True
        for result in results:
            status = "✅" if result.passed else "❌"
            print(f"\n{status} {result.validator_name}: {'通过' if result.passed else '未通过'}")
            
            if result.issues:
                print(f"   问题:")
                for issue in result.issues:
                    print(f"   - {issue}")
            
            if not result.passed:
                all_passed = False
        
        print(f"\n{'=' * 50}")
        print(f"总体结果：{'✅ 通过' if all_passed else '❌ 未通过'}")
    
    def cmd_relations(self, memory_id: int, depth: int = 2):
        """显示记忆关系"""
        related = self.knowledge_graph.find_related(memory_id, depth)
        
        print(f"\n🔗 记忆 #{memory_id} 的关联记忆")
        print("=" * 50)
        
        if not related:
            print("暂无关联记忆")
            return
        
        for mem in related:
            print(f"\n- #{mem['id']}: {mem.get('title', 'N/A')}")
            print(f"  类型：{mem.get('relation_type', 'unknown')}")
            print(f"  距离：{mem.get('level', 1)}")
            print(f"  GDI: {mem.get('gdi_score', 0):.3f}")
    
    def cmd_inherit(self, memory_id: int):
        """显示继承链"""
        chain = self.knowledge_graph.get_inheritance_chain(memory_id)
        
        print(f"\n🌳 记忆 #{memory_id} 的继承链")
        print("=" * 50)
        
        if not chain:
            print("暂无继承链")
            return
        
        for i, mem in enumerate(chain):
            indent = "  " * i
            gen = mem.get('generation', 1)
            print(f"{indent}└─ #{mem['id']} (第{gen}代): {mem.get('title', 'N/A')}")
            print(f"{indent}   GDI: {mem.get('gdi_score', 0):.3f}")
    
    def cmd_derive(self, parent_id: int, title: str, content: str):
        """从父记忆派生新记忆"""
        modifications = {
            'title': title,
            'content': content
        }
        
        new_id = self.knowledge_graph.derive_memory(parent_id, modifications)
        
        if new_id:
            print(f"✅ 成功派生新记忆 #{new_id}")
            print(f"   父记忆：#{parent_id}")
            print(f"   标题：{title}")
        else:
            print(f"❌ 派生失败")
    
    def cmd_evolve(self, memory_id: int):
        """触发记忆进化"""
        context = {
            'feedback': 'positive',
            'is_new_scenario': False
        }
        
        new_id = self.evolution_engine.trigger_evolution(memory_id, context)
        
        if new_id:
            print(f"✅ 成功触发进化")
            print(f"   原始记忆：#{memory_id}")
            print(f"   新记忆：#{new_id}")
        else:
            print(f"ℹ️  未检测到进化机会")
    
    def cmd_history(self, memory_id: int):
        """显示进化历史"""
        events = self.evolution_events.get_events(memory_id)
        
        print(f"\n📜 记忆 #{memory_id} 的进化历史")
        print("=" * 50)
        
        if not events:
            print("暂无进化记录")
            return
        
        for event in events:
            print(f"\n- {event.get('created_at', 'N/A')}")
            print(f"  类型：{event.get('event_type', 'unknown')}")
            print(f"  数据：{event.get('event_data', '{}')}")
    
    def cmd_stats(self):
        """显示图谱统计"""
        stats = self.knowledge_graph.get_statistics()
        
        print(f"\n📊 知识图谱统计")
        print("=" * 50)
        print(f"总关系数：{stats.get('total_relations', 0)}")
        print(f"关联记忆数：{stats.get('connected_memories', 0)}")
        
        by_type = stats.get('by_type', {})
        if by_type:
            print(f"\n按类型统计:")
            for rel_type, count in by_type.items():
                print(f"  - {rel_type}: {count}")
    
    def _get_memory(self, memory_id: int) -> dict:
        """获取记忆"""
        import sqlite3
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Trae Memory 2.0 CLI')
    parser.add_argument('--db', default=None, help='数据库路径')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # GDI 命令
    gdi_parser = subparsers.add_parser('gdi', help='显示 GDI 评分')
    gdi_parser.add_argument('memory_id', type=int, help='记忆 ID')
    
    # 验证命令
    validate_parser = subparsers.add_parser('validate', help='验证记忆质量')
    validate_parser.add_argument('memory_id', type=int, help='记忆 ID')
    
    # 关系命令
    relations_parser = subparsers.add_parser('relations', help='显示关联记忆')
    relations_parser.add_argument('memory_id', type=int, help='记忆 ID')
    relations_parser.add_argument('--depth', type=int, default=2, help='搜索深度')
    
    # 继承链命令
    inherit_parser = subparsers.add_parser('inherit', help='显示继承链')
    inherit_parser.add_argument('memory_id', type=int, help='记忆 ID')
    
    # 派生命令
    derive_parser = subparsers.add_parser('derive', help='派生新记忆')
    derive_parser.add_argument('parent_id', type=int, help='父记忆 ID')
    derive_parser.add_argument('title', type=str, help='新记忆标题')
    derive_parser.add_argument('content', type=str, help='新记忆内容')
    
    # 进化命令
    evolve_parser = subparsers.add_parser('evolve', help='触发进化')
    evolve_parser.add_argument('memory_id', type=int, help='记忆 ID')
    
    # 历史命令
    history_parser = subparsers.add_parser('history', help='显示进化历史')
    history_parser.add_argument('memory_id', type=int, help='记忆 ID')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示图谱统计')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 获取数据库路径
    db_path = args.db
    if not db_path:
        home_dir = str(Path.home())
        db_path = str(Path(home_dir) / ".trae" / "memory" / "trae_memory.db")
    
    # 创建 CLI 实例
    cli = MemoryCLI(db_path)
    
    # 执行命令
    if args.command == 'gdi':
        cli.cmd_gdi(args.memory_id)
    elif args.command == 'validate':
        cli.cmd_validate(args.memory_id)
    elif args.command == 'relations':
        cli.cmd_relations(args.memory_id, args.depth)
    elif args.command == 'inherit':
        cli.cmd_inherit(args.memory_id)
    elif args.command == 'derive':
        cli.cmd_derive(args.parent_id, args.title, args.content)
    elif args.command == 'evolve':
        cli.cmd_evolve(args.memory_id)
    elif args.command == 'history':
        cli.cmd_history(args.memory_id)
    elif args.command == 'stats':
        cli.cmd_stats()


if __name__ == '__main__':
    main()
