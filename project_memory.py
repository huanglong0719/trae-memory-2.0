#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目级记忆管理器 - 支持项目级 MEMORY.md 文件
类似 Claude Code 的 CLAUDE.md 功能
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProjectMemoryManager:
    """
    项目级记忆管理器
    
    功能：
    - 支持项目级 MEMORY.md 文件
    - 自动提取项目信息
    - 与全局记忆库同步
    - 支持多项目切换
    """
    
    MEMORY_DIR = '.trae'
    MEMORY_FILE = 'MEMORY.md'
    
    def __init__(self, project_path: str = None):
        """
        初始化项目记忆管理器
        
        Args:
            project_path: 项目路径，默认为当前目录
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.memory_dir = self.project_path / self.MEMORY_DIR
        self.memory_file = self.memory_dir / self.MEMORY_FILE
        
    def load_project_memory(self) -> Dict:
        """
        加载项目记忆
        
        Returns:
            项目记忆字典
        """
        if not self.memory_file.exists():
            return self._get_default_memory()
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_memory_md(content)
        except Exception as e:
            print(f"⚠️  加载项目记忆失败：{e}")
            return self._get_default_memory()
    
    def save_project_memory(self, memory: Dict) -> bool:
        """
        保存项目记忆
        
        Args:
            memory: 项目记忆字典
            
        Returns:
            是否成功保存
        """
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            
            content = self.generate_memory_md(memory)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 项目记忆已保存到：{self.memory_file}")
            return True
        except Exception as e:
            print(f"❌ 保存项目记忆失败：{e}")
            return False
    
    def parse_memory_md(self, content: str) -> Dict:
        """
        解析 MEMORY.md 文件
        
        Args:
            content: 文件内容
            
        Returns:
            解析后的记忆字典
        """
        memory = self._get_default_memory()
        
        sections = {
            '基本信息': self._parse_basic_info,
            '技术规范': self._parse_tech_specs,
            '用户偏好': self._parse_preferences,
            '已知问题': self._parse_issues,
            '重要决策': self._parse_decisions,
            '相关记忆': self._parse_related_memories,
            '自定义数据': self._parse_custom_data,
        }
        
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            section_match = re.match(r'^##\s+(.+)$', line)
            if section_match:
                if current_section and current_section in sections:
                    parser = sections[current_section]
                    memory.update(parser('\n'.join(current_content)))
                
                current_section = section_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section and current_section in sections:
            parser = sections[current_section]
            memory.update(parser('\n'.join(current_content)))
        
        return memory
    
    def generate_memory_md(self, memory: Dict) -> str:
        """
        生成 MEMORY.md 文件内容
        
        Args:
            memory: 项目记忆字典
            
        Returns:
            Markdown 格式的文件内容
        """
        lines = [
            "# Project Memory",
            "",
            f"> 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 基本信息",
            ""
        ]
        
        if memory.get('project_name'):
            lines.append(f"- 项目名称：{memory['project_name']}")
        if memory.get('tech_stack'):
            lines.append(f"- 技术栈：{', '.join(memory['tech_stack'])}")
        if memory.get('created_at'):
            lines.append(f"- 创建时间：{memory['created_at']}")
        if memory.get('description'):
            lines.append(f"- 项目描述：{memory['description']}")
        
        lines.extend(["", "## 技术规范", ""])
        
        if memory.get('code_style'):
            lines.append(f"- 代码风格：{memory['code_style']}")
        if memory.get('test_framework'):
            lines.append(f"- 测试框架：{memory['test_framework']}")
        if memory.get('deployment'):
            lines.append(f"- 部署方式：{memory['deployment']}")
        if memory.get('dependencies'):
            lines.append(f"- 主要依赖：{', '.join(memory['dependencies'][:10])}")
        
        lines.extend(["", "## 用户偏好", ""])
        
        if memory.get('editor'):
            lines.append(f"- 编辑器：{memory['editor']}")
        if memory.get('preferred_language'):
            lines.append(f"- 偏好语言：{memory['preferred_language']}")
        
        for key, value in memory.get('custom_preferences', {}).items():
            lines.append(f"- {key}：{value}")
        
        lines.extend(["", "## 已知问题", ""])
        
        for issue in memory.get('issues', []):
            lines.append(f"- {issue}")
        
        if not memory.get('issues'):
            lines.append("- 暂无已知问题")
        
        lines.extend(["", "## 重要决策", ""])
        
        for decision in memory.get('decisions', []):
            lines.append(f"- {decision}")
        
        if not memory.get('decisions'):
            lines.append("- 暂无重要决策")
        
        lines.extend(["", "## 相关记忆", ""])
        
        for mem_id in memory.get('related_memory_ids', []):
            lines.append(f"- #{mem_id}")
        
        if not memory.get('related_memory_ids'):
            lines.append("- 暂无相关记忆")
        
        default_fields = {
            'project_name', 'tech_stack', 'created_at', 'description',
            'code_style', 'test_framework', 'deployment', 'dependencies',
            'editor', 'preferred_language', 'custom_preferences',
            'issues', 'decisions', 'related_memory_ids'
        }
        
        custom_fields = {k: v for k, v in memory.items() if k not in default_fields}
        
        if custom_fields:
            lines.extend(["", "## 自定义数据", ""])
            lines.append("```json")
            lines.append(json.dumps(custom_fields, ensure_ascii=False, indent=2))
            lines.append("```")
        
        lines.append("")
        
        return '\n'.join(lines)
    
    def extract_from_project(self) -> Dict:
        """
        从项目文件自动提取信息
        
        Returns:
            提取的项目信息字典
        """
        memory = self._get_default_memory()
        
        self._detect_package_json(memory)
        self._detect_requirements_txt(memory)
        self._detect_config_files(memory)
        self._detect_readme(memory)
        
        memory['project_name'] = self.project_path.name
        memory['created_at'] = datetime.now().strftime('%Y-%m-%d')
        
        return memory
    
    def sync_with_store(self, store, memory_ids: List[int] = None) -> bool:
        """
        与全局记忆库同步
        
        Args:
            store: MemoryStore 实例
            memory_ids: 要关联的记忆 ID 列表
            
        Returns:
            是否成功同步
        """
        try:
            memory = self.load_project_memory()
            
            if memory_ids:
                memory['related_memory_ids'] = memory_ids
            
            tags = ['project', self.project_path.name]
            for tech in memory.get('tech_stack', []):
                tags.append(tech.lower())
            
            if hasattr(store, 'add_memory'):
                memory_id = store.add_memory(
                    category='rule',
                    title=f"项目规范：{memory.get('project_name', 'Unknown')}",
                    content=self._memory_to_content(memory),
                    tags=tags,
                    source='project_file'
                )
                
                if memory_id:
                    if 'related_memory_ids' not in memory:
                        memory['related_memory_ids'] = []
                    memory['related_memory_ids'].append(memory_id)
                    
                    self.save_project_memory(memory)
                    print(f"✅ 已同步到全局记忆库，ID: {memory_id}")
                    return True
            
            return False
        except Exception as e:
            print(f"❌ 同步失败：{e}")
            return False
    
    def _get_default_memory(self) -> Dict:
        """获取默认记忆结构"""
        return {
            'project_name': '',
            'tech_stack': [],
            'created_at': '',
            'description': '',
            'code_style': '',
            'test_framework': '',
            'deployment': '',
            'dependencies': [],
            'editor': '',
            'preferred_language': '',
            'custom_preferences': {},
            'issues': [],
            'decisions': [],
            'related_memory_ids': []
        }
    
    def _parse_basic_info(self, content: str) -> Dict:
        """解析基本信息"""
        info = {}
        
        patterns = {
            'project_name': r'项目名称[：:]\s*(.+)',
            'tech_stack': r'技术栈[：:]\s*(.+)',
            'created_at': r'创建时间[：:]\s*(.+)',
            'description': r'项目描述[：:]\s*(.+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if key == 'tech_stack':
                    info[key] = [t.strip() for t in value.split(',')]
                else:
                    info[key] = value
        
        return info
    
    def _parse_tech_specs(self, content: str) -> Dict:
        """解析技术规范"""
        specs = {}
        
        patterns = {
            'code_style': r'代码风格[：:]\s*(.+)',
            'test_framework': r'测试框架[：:]\s*(.+)',
            'deployment': r'部署方式[：:]\s*(.+)',
            'dependencies': r'主要依赖[：:]\s*(.+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if key == 'dependencies':
                    specs[key] = [d.strip() for d in value.split(',')]
                else:
                    specs[key] = value
        
        return specs
    
    def _parse_preferences(self, content: str) -> Dict:
        """解析用户偏好"""
        prefs = {'custom_preferences': {}}
        
        patterns = {
            'editor': r'编辑器[：:]\s*(.+)',
            'preferred_language': r'偏好语言[：:]\s*(.+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                prefs[key] = match.group(1).strip()
        
        return prefs
    
    def _parse_issues(self, content: str) -> Dict:
        """解析已知问题"""
        issues = []
        for line in content.split('\n'):
            match = re.match(r'^-\s*(.+)$', line.strip())
            if match and '暂无已知问题' not in line:
                issues.append(match.group(1).strip())
        return {'issues': issues}
    
    def _parse_decisions(self, content: str) -> Dict:
        """解析重要决策"""
        decisions = []
        for line in content.split('\n'):
            match = re.match(r'^-\s*(.+)$', line.strip())
            if match and '暂无重要决策' not in line:
                decisions.append(match.group(1).strip())
        return {'decisions': decisions}
    
    def _parse_related_memories(self, content: str) -> Dict:
        """解析相关记忆"""
        ids = []
        for line in content.split('\n'):
            match = re.match(r'^-\s*#(\d+)', line.strip())
            if match:
                ids.append(int(match.group(1)))
        return {'related_memory_ids': ids}
    
    def _parse_custom_data(self, content: str) -> Dict:
        """解析自定义数据"""
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        return {}
    
    def _detect_package_json(self, memory: Dict):
        """检测 package.json"""
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                memory['tech_stack'].append('Node.js')
                
                if 'dependencies' in data:
                    deps = list(data['dependencies'].keys())
                    memory['dependencies'].extend(deps[:10])
                    
                    if 'react' in deps:
                        memory['tech_stack'].append('React')
                    elif 'vue' in deps:
                        memory['tech_stack'].append('Vue')
                    elif 'angular' in deps:
                        memory['tech_stack'].append('Angular')
                
                if 'devDependencies' in data:
                    dev_deps = data['devDependencies']
                    if 'eslint' in dev_deps:
                        memory['code_style'] = 'ESLint'
                    if 'jest' in dev_deps or 'vitest' in dev_deps:
                        memory['test_framework'] = 'Jest' if 'jest' in dev_deps else 'Vitest'
                
                if data.get('description'):
                    memory['description'] = data['description']
            except Exception:
                pass
    
    def _detect_requirements_txt(self, memory: Dict):
        """检测 requirements.txt"""
        requirements = self.project_path / 'requirements.txt'
        if requirements.exists():
            try:
                with open(requirements, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                memory['tech_stack'].append('Python')
                
                deps = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0]
                        deps.append(pkg)
                
                memory['dependencies'].extend(deps[:10])
                
                if any('pytest' in d for d in deps):
                    memory['test_framework'] = 'pytest'
                if any('black' in d for d in deps):
                    memory['code_style'] = 'Black'
                elif any('flake8' in d for d in deps):
                    memory['code_style'] = 'Flake8'
            except Exception:
                pass
    
    def _detect_config_files(self, memory: Dict):
        """检测配置文件"""
        config_files = {
            '.eslintrc': ('ESLint', 'code_style'),
            '.eslintrc.json': ('ESLint', 'code_style'),
            '.eslintrc.js': ('ESLint', 'code_style'),
            'pytest.ini': ('pytest', 'test_framework'),
            'setup.py': ('Python Package', 'deployment'),
            'Dockerfile': ('Docker', 'deployment'),
            'docker-compose.yml': ('Docker Compose', 'deployment'),
        }
        
        for filename, (tool, field) in config_files.items():
            if (self.project_path / filename).exists():
                memory[field] = tool
    
    def _detect_readme(self, memory: Dict):
        """检测 README"""
        readme_files = ['README.md', 'README.rst', 'README.txt']
        
        for filename in readme_files:
            readme = self.project_path / filename
            if readme.exists():
                try:
                    with open(readme, 'r', encoding='utf-8') as f:
                        content = f.read(500)
                    
                    if not memory.get('description'):
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#') and len(line) > 10:
                                memory['description'] = line[:200]
                                break
                except Exception:
                    pass
                break
    
    def _memory_to_content(self, memory: Dict) -> str:
        """将记忆转换为内容字符串"""
        parts = []
        
        if memory.get('description'):
            parts.append(f"项目描述：{memory['description']}")
        
        if memory.get('tech_stack'):
            parts.append(f"技术栈：{', '.join(memory['tech_stack'])}")
        
        if memory.get('code_style'):
            parts.append(f"代码风格：{memory['code_style']}")
        
        if memory.get('test_framework'):
            parts.append(f"测试框架：{memory['test_framework']}")
        
        if memory.get('deployment'):
            parts.append(f"部署方式：{memory['deployment']}")
        
        return '\n'.join(parts)


def main():
    """测试函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法：")
        print("  python project_memory.py extract [项目路径]  # 提取项目信息")
        print("  python project_memory.py load [项目路径]    # 加载项目记忆")
        print("  python project_memory.py save [项目路径]    # 保存项目记忆")
        return
    
    command = sys.argv[1]
    project_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    pm = ProjectMemoryManager(project_path)
    
    if command == 'extract':
        memory = pm.extract_from_project()
        print("\n📦 提取的项目信息：")
        print(json.dumps(memory, indent=2, ensure_ascii=False))
        
        if input("\n是否保存到 MEMORY.md？(y/n): ").lower() == 'y':
            pm.save_project_memory(memory)
    
    elif command == 'load':
        memory = pm.load_project_memory()
        print("\n📂 项目记忆：")
        print(json.dumps(memory, indent=2, ensure_ascii=False))
    
    elif command == 'save':
        memory = pm.extract_from_project()
        pm.save_project_memory(memory)


if __name__ == '__main__':
    main()
