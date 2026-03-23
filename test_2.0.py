#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae Memory 2.0 测试脚本
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from trae_memory_2 import TraeMemory2


def test_gdi_scorer():
    """测试 GDI 评分器"""
    print("\n" + "="*60)
    print("测试 GDI 评分器")
    print("="*60)
    
    tm = TraeMemory2()
    
    # 创建测试记忆
    memory = {
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

这个函数遵循了所有最佳实践。
        ''',
        'tags': ['python', '函数', '最佳实践'],
        'access_count': 5,
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-15T00:00:00'
    }
    
    gdi_result = tm.gdi_scorer.calculate_gdi(memory)
    
    print(f"\n测试记忆：{memory['title']}")
    print(f"综合评分：{gdi_result['gdi_score']:.3f}")
    print(f"质量等级：{tm.gdi_scorer.get_quality_level(gdi_result['gdi_score'])}")
    print(f"\n维度评分:")
    print(f"  - 内在质量：{gdi_result['gdi_intrinsic']:.3f}")
    print(f"  - 使用指标：{gdi_result['gdi_usage']:.3f}")
    print(f"  - 社交信号：{gdi_result['gdi_social']:.3f}")
    print(f"  - 新鲜度：  {gdi_result['gdi_freshness']:.3f}")
    
    suggestions = tm.gdi_scorer.get_quality_suggestions(memory)
    if suggestions:
        print(f"\n改进建议:")
        for s in suggestions:
            print(f"  - {s}")
    else:
        print("\n✅ 无明显改进建议")


def test_validation_pipeline():
    """测试验证管道"""
    print("\n" + "="*60)
    print("测试验证管道")
    print("="*60)
    
    tm = TraeMemory2()
    
    # 测试记忆 1：高质量
    memory_good = {
        'title': 'Python 装饰器使用指南',
        'content': '''
装饰器是 Python 的强大特性。

## 基本语法

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function")
        result = func(*args, **kwargs)
        print("After function")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")
```

装饰器可以用于日志、性能测试等场景。
        ''',
        'tags': ['python', '装饰器', '高级特性']
    }
    
    # 测试记忆 2：低质量
    memory_bad = {
        'title': '测试',
        'content': '内容太短',
        'tags': []
    }
    
    print("\n测试记忆 1（高质量）:")
    results = tm.validation_pipeline.validate(memory_good)
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.validator_name}: {'通过' if result.passed else '未通过'}")
        if result.issues:
            for issue in result.issues:
                print(f"     - {issue}")
    
    print("\n测试记忆 2（低质量）:")
    results = tm.validation_pipeline.validate(memory_bad)
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.validator_name}: {'通过' if result.passed else '未通过'}")
        if result.issues:
            for issue in result.issues:
                print(f"     - {issue}")


def test_knowledge_graph():
    """测试知识图谱"""
    print("\n" + "="*60)
    print("测试知识图谱")
    print("="*60)
    
    tm = TraeMemory2()
    
    # 添加测试记忆
    print("\n添加测试记忆...")
    
    # 父记忆
    parent_id = tm.add_memory(
        category='knowledge',
        title='Python 基础：列表推导式',
        content='列表推导式是 Python 的简洁语法。',
        tags=['python', '基础']
    )
    
    if parent_id:
        print(f"✅ 创建父记忆 #{parent_id}")
        
        # 派生子记忆
        child_id = tm.derive_memory(
            parent_id,
            'Python 进阶：字典推导式',
            '字典推导式类似于列表推导式，但用于创建字典。',
            tags=['python', '进阶']
        )
        
        if child_id:
            print(f"✅ 派生子记忆 #{child_id}")
            
            # 显示继承链
            print("\n继承链:")
            chain = tm.knowledge_graph.get_inheritance_chain(child_id)
            for mem in chain:
                print(f"  - #{mem['id']}: {mem['title']}")
            
            # 显示关系
            print("\n关系网络:")
            related = tm.knowledge_graph.find_related(parent_id)
            for mem in related:
                print(f"  - #{mem['id']}: {mem['title']} ({mem.get('relation_type', 'unknown')})")
    else:
        print("⚠️  创建记忆失败（可能已存在）")


def test_evolution_engine():
    """测试进化引擎"""
    print("\n" + "="*60)
    print("测试进化引擎")
    print("="*60)
    
    tm = TraeMemory2()
    
    # 获取一个记忆
    memory = tm._get_memory(1)
    
    if memory:
        print(f"\n测试记忆：{memory['title']}")
        
        # 检测进化机会
        if tm.evolution_engine:
            mutation_type = tm.evolution_engine.detect_mutation_opportunity(
                memory,
                {'feedback': 'negative'}
            )
            
            if mutation_type:
                print(f"检测到进化机会：{mutation_type.value}")
                
                # 生成变异
                mutant = tm.evolution_engine.generate_mutation(memory, mutation_type)
                print(f"生成变异版本")
            else:
                print("未检测到进化机会")
        else:
            print("⚠️  未设置 store 实例，跳过进化引擎测试")
    else:
        print("⚠️  未找到测试记忆")


def test_quality_report():
    """测试质量报告"""
    print("\n" + "="*60)
    print("测试质量报告")
    print("="*60)
    
    tm = TraeMemory2()
    
    # 获取记忆
    memory = tm._get_memory(1)
    
    if memory:
        report = tm.get_memory_quality(memory['id'])
        
        print(f"\n记忆：{report.get('title')}")
        print(f"GDI 评分：{report.get('gdi_score', 0):.3f} ({report.get('quality_level', 'N/A')})")
        print(f"验证状态：{'✅ 通过' if report.get('validation_passed') else '❌ 未通过'}")
        
        if report.get('validation_issues'):
            print("\n验证问题:")
            for issue in report['validation_issues']:
                print(f"  - {issue}")
        
        if report.get('suggestions'):
            print("\n改进建议:")
            for s in report['suggestions']:
                print(f"  - {s}")
        
        print(f"\n相关记忆数：{report.get('related_count', 0)}")
    else:
        print("⚠️  未找到测试记忆")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Trae Memory 2.0 测试套件")
    print("="*60)
    
    test_gdi_scorer()
    test_validation_pipeline()
    test_knowledge_graph()
    test_evolution_engine()
    test_quality_report()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
