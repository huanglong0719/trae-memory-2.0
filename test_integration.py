#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae Memory 2.0 集成测试
验证所有模块协同工作
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from project_memory import ProjectMemoryManager
from project_registry import ProjectRegistry, MultiProjectMemoryManager
from confidence_evaluator import ConfidenceEvaluator
from conversation_manager import ConversationManager
from auto_extractor import AutoMemoryExtractor
from integrated_memory_manager import IntegratedMemoryManager
from smart_retriever import SmartMemoryRetriever


def test_project_memory():
    """测试项目级记忆"""
    print("\n" + "=" * 60)
    print("测试 1: 项目级记忆管理器")
    print("=" * 60)
    
    pm = ProjectMemoryManager()
    
    memory = pm.extract_from_project()
    print(f"✅ 提取项目信息: {memory.get('project_name', 'N/A')}")
    
    pm.save_project_memory(memory)
    print(f"✅ 保存项目记忆")
    
    loaded = pm.load_project_memory()
    print(f"✅ 加载项目记忆: {loaded.get('project_name', 'N/A')}")
    
    return True


def test_project_registry():
    """测试项目注册表"""
    print("\n" + "=" * 60)
    print("测试 2: 项目注册表（多项目支持）")
    print("=" * 60)
    
    registry = ProjectRegistry()
    
    projects = registry.list_projects()
    print(f"✅ 已注册项目数: {len(projects)}")
    
    if projects:
        current = registry.get_current_project()
        if current:
            print(f"✅ 当前项目: {current['name']}")
        
        stats = registry.get_stats()
        print(f"✅ 统计信息: {stats['total_projects']} 项目, {stats['total_accesses']} 次访问")
    
    return True


def test_integrated_manager():
    """测试集成记忆管理器"""
    print("\n" + "=" * 60)
    print("测试 3: 集成记忆管理器")
    print("=" * 60)
    
    imm = IntegratedMemoryManager(auto_detect=False)
    
    projects = imm.list_projects()
    print(f"✅ 已注册项目数: {len(projects)}")
    
    if projects:
        project_id = projects[0]['id']
        imm.switch_project(project_id)
        print(f"✅ 切换到项目: {projects[0]['name']}")
    
    return True


def test_confidence_evaluator():
    """测试置信度评估器"""
    print("\n" + "=" * 60)
    print("测试 4: 置信度评估器")
    print("=" * 60)
    
    evaluator = ConfidenceEvaluator()
    
    test_memory = {
        'id': 999,
        'title': '测试记忆',
        'content': '这是一个测试记忆，用于验证置信度评估功能。' * 5,
        'tags': ['test'],
        'source': 'user_explicit',
        'created_at': '2026-04-02T00:00:00',
        'verified': True
    }
    
    report = evaluator.get_quality_report(test_memory)
    print(f"✅ 置信度: {report['confidence']:.3f}")
    print(f"✅ 质量等级: {report['quality_level']}")
    
    return True


def test_conversation_manager():
    """测试对话历史管理器"""
    print("\n" + "=" * 60)
    print("测试 5: 对话历史管理器")
    print("=" * 60)
    
    cm = ConversationManager()
    
    session_id = cm.start_session()
    print(f"✅ 开始会话: #{session_id}")
    
    cm.add_turn(
        user_msg="测试用户消息",
        ai_response="测试 AI 响应",
        tools_used=['test_tool']
    )
    print(f"✅ 添加对话轮次")
    
    context = cm.get_context()
    print(f"✅ 获取上下文: {len(context)} 轮")
    
    cm.end_session()
    print(f"✅ 结束会话")
    
    return True


def test_auto_extractor():
    """测试自动记忆提取器"""
    print("\n" + "=" * 60)
    print("测试 6: 自动记忆提取器")
    print("=" * 60)
    
    extractor = AutoMemoryExtractor()
    
    test_conversation = [
        {
            'turn_number': 1,
            'user_message': '错误：无法连接数据库',
            'ai_response': '解决：检查数据库连接配置，确保连接字符串正确',
            'session_id': 1
        },
        {
            'turn_number': 2,
            'user_message': '我喜欢使用 Python 进行数据分析',
            'ai_response': '好的，我会记住你的偏好',
            'session_id': 1
        }
    ]
    
    memories = extractor.extract_from_conversation(test_conversation)
    print(f"✅ 提取记忆: {len(memories)} 条")
    
    for mem in memories:
        print(f"   - {mem['category']}: {mem['title'][:30]}...")
    
    return True


def test_smart_retriever():
    """测试智能记忆检索器"""
    print("\n" + "=" * 60)
    print("测试 7: 智能记忆检索器")
    print("=" * 60)
    
    imm = IntegratedMemoryManager(auto_detect=False)
    retriever = SmartMemoryRetriever(imm)
    
    stats = retriever.get_search_stats()
    print(f"✅ 检索统计: {stats['total_projects']} 项目")
    
    result = retriever.search("Python", scope='auto', limit=5)
    print(f"✅ 自动检索: 项目 {len(result['project_results'])} 条, 全局 {len(result['global_results'])} 条")
    
    result = retriever.search("记忆", scope='project', limit=5)
    print(f"✅ 项目检索: {result['total']} 条结果")
    
    result = retriever.search("记忆", scope='global', limit=5)
    print(f"✅ 全局检索: {result['total']} 条结果")
    
    return True


def test_integration():
    """测试集成场景"""
    print("\n" + "=" * 60)
    print("测试 8: 集成场景测试")
    print("=" * 60)
    
    pm = ProjectMemoryManager()
    cm = ConversationManager()
    extractor = AutoMemoryExtractor()
    evaluator = ConfidenceEvaluator()
    
    session_id = cm.start_session()
    
    conversation = [
        {
            'turn_number': 1,
            'user_message': '项目规范：所有代码必须通过单元测试',
            'ai_response': '已记录项目规范。单元测试是保证代码质量的重要手段。',
            'session_id': session_id
        }
    ]
    
    memories = extractor.extract_from_conversation(conversation)
    print(f"✅ 从对话提取 {len(memories)} 条记忆")
    
    if memories:
        report = evaluator.get_quality_report(memories[0])
        print(f"✅ 记忆置信度: {report['confidence']:.3f}")
    
    project_memory = pm.load_project_memory()
    if memories:
        project_memory['decisions'].append(memories[0]['content'][:50])
        pm.save_project_memory(project_memory)
        print(f"✅ 同步到项目记忆")
    
    cm.end_session()
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Trae Memory 2.0 集成测试")
    print("=" * 60)
    
    tests = [
        ("项目级记忆", test_project_memory),
        ("项目注册表", test_project_registry),
        ("集成记忆管理器", test_integrated_manager),
        ("置信度评估", test_confidence_evaluator),
        ("对话历史管理", test_conversation_manager),
        ("自动记忆提取", test_auto_extractor),
        ("智能记忆检索", test_smart_retriever),
        ("集成场景", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, success, error in results:
        if success:
            print(f"✅ {name}: 通过")
            passed += 1
        else:
            print(f"❌ {name}: 失败 - {error}")
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
