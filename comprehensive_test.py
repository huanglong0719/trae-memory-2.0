#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae Memory 2.0 全面测试套件
包含功能测试、性能测试、可靠性测试和兼容性测试
"""

import sys
import os
import time
import json
import shutil
import tempfile
import threading
import random
import string
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from project_memory import ProjectMemoryManager
from project_registry import ProjectRegistry
from confidence_evaluator import ConfidenceEvaluator
from conversation_manager import ConversationManager
from auto_extractor import AutoMemoryExtractor
from integrated_memory_manager import IntegratedMemoryManager
from smart_retriever import SmartMemoryRetriever


class TestResult:
    """测试结果记录"""
    
    def __init__(self, category: str, name: str):
        self.category = category
        self.name = name
        self.passed = False
        self.duration = 0.0
        self.message = ""
        self.details = {}
        self.error = None
    
    def to_dict(self) -> Dict:
        return {
            'category': self.category,
            'name': self.name,
            'passed': self.passed,
            'duration': self.duration,
            'message': self.message,
            'details': self.details,
            'error': str(self.error) if self.error else None
        }


class ComprehensiveTestSuite:
    """全面测试套件"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_dir = None
        self.start_time = None
    
    def setup(self):
        """测试环境设置"""
        self.test_dir = Path(tempfile.mkdtemp(prefix='trae_memory_test_'))
        print(f"📁 测试目录: {self.test_dir}")
        
        os.environ['TRAE_MEMORY_HOME'] = str(self.test_dir)
        
        self.start_time = time.time()
    
    def teardown(self):
        """测试环境清理"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)
            print(f"🧹 已清理测试目录")
    
    def record_result(self, result: TestResult):
        """记录测试结果"""
        self.results.append(result)
        
        status = "✅" if result.passed else "❌"
        print(f"{status} [{result.category}] {result.name}: {result.message} ({result.duration:.3f}s)")
    
    # ==================== 功能测试 ====================
    
    def test_functional_data_storage(self):
        """功能测试：数据存储"""
        result = TestResult("功能测试", "数据存储")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'test_project',
                'description': '测试项目描述',
                'tech_stack': ['Python', 'SQLite'],
                'dependencies': ['pytest', 'json'],
                'issues': ['测试问题1'],
                'decisions': ['测试决策1']
            }
            
            pm.save_project_memory(memory)
            
            loaded = pm.load_project_memory()
            
            assert loaded['project_name'] == 'test_project', "项目名称不匹配"
            assert 'Python' in loaded['tech_stack'], "技术栈未保存"
            assert '测试问题1' in loaded['issues'], "问题未保存"
            
            result.passed = True
            result.message = "数据存储和加载成功"
            result.details = {
                'saved_fields': len(memory),
                'loaded_fields': len(loaded)
            }
        
        except Exception as e:
            result.error = e
            result.message = f"数据存储失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_functional_data_retrieval(self):
        """功能测试：数据检索"""
        result = TestResult("功能测试", "数据检索")
        start = time.time()
        
        try:
            imm = IntegratedMemoryManager(auto_detect=False)
            
            test_memory = {
                'id': 9999,
                'title': '测试检索记忆',
                'content': '这是一个用于测试检索功能的记忆条目',
                'tags': ['test', 'retrieval'],
                'source': 'test',
                'created_at': datetime.now().isoformat()
            }
            
            search_result = imm.smart_search("检索", scope='project', limit=5)
            
            assert 'results' in search_result, "检索结果格式错误"
            assert 'total' in search_result, "缺少总数统计"
            
            result.passed = True
            result.message = f"检索成功，返回 {search_result['total']} 条结果"
            result.details = {
                'query': '检索',
                'scope': 'project',
                'total_results': search_result['total']
            }
        
        except Exception as e:
            result.error = e
            result.message = f"数据检索失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_functional_memory_update(self):
        """功能测试：记忆更新"""
        result = TestResult("功能测试", "记忆更新")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'update_test',
                'description': '原始描述',
                'tech_stack': ['Python']
            }
            pm.save_project_memory(memory)
            
            loaded = pm.load_project_memory()
            loaded['description'] = '更新后的描述'
            loaded['tech_stack'].append('JavaScript')
            pm.save_project_memory(loaded)
            
            updated = pm.load_project_memory()
            
            assert updated['description'] == '更新后的描述', "描述未更新"
            assert 'JavaScript' in updated['tech_stack'], "技术栈未更新"
            
            result.passed = True
            result.message = "记忆更新成功"
            result.details = {
                'original_desc': '原始描述',
                'updated_desc': updated['description']
            }
        
        except Exception as e:
            result.error = e
            result.message = f"记忆更新失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_functional_memory_delete(self):
        """功能测试：记忆删除"""
        result = TestResult("功能测试", "记忆删除")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'delete_test',
                'issues': ['问题1', '问题2', '问题3']
            }
            pm.save_project_memory(memory)
            
            loaded = pm.load_project_memory()
            loaded['issues'].remove('问题2')
            pm.save_project_memory(loaded)
            
            updated = pm.load_project_memory()
            
            assert '问题2' not in updated['issues'], "问题未删除"
            assert len(updated['issues']) == 2, "删除数量错误"
            
            result.passed = True
            result.message = "记忆删除成功"
            result.details = {
                'original_count': 3,
                'after_delete': len(updated['issues'])
            }
        
        except Exception as e:
            result.error = e
            result.message = f"记忆删除失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_functional_project_registration(self):
        """功能测试：项目注册"""
        result = TestResult("功能测试", "项目注册")
        start = time.time()
        
        try:
            registry = ProjectRegistry()
            
            test_path = str(self.test_dir / "test_project")
            Path(test_path).mkdir(parents=True, exist_ok=True)
            
            project_id = registry.register_project(
                test_path,
                name="测试项目",
                description="用于测试的项目",
                tags=["test", "demo"]
            )
            
            assert project_id.startswith("proj_"), "项目ID格式错误"
            
            project = registry.get_project(project_id)
            assert project is not None, "项目未找到"
            assert project['name'] == "测试项目", "项目名称不匹配"
            
            result.passed = True
            result.message = f"项目注册成功: {project_id}"
            result.details = {
                'project_id': project_id,
                'project_name': project['name']
            }
        
        except Exception as e:
            result.error = e
            result.message = f"项目注册失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_functional_conversation_tracking(self):
        """功能测试：对话跟踪"""
        result = TestResult("功能测试", "对话跟踪")
        start = time.time()
        
        try:
            cm = ConversationManager()
            
            session_id = cm.start_session()
            
            for i in range(5):
                cm.add_turn(
                    user_msg=f"用户消息 {i+1}",
                    ai_response=f"AI 响应 {i+1}",
                    tools_used=['test_tool']
                )
            
            context = cm.get_context()
            
            assert len(context) == 5, "对话轮次数量错误"
            
            cm.end_session()
            
            sessions = cm.list_sessions(limit=10)
            assert len(sessions) > 0, "会话未保存"
            
            result.passed = True
            result.message = f"对话跟踪成功，{len(context)} 轮对话"
            result.details = {
                'session_id': session_id,
                'turns': len(context)
            }
        
        except Exception as e:
            result.error = e
            result.message = f"对话跟踪失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_functional_auto_extraction(self):
        """功能测试：自动提取"""
        result = TestResult("功能测试", "自动提取")
        start = time.time()
        
        try:
            extractor = AutoMemoryExtractor()
            
            conversation = [
                {
                    'turn_number': 1,
                    'user_message': '错误：无法连接数据库',
                    'ai_response': '解决：检查连接字符串配置',
                    'session_id': 1
                },
                {
                    'turn_number': 2,
                    'user_message': '项目规范：所有函数必须有文档字符串',
                    'ai_response': '已记录规范',
                    'session_id': 1
                },
                {
                    'turn_number': 3,
                    'user_message': '我喜欢使用 Python 进行开发',
                    'ai_response': '已记录偏好',
                    'session_id': 1
                }
            ]
            
            memories = extractor.extract_from_conversation(conversation)
            
            assert len(memories) > 0, "未提取到记忆"
            
            categories = [m['category'] for m in memories]
            assert 'error' in categories or 'rule' in categories or 'preference' in categories, "记忆类别提取错误"
            
            result.passed = True
            result.message = f"自动提取成功，{len(memories)} 条记忆"
            result.details = {
                'memories_count': len(memories),
                'categories': list(set(categories))
            }
        
        except Exception as e:
            result.error = e
            result.message = f"自动提取失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    # ==================== 性能测试 ====================
    
    def test_performance_storage_speed(self):
        """性能测试：存储速度"""
        result = TestResult("性能测试", "存储速度")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            iterations = 100
            times = []
            
            for i in range(iterations):
                memory = {
                    'project_name': f'perf_test_{i}',
                    'description': f'性能测试项目 {i}',
                    'tech_stack': [f'tech_{j}' for j in range(10)],
                    'issues': [f'issue_{j}' for j in range(5)]
                }
                
                t0 = time.time()
                pm.save_project_memory(memory)
                times.append(time.time() - t0)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            result.passed = avg_time < 0.1
            result.message = f"平均存储时间: {avg_time*1000:.2f}ms"
            result.details = {
                'iterations': iterations,
                'avg_time_ms': avg_time * 1000,
                'max_time_ms': max_time * 1000,
                'min_time_ms': min_time * 1000
            }
        
        except Exception as e:
            result.error = e
            result.message = f"存储速度测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_performance_retrieval_speed(self):
        """性能测试：检索速度"""
        result = TestResult("性能测试", "检索速度")
        start = time.time()
        
        try:
            imm = IntegratedMemoryManager(auto_detect=False)
            retriever = SmartMemoryRetriever(imm)
            
            iterations = 50
            times = []
            
            queries = ['Python', '测试', '记忆', '项目', '规范']
            
            for i in range(iterations):
                query = queries[i % len(queries)]
                
                t0 = time.time()
                retriever.search(query, scope='auto', limit=10)
                times.append(time.time() - t0)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            result.passed = avg_time < 0.2
            result.message = f"平均检索时间: {avg_time*1000:.2f}ms"
            result.details = {
                'iterations': iterations,
                'avg_time_ms': avg_time * 1000,
                'max_time_ms': max_time * 1000
            }
        
        except Exception as e:
            result.error = e
            result.message = f"检索速度测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_performance_large_data(self):
        """性能测试：大数据量"""
        result = TestResult("性能测试", "大数据量")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            large_memory = {
                'project_name': 'large_data_test',
                'description': '大数据量测试' * 100,
                'tech_stack': [f'technology_{i}' for i in range(100)],
                'dependencies': [f'dependency_{i}' for i in range(100)],
                'issues': [f'issue_description_{i}' * 10 for i in range(50)],
                'decisions': [f'decision_{i}' * 20 for i in range(50)]
            }
            
            t0 = time.time()
            pm.save_project_memory(large_memory)
            save_time = time.time() - t0
            
            t0 = time.time()
            loaded = pm.load_project_memory()
            load_time = time.time() - t0
            
            assert len(loaded['tech_stack']) == 100, "技术栈数据丢失"
            assert len(loaded['issues']) == 50, "问题数据丢失"
            
            result.passed = save_time < 1.0 and load_time < 0.5
            result.message = f"大数据量处理成功"
            result.details = {
                'save_time_ms': save_time * 1000,
                'load_time_ms': load_time * 1000,
                'data_size': len(json.dumps(large_memory))
            }
        
        except Exception as e:
            result.error = e
            result.message = f"大数据量测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_performance_memory_usage(self):
        """性能测试：内存占用"""
        result = TestResult("性能测试", "内存占用")
        start = time.time()
        
        try:
            import tracemalloc
            tracemalloc.start()
            
            imm = IntegratedMemoryManager(auto_detect=False)
            
            for i in range(10):
                session_id = imm.start_session()
                imm.add_conversation_turn(
                    user_msg=f"测试消息 {i}" * 100,
                    ai_response=f"响应 {i}" * 100
                )
                imm.end_session()
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            peak_mb = peak / 1024 / 1024
            
            result.passed = peak_mb < 100
            result.message = f"峰值内存: {peak_mb:.2f} MB"
            result.details = {
                'current_mb': current / 1024 / 1024,
                'peak_mb': peak_mb
            }
        
        except Exception as e:
            result.error = e
            result.message = f"内存占用测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    # ==================== 可靠性测试 ====================
    
    def test_reliability_error_handling(self):
        """可靠性测试：错误处理"""
        result = TestResult("可靠性测试", "错误处理")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            invalid_memory = {
                'project_name': None,
                'description': 12345,
                'tech_stack': "should be list"
            }
            
            try:
                pm.save_project_memory(invalid_memory)
            except Exception:
                pass
            
            loaded = pm.load_project_memory()
            assert loaded is not None, "错误处理后无法加载"
            
            result.passed = True
            result.message = "错误处理正常"
            result.details = {
                'handled_invalid_type': True
            }
        
        except Exception as e:
            result.error = e
            result.message = f"错误处理测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_reliability_data_integrity(self):
        """可靠性测试：数据完整性"""
        result = TestResult("可靠性测试", "数据完整性")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            original = {
                'project_name': 'integrity_test',
                'description': '数据完整性测试',
                'tech_stack': ['Python', 'SQLite'],
                'special_chars': '特殊字符: 中文、emoji 🎉、符号 <>&"\'',
                'unicode': '日本語 한국어 العربية'
            }
            
            pm.save_project_memory(original)
            loaded = pm.load_project_memory()
            
            assert loaded['project_name'] == original['project_name'], "项目名称损坏"
            assert loaded['special_chars'] == original['special_chars'], "特殊字符损坏"
            assert loaded['unicode'] == original['unicode'], "Unicode字符损坏"
            
            result.passed = True
            result.message = "数据完整性验证通过"
            result.details = {
                'special_chars_preserved': True,
                'unicode_preserved': True
            }
        
        except Exception as e:
            result.error = e
            result.message = f"数据完整性测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_reliability_long_term_storage(self):
        """可靠性测试：长期存储"""
        result = TestResult("可靠性测试", "长期存储")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'long_term_test',
                'created_at': datetime.now().isoformat(),
                'description': '长期存储测试数据'
            }
            
            pm.save_project_memory(memory)
            
            for i in range(20):
                loaded = pm.load_project_memory()
                loaded['access_count'] = loaded.get('access_count', 0) + 1
                pm.save_project_memory(loaded)
            
            final = pm.load_project_memory()
            
            assert final['project_name'] == 'long_term_test', "长期存储后数据损坏"
            assert final.get('access_count', 0) == 20, "更新计数错误"
            
            result.passed = True
            result.message = "长期存储稳定性验证通过"
            result.details = {
                'iterations': 20,
                'final_access_count': final.get('access_count', 0)
            }
        
        except Exception as e:
            result.error = e
            result.message = f"长期存储测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_reliability_recovery(self):
        """可靠性测试：恢复能力"""
        result = TestResult("可靠性测试", "恢复能力")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'recovery_test',
                'description': '恢复能力测试'
            }
            pm.save_project_memory(memory)
            
            memory_file = pm.memory_file
            
            loaded = pm.load_project_memory()
            assert loaded is not None, "初始加载失败"
            
            loaded['description'] = "更新后的描述"
            pm.save_project_memory(loaded)
            
            recovered = pm.load_project_memory()
            assert recovered['description'] == "更新后的描述", "恢复后数据不一致"
            
            result.passed = True
            result.message = "恢复能力验证通过"
            result.details = {
                'recovery_successful': True
            }
        
        except Exception as e:
            result.error = e
            result.message = f"恢复能力测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    # ==================== 兼容性测试 ====================
    
    def test_compatibility_concurrent_read(self):
        """兼容性测试：并发读取"""
        result = TestResult("兼容性测试", "并发读取")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'concurrent_test',
                'description': '并发读取测试'
            }
            pm.save_project_memory(memory)
            
            results = []
            errors = []
            
            def read_memory():
                try:
                    loaded = pm.load_project_memory()
                    results.append(loaded)
                except Exception as e:
                    errors.append(e)
            
            threads = [threading.Thread(target=read_memory) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            assert len(errors) == 0, f"并发读取错误: {errors}"
            assert len(results) == 10, "并发读取结果数量错误"
            
            result.passed = True
            result.message = f"并发读取成功，{len(results)} 次读取"
            result.details = {
                'threads': 10,
                'successful_reads': len(results),
                'errors': len(errors)
            }
        
        except Exception as e:
            result.error = e
            result.message = f"并发读取测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_compatibility_concurrent_write(self):
        """兼容性测试：并发写入"""
        result = TestResult("兼容性测试", "并发写入")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            errors = []
            lock = threading.Lock()
            
            def write_memory(index):
                try:
                    with lock:
                        memory = pm.load_project_memory()
                        if memory.get('write_order') is None:
                            memory['write_order'] = []
                        memory['write_order'].append(index)
                        pm.save_project_memory(memory)
                except Exception as e:
                    errors.append(e)
            
            threads = [threading.Thread(target=write_memory, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            result.passed = len(errors) == 0
            result.message = f"并发写入{'成功' if len(errors) == 0 else '有错误'}"
            result.details = {
                'threads': 5,
                'errors': len(errors)
            }
        
        except Exception as e:
            result.error = e
            result.message = f"并发写入测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_compatibility_path_handling(self):
        """兼容性测试：路径处理"""
        result = TestResult("兼容性测试", "路径处理")
        start = time.time()
        
        try:
            registry = ProjectRegistry()
            
            test_paths = [
                str(self.test_dir / "normal_path"),
                str(self.test_dir / "路径 with 中文"),
                str(self.test_dir / "path with spaces"),
            ]
            
            registered = []
            for path in test_paths:
                Path(path).mkdir(parents=True, exist_ok=True)
                project_id = registry.register_project(path)
                registered.append(project_id)
            
            for i, project_id in enumerate(registered):
                project = registry.get_project(project_id)
                assert project is not None, f"路径 {test_paths[i]} 注册失败"
            
            result.passed = True
            result.message = "路径处理兼容性验证通过"
            result.details = {
                'tested_paths': len(test_paths),
                'registered': len(registered)
            }
        
        except Exception as e:
            result.error = e
            result.message = f"路径处理测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    def test_compatibility_data_format(self):
        """兼容性测试：数据格式"""
        result = TestResult("兼容性测试", "数据格式")
        start = time.time()
        
        try:
            pm = ProjectMemoryManager()
            
            memory = {
                'project_name': 'format_test',
                'list_data': [1, 2, 3, 'a', 'b', 'c'],
                'dict_data': {'key1': 'value1', 'key2': 123},
                'mixed_data': {
                    'nested': {
                        'deep': ['x', 'y', 'z']
                    }
                }
            }
            
            pm.save_project_memory(memory)
            loaded = pm.load_project_memory()
            
            assert loaded['list_data'] == memory['list_data'], "列表数据格式错误"
            assert loaded['dict_data'] == memory['dict_data'], "字典数据格式错误"
            
            result.passed = True
            result.message = "数据格式兼容性验证通过"
            result.details = {
                'list_preserved': True,
                'dict_preserved': True
            }
        
        except Exception as e:
            result.error = e
            result.message = f"数据格式测试失败: {str(e)}"
        
        result.duration = time.time() - start
        self.record_result(result)
    
    # ==================== 运行所有测试 ====================
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("Trae Memory 2.0 全面测试套件")
        print("=" * 70)
        
        self.setup()
        
        try:
            print("\n📋 功能测试")
            print("-" * 70)
            self.test_functional_data_storage()
            self.test_functional_data_retrieval()
            self.test_functional_memory_update()
            self.test_functional_memory_delete()
            self.test_functional_project_registration()
            self.test_functional_conversation_tracking()
            self.test_functional_auto_extraction()
            
            print("\n⚡ 性能测试")
            print("-" * 70)
            self.test_performance_storage_speed()
            self.test_performance_retrieval_speed()
            self.test_performance_large_data()
            self.test_performance_memory_usage()
            
            print("\n🔒 可靠性测试")
            print("-" * 70)
            self.test_reliability_error_handling()
            self.test_reliability_data_integrity()
            self.test_reliability_long_term_storage()
            self.test_reliability_recovery()
            
            print("\n🔄 兼容性测试")
            print("-" * 70)
            self.test_compatibility_concurrent_read()
            self.test_compatibility_concurrent_write()
            self.test_compatibility_path_handling()
            self.test_compatibility_data_format()
        
        finally:
            self.teardown()
    
    def generate_report(self) -> Dict:
        """生成测试报告"""
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {'passed': 0, 'failed': 0, 'total': 0}
            categories[r.category]['total'] += 1
            if r.passed:
                categories[r.category]['passed'] += 1
            else:
                categories[r.category]['failed'] += 1
        
        total_passed = sum(1 for r in self.results if r.passed)
        total_failed = len(self.results) - total_passed
        
        report = {
            'summary': {
                'total_tests': len(self.results),
                'passed': total_passed,
                'failed': total_failed,
                'pass_rate': f"{total_passed/len(self.results)*100:.1f}%" if self.results else "0%",
                'total_duration': f"{total_duration:.2f}s",
                'test_date': datetime.now().isoformat()
            },
            'categories': categories,
            'results': [r.to_dict() for r in self.results],
            'failed_tests': [r.to_dict() for r in self.results if not r.passed]
        }
        
        return report
    
    def print_summary(self):
        """打印测试摘要"""
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("测试报告摘要")
        print("=" * 70)
        
        summary = report['summary']
        print(f"\n📊 总体结果:")
        print(f"   总测试数: {summary['total_tests']}")
        print(f"   通过: {summary['passed']}")
        print(f"   失败: {summary['failed']}")
        print(f"   通过率: {summary['pass_rate']}")
        print(f"   总耗时: {summary['total_duration']}")
        
        print(f"\n📋 分类统计:")
        for category, stats in report['categories'].items():
            status = "✅" if stats['failed'] == 0 else "⚠️"
            print(f"   {status} {category}: {stats['passed']}/{stats['total']} 通过")
        
        if report['failed_tests']:
            print(f"\n❌ 失败的测试:")
            for test in report['failed_tests']:
                print(f"   - [{test['category']}] {test['name']}: {test['message']}")
                if test['error']:
                    print(f"     错误: {test['error']}")
        
        print("\n" + "=" * 70)


def main():
    """主函数"""
    suite = ComprehensiveTestSuite()
    suite.run_all_tests()
    suite.print_summary()
    
    report = suite.generate_report()
    
    report_file = Path(__file__).parent / 'test_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细测试报告已保存: {report_file}")
    
    return report['summary']['failed'] == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
