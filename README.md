# Trae Memory 2.0

融合 EvoMap 理念的 Trae Memory 升级版本，实现记忆的自我进化机制。

## 🎯 核心特性

### 1. GDI 评分系统
- **内在质量** (35%): 内容长度、结构完整性、代码示例、标签丰富度
- **使用指标** (30%): 访问频率、复用率、最近使用
- **社交信号** (20%): 用户反馈、点赞标记
- **新鲜度** (15%): 基于创建和更新时间

### 2. 多维度验证管道
- **内容验证**: 最小长度、标题完整性、代码块闭合
- **代码验证**: Python 语法检查
- **唯一性验证**: 检测重复记忆
- **事实验证**: 不确定性表述检测

### 3. 知识图谱管理
- **关系类型**: derives_from, references, contradicts, extends, replaces, related_to
- **继承链**: 追踪知识演化历史
- **派生功能**: 从现有记忆创建新版本

### 4. 进化引擎
- **突变检测**: 基于反馈、GDI 评分、验证结果
- **突变生成**: REPAIR（修复）、OPTIMIZE（优化）、INNOVATE（创新）
- **自然选择**: 基于 GDI 评分选择最优版本

## 📁 文件结构

```
trae-memory-2.0/
├── gdi_scorer.py          # GDI 评分器
├── validation_pipeline.py  # 验证管道
├── knowledge_graph.py      # 知识图谱管理器
├── evolution_engine.py     # 进化引擎
├── trae_memory_2.py       # 集成模块
├── cli.py                 # 命令行接口
├── test_2.0.py            # 测试脚本
└── README.md              # 本文档
```

## 🚀 快速开始

### 方法一：使用 Python API

```python
from trae_memory_2 import TraeMemory2

# 创建实例
tm = TraeMemory2()

# 添加记忆（自动验证）
memory_id = tm.add_memory(
    category='knowledge',
    title='Python 装饰器指南',
    content='装饰器是 Python 的强大特性...',
    tags=['python', '装饰器']
)

# 获取质量报告
report = tm.get_memory_quality(memory_id)
print(f"GDI 评分：{report['gdi_score']:.3f}")
print(f"质量等级：{report['quality_level']}")

# 派生新记忆
child_id = tm.derive_memory(
    parent_id=memory_id,
    title='Python 类装饰器',
    content='类装饰器用于修饰类...'
)
```

### 方法二：使用 CLI

```bash
# 查看 GDI 评分
python cli.py gdi 1

# 验证记忆质量
python cli.py validate 1

# 显示关联记忆
python cli.py relations 1

# 显示继承链
python cli.py inherit 1

# 派生新记忆
python cli.py derive 1 "新标题" "新内容"

# 触发进化
python cli.py evolve 1

# 查看进化历史
python cli.py history 1

# 查看图谱统计
python cli.py stats
```

## 📊 GDI 评分示例

```python
from gdi_scorer import GDIScorer

scorer = GDIScorer()

memory = {
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
    ''',
    'tags': ['python', '函数', '最佳实践'],
    'access_count': 5,
    'created_at': '2024-01-01T00:00:00'
}

result = scorer.calculate_gdi(memory)
print(f"综合评分：{result['gdi_score']:.3f}")
print(f"内在质量：{result['gdi_intrinsic']:.3f}")
print(f"使用指标：{result['gdi_usage']:.3f}")
```

## 🔍 验证管道示例

```python
from validation_pipeline import ValidationPipeline

pipeline = ValidationPipeline()

memory = {
    'title': '测试',
    'content': '内容太短',
    'tags': []
}

results = pipeline.validate(memory)

for result in results:
    print(f"{result.validator_name}: {'通过' if result.passed else '未通过'}")
    if result.issues:
        for issue in result.issues:
            print(f"  - {issue}")
```

## 🌳 知识图谱示例

```python
from knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph('path/to/database.db')

# 添加关系
kg.add_relation(source_id=1, target_id=2, relation_type='extends')

# 查找相关记忆
related = kg.find_related(memory_id=1, depth=2)

# 获取继承链
chain = kg.get_inheritance_chain(memory_id=5)
for mem in chain:
    print(f"#{mem['id']}: {mem['title']} (第{mem['generation']}代)")

# 派生新记忆
new_id = kg.derive_memory(
    parent_id=1,
    modifications={'title': '新标题', 'content': '新内容'}
)
```

## 🧬 进化引擎示例

```python
from evolution_engine import EvolutionEngine, MutationType

engine = EvolutionEngine(store, gdi_scorer, validation_pipeline, knowledge_graph)

# 检测进化机会
memory = get_memory(1)
mutation_type = engine.detect_mutation_opportunity(
    memory,
    context={'feedback': 'negative'}
)

if mutation_type == MutationType.REPAIR:
    print("检测到修复机会")
    
    # 生成变异
    mutant = engine.generate_mutation(memory, mutation_type)
    
    # 选择与继承
    selected = engine.select_and_inherit(memory, mutant)
```

## 📈 质量改进建议

GDI 评分器会自动提供改进建议：

```python
suggestions = scorer.get_quality_suggestions(memory)
for s in suggestions:
    print(f"- {s}")
```

常见建议：
- 内容过短，建议补充详细说明或示例
- 标题不够具体，建议使用更描述性的标题
- 包含代码但未使用代码块，建议用 ``` 包裹代码
- 标签较少，建议添加 2-3 个相关标签便于检索
- 内容为单一段落，建议分段提高可读性

## 🎯 使用场景

### 1. 知识管理
- 追踪知识的演化历史
- 识别高质量知识
- 自动淘汰低质量内容

### 2. 团队协作
- 基于现有知识派生新版本
- 记录知识修改历史
- 通过 GDI 评分筛选优质内容

### 3. 个人学习
- 记录学习轨迹
- 发现知识盲点
- 持续优化知识体系

## 📝 数据库扩展

Trae Memory 2.0 扩展了以下数据库字段：

### memories 表新增列：
- `gdi_score`: GDI 综合评分
- `gdi_intrinsic`: 内在质量评分
- `gdi_usage`: 使用指标评分
- `gdi_social`: 社交信号评分
- `gdi_freshness`: 新鲜度评分
- `parent_id`: 父记忆 ID（继承链）
- `generation`: 代数
- `validation_status`: 验证状态

### 新增表：
- `memory_relations`: 记忆关系表
- `evolution_events`: 进化事件表

## 🔧 集成到现有系统

```python
# 如果使用原有 Trae Memory
from memory_store import MemoryStore
from trae_memory_2 import TraeMemory2

# 创建原有 store
store = MemoryStore()

# 创建 2.0 实例
tm = TraeMemory2()
tm.set_store(store)

# 现在可以使用所有 2.0 功能
```

## 🧪 运行测试

```bash
python test_2.0.py
```

测试内容包括：
- GDI 评分器
- 验证管道
- 知识图谱
- 进化引擎
- 质量报告

## 📚 设计理念

Trae Memory 2.0 受 EvoMap 启发，实现了：

1. **质量导向**: 通过 GDI 评分系统量化记忆质量
2. **自我进化**: 突变 - 验证-选择循环机制
3. **知识图谱**: 追踪记忆间的关系和演化
4. **多维度验证**: 确保记忆质量的 Pipeline

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
