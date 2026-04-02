#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目注册表 - 管理多个项目的记忆
支持项目注册、切换、搜索等功能
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProjectRegistry:
    """
    项目注册表
    
    功能：
    - 注册和管理多个项目
    - 项目切换
    - 跨项目搜索
    - 项目分组
    """
    
    REGISTRY_DIR = '.trae'
    REGISTRY_FILE = 'project_registry.json'
    
    def __init__(self, registry_path: str = None):
        """
        初始化项目注册表
        
        Args:
            registry_path: 注册表存储路径，默认为用户主目录
        """
        if registry_path is None:
            registry_path = str(Path.home() / self.REGISTRY_DIR)
        
        self.registry_path = Path(registry_path)
        self.registry_file = self.registry_path / self.REGISTRY_FILE
        self.current_project_id = None
        
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.projects = data.get('projects', {})
                self.current_project_id = data.get('current_project_id')
                self.groups = data.get('groups', {})
            except Exception:
                self.projects = {}
                self.current_project_id = None
                self.groups = {}
        else:
            self.projects = {}
            self.current_project_id = None
            self.groups = {}
    
    def _save_registry(self):
        """保存注册表"""
        data = {
            'projects': self.projects,
            'current_project_id': self.current_project_id,
            'groups': self.groups,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def register_project(self, project_path: str, name: str = None, 
                         description: str = None, group: str = None,
                         tags: List[str] = None) -> str:
        """
        注册项目
        
        Args:
            project_path: 项目路径
            name: 项目名称（默认使用目录名）
            description: 项目描述
            group: 所属分组
            tags: 标签列表
            
        Returns:
            项目 ID
        """
        project_path = str(Path(project_path).resolve())
        
        for pid, pinfo in self.projects.items():
            if pinfo['path'] == project_path:
                if name:
                    pinfo['name'] = name
                if description:
                    pinfo['description'] = description
                if tags:
                    pinfo['tags'] = tags
                if group:
                    old_group = pinfo.get('group')
                    if old_group and old_group in self.groups:
                        if pid in self.groups[old_group]:
                            self.groups[old_group].remove(pid)
                    pinfo['group'] = group
                    if group not in self.groups:
                        self.groups[group] = []
                    if pid not in self.groups[group]:
                        self.groups[group].append(pid)
                pinfo['updated_at'] = datetime.now().isoformat()
                self._save_registry()
                return pid
        
        project_id = f"proj_{len(self.projects) + 1:04d}"
        
        if name is None:
            name = Path(project_path).name
        
        self.projects[project_id] = {
            'id': project_id,
            'name': name,
            'path': project_path,
            'description': description or '',
            'tags': tags or [],
            'group': group,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_accessed': None,
            'access_count': 0
        }
        
        if group:
            if group not in self.groups:
                self.groups[group] = []
            self.groups[group].append(project_id)
        
        if self.current_project_id is None:
            self.current_project_id = project_id
        
        self._save_registry()
        
        print(f"✅ 注册项目: {name} (ID: {project_id})")
        return project_id
    
    def unregister_project(self, project_id: str) -> bool:
        """
        注销项目
        
        Args:
            project_id: 项目 ID
            
        Returns:
            是否成功
        """
        if project_id not in self.projects:
            print(f"❌ 项目不存在: {project_id}")
            return False
        
        project = self.projects[project_id]
        name = project['name']
        
        group = project.get('group')
        if group and group in self.groups:
            if project_id in self.groups[group]:
                self.groups[group].remove(project_id)
        
        del self.projects[project_id]
        
        if self.current_project_id == project_id:
            if self.projects:
                self.current_project_id = list(self.projects.keys())[0]
            else:
                self.current_project_id = None
        
        self._save_registry()
        
        print(f"✅ 注销项目: {name}")
        return True
    
    def switch_project(self, project_id: str) -> bool:
        """
        切换当前项目
        
        Args:
            project_id: 项目 ID
            
        Returns:
            是否成功
        """
        if project_id not in self.projects:
            print(f"❌ 项目不存在: {project_id}")
            return False
        
        self.current_project_id = project_id
        self.projects[project_id]['last_accessed'] = datetime.now().isoformat()
        self.projects[project_id]['access_count'] += 1
        
        self._save_registry()
        
        project = self.projects[project_id]
        print(f"✅ 切换到项目: {project['name']} ({project['path']})")
        return True
    
    def get_current_project(self) -> Optional[Dict]:
        """
        获取当前项目信息
        
        Returns:
            当前项目信息字典
        """
        if self.current_project_id and self.current_project_id in self.projects:
            return self.projects[self.current_project_id]
        return None
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        获取项目信息
        
        Args:
            project_id: 项目 ID
            
        Returns:
            项目信息字典
        """
        return self.projects.get(project_id)
    
    def list_projects(self, group: str = None, tag: str = None) -> List[Dict]:
        """
        列出项目
        
        Args:
            group: 按分组过滤
            tag: 按标签过滤
            
        Returns:
            项目列表
        """
        projects = list(self.projects.values())
        
        if group:
            projects = [p for p in projects if p.get('group') == group]
        
        if tag:
            projects = [p for p in projects if tag in p.get('tags', [])]
        
        projects.sort(key=lambda x: x.get('last_accessed') or x.get('created_at'), reverse=True)
        
        return projects
    
    def list_groups(self) -> List[str]:
        """
        列出所有分组
        
        Returns:
            分组名称列表
        """
        return list(self.groups.keys())
    
    def search_projects(self, keyword: str) -> List[Dict]:
        """
        搜索项目
        
        Args:
            keyword: 关键词
            
        Returns:
            匹配的项目列表
        """
        keyword = keyword.lower()
        results = []
        
        for project in self.projects.values():
            if (keyword in project['name'].lower() or
                keyword in project.get('description', '').lower() or
                keyword in project['path'].lower() or
                any(keyword in tag.lower() for tag in project.get('tags', []))):
                results.append(project)
        
        return results
    
    def get_recent_projects(self, limit: int = 5) -> List[Dict]:
        """
        获取最近访问的项目
        
        Args:
            limit: 限制数量
            
        Returns:
            项目列表
        """
        projects = [p for p in self.projects.values() if p.get('last_accessed')]
        projects.sort(key=lambda x: x.get('last_accessed'), reverse=True)
        return projects[:limit]
    
    def get_frequent_projects(self, limit: int = 5) -> List[Dict]:
        """
        获取最常访问的项目
        
        Args:
            limit: 限制数量
            
        Returns:
            项目列表
        """
        projects = list(self.projects.values())
        projects.sort(key=lambda x: x.get('access_count', 0), reverse=True)
        return projects[:limit]
    
    def update_project_info(self, project_id: str, **kwargs) -> bool:
        """
        更新项目信息
        
        Args:
            project_id: 项目 ID
            **kwargs: 要更新的字段
            
        Returns:
            是否成功
        """
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        for key, value in kwargs.items():
            if key in ['name', 'description', 'tags']:
                project[key] = value
            elif key == 'group':
                old_group = project.get('group')
                if old_group and old_group in self.groups:
                    if project_id in self.groups[old_group]:
                        self.groups[old_group].remove(project_id)
                
                project['group'] = value
                if value:
                    if value not in self.groups:
                        self.groups[value] = []
                    if project_id not in self.groups[value]:
                        self.groups[value].append(project_id)
        
        project['updated_at'] = datetime.now().isoformat()
        self._save_registry()
        
        return True
    
    def export_registry(self) -> str:
        """
        导出注册表
        
        Returns:
            JSON 字符串
        """
        data = {
            'projects': self.projects,
            'current_project_id': self.current_project_id,
            'groups': self.groups,
            'exported_at': datetime.now().isoformat()
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def import_registry(self, json_data: str, merge: bool = True) -> bool:
        """
        导入注册表
        
        Args:
            json_data: JSON 字符串
            merge: 是否合并（True）或覆盖（False）
            
        Returns:
            是否成功
        """
        try:
            data = json.loads(json_data)
            
            if not merge:
                self.projects = {}
                self.groups = {}
            
            for pid, pinfo in data.get('projects', {}).items():
                if pid not in self.projects:
                    self.projects[pid] = pinfo
            
            for group, pids in data.get('groups', {}).items():
                if group not in self.groups:
                    self.groups[group] = []
                for pid in pids:
                    if pid not in self.groups[group]:
                        self.groups[group].append(pid)
            
            self._save_registry()
            return True
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        total_projects = len(self.projects)
        total_groups = len(self.groups)
        total_accesses = sum(p.get('access_count', 0) for p in self.projects.values())
        
        tags = set()
        for p in self.projects.values():
            tags.update(p.get('tags', []))
        
        return {
            'total_projects': total_projects,
            'total_groups': total_groups,
            'total_accesses': total_accesses,
            'total_tags': len(tags),
            'current_project': self.current_project_id
        }


class MultiProjectMemoryManager:
    """
    多项目记忆管理器
    
    结合 ProjectRegistry 和 ProjectMemoryManager
    提供统一的多项目管理接口
    """
    
    def __init__(self, registry_path: str = None):
        """
        初始化多项目记忆管理器
        
        Args:
            registry_path: 注册表路径
        """
        self.registry = ProjectRegistry(registry_path)
        self._managers = {}
    
    def _get_manager(self, project_id: str = None):
        """
        获取项目记忆管理器
        
        Args:
            project_id: 项目 ID，默认为当前项目
            
        Returns:
            ProjectMemoryManager 实例
        """
        if project_id is None:
            project_id = self.registry.current_project_id
        
        if project_id is None:
            return None
        
        if project_id not in self._managers:
            project = self.registry.get_project(project_id)
            if project:
                from project_memory import ProjectMemoryManager
                self._managers[project_id] = ProjectMemoryManager(project['path'])
            else:
                return None
        
        return self._managers.get(project_id)
    
    def register_project(self, project_path: str, **kwargs) -> str:
        """
        注册项目并初始化记忆
        
        Args:
            project_path: 项目路径
            **kwargs: 其他参数
            
        Returns:
            项目 ID
        """
        project_id = self.registry.register_project(project_path, **kwargs)
        
        from project_memory import ProjectMemoryManager
        manager = ProjectMemoryManager(project_path)
        memory = manager.extract_from_project()
        manager.save_project_memory(memory)
        
        self._managers[project_id] = manager
        
        return project_id
    
    def switch_to(self, project_id: str) -> bool:
        """
        切换到指定项目
        
        Args:
            project_id: 项目 ID
            
        Returns:
            是否成功
        """
        return self.registry.switch_project(project_id)
    
    def load_memory(self, project_id: str = None) -> Dict:
        """
        加载项目记忆
        
        Args:
            project_id: 项目 ID
            
        Returns:
            项目记忆字典
        """
        manager = self._get_manager(project_id)
        if manager:
            return manager.load_project_memory()
        return {}
    
    def save_memory(self, memory: Dict, project_id: str = None) -> bool:
        """
        保存项目记忆
        
        Args:
            memory: 记忆字典
            project_id: 项目 ID
            
        Returns:
            是否成功
        """
        manager = self._get_manager(project_id)
        if manager:
            return manager.save_project_memory(memory)
        return False
    
    def list_projects(self, **kwargs) -> List[Dict]:
        """
        列出项目
        
        Returns:
            项目列表
        """
        return self.registry.list_projects(**kwargs)
    
    def search_all_projects(self, keyword: str) -> List[Dict]:
        """
        在所有项目中搜索
        
        Args:
            keyword: 关键词
            
        Returns:
            搜索结果列表
        """
        results = []
        
        for project_id, project in self.registry.projects.items():
            manager = self._get_manager(project_id)
            if manager:
                memory = manager.load_project_memory()
                
                searchable = ' '.join([
                    memory.get('description', ''),
                    ' '.join(memory.get('tech_stack', [])),
                    ' '.join(memory.get('dependencies', [])),
                    ' '.join(memory.get('issues', [])),
                    ' '.join(memory.get('decisions', []))
                ])
                
                if keyword.lower() in searchable.lower():
                    results.append({
                        'project_id': project_id,
                        'project_name': project['name'],
                        'project_path': project['path'],
                        'memory': memory
                    })
        
        return results


def main():
    """测试函数"""
    import sys
    
    registry = ProjectRegistry()
    
    print("=" * 60)
    print("项目注册表测试")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'register':
            path = sys.argv[2] if len(sys.argv) > 2 else '.'
            name = sys.argv[3] if len(sys.argv) > 3 else None
            registry.register_project(path, name)
        
        elif command == 'list':
            projects = registry.list_projects()
            print(f"\n📋 已注册项目 ({len(projects)} 个):")
            for p in projects:
                current = "👉 " if p['id'] == registry.current_project_id else "   "
                print(f"{current}{p['name']} (ID: {p['id']})")
                print(f"      路径: {p['path']}")
                print(f"      访问: {p.get('access_count', 0)} 次")
        
        elif command == 'switch':
            if len(sys.argv) > 2:
                registry.switch_project(sys.argv[2])
        
        elif command == 'search':
            if len(sys.argv) > 2:
                results = registry.search_projects(sys.argv[2])
                print(f"\n🔍 搜索结果 ({len(results)} 个):")
                for p in results:
                    print(f"   - {p['name']} ({p['path']})")
        
        elif command == 'stats':
            stats = registry.get_stats()
            print(f"\n📊 统计信息:")
            print(f"   总项目数: {stats['total_projects']}")
            print(f"   总分组数: {stats['total_groups']}")
            print(f"   总访问数: {stats['total_accesses']}")
            print(f"   当前项目: {stats['current_project']}")
    
    else:
        print("\n用法:")
        print("  python project_registry.py register [路径] [名称]  # 注册项目")
        print("  python project_registry.py list                    # 列出项目")
        print("  python project_registry.py switch [项目ID]         # 切换项目")
        print("  python project_registry.py search [关键词]         # 搜索项目")
        print("  python project_registry.py stats                   # 统计信息")


if __name__ == '__main__':
    main()
