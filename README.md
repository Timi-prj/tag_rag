# Tag RAG - Markdown 解析与结构化处理工具

<!-- LLM可提取的结构化信息 -->
<项目元数据>
- 类型: Markdown解析工具
- 阶段: RAG流水线模块一
- 状态: 核心功能完成，测试优化中
- 主要组件: RowParserNode, TagExtractorNode, ScopeBuilderNode
- 关键技术: 标题切块、保护元素识别、种子标签转换
- 输出格式: JSON结构化块
- 语言: Python 3.8+
- 版本: 1.0.0
- 最后更新: 2025-12-27
</项目元数据>

## 🚀 快速概览

**项目状态**: 开发中 | **版本**: 1.0.0 | **最后更新**: 2025-12-27

### 已完成 ✅
- ✅ Markdown解析与标题驱动切块
- ✅ 保护元素（代码块、表格）完整性保持
- ✅ 种子标签转换 (#?xxx → #seed/xxx)
- ✅ 多线程批量处理
- ✅ 可变参数API接口
- ✅ 文件后缀白名单过滤
- ✅ 编码自动检测（UTF-8、GBK、UTF-16等）

### 进行中 🔄
- 🔄 测试覆盖完善
- 🔄 性能优化

### 待开发 📋
- 📋 向量存储模块集成
- 📋 更多Markdown元素支持

## 🎯 设计意图

### 核心目标
作为RAG（检索增强生成）流水线的**模块一**，专注于将非结构化Markdown转换为结构化文本块，为后续向量化和检索提供高质量输入。

### 关键设计决策
1. **保护元素优先**: 代码块（```）和表格（|）保持完整，确保技术文档的准确性
2. **标题驱动切块**: 尊重文档的语义结构，切块边界与标题对齐（H1~H6）
3. **种子标签系统**: 通过`#?`前缀标记重要概念（如`#?project/tag_rag`），转换为`#seed/project/tag_rag`便于后续重点处理
4. **模块化流水线**: 行解析→标签提取→作用域构建的清晰分离，便于维护和扩展
5. **多线程批量处理**: 支持并发处理多个文件，提高处理效率

## ✨ 核心功能

### 📄 智能解析
- **标题驱动切块**: 自动按H1~H6标题进行文档切分
- **保护元素识别**: 完整保持代码块和表格的完整性
- **超长处理**: 超过配置字符数时自动切分，标记切分状态

### 🏷️ 标签处理
- **标签提取**: 自动提取`#tag/value`格式标签
- **种子标签转换**: `#?xxx/yyy` → `#seed/xxx/yyy`
- **标签过滤**: 支持正则表达式排除特定标签

### 🔧 工程特性
- **多线程批量处理**: 支持并发处理多个文件
- **可变参数接口**: 灵活的API设计
- **文件后缀过滤**: 可配置的文件类型白名单
- **编码自动检测**: 支持多种编码格式

## 🚦 快速开始

### 环境要求
- Python 3.8+
- Docker（可选）

### 1分钟体验
```bash
# 克隆项目（假设已克隆）
cd tag_rag

# 安装依赖
pip install -r requirements.txt

# 处理示例文件
python src/main.py data/test_seed_tags.md --no-vectorize

# 查看结果
cat output/parsed_result.json
```

### 基本配置
编辑 `config.yaml`：
```yaml
parser:
  input_dir: "./data"
  output_dir: "./output"
  file_extensions: [".md", ".markdown"]
  chunk_strategy:
    max_chars: 1000
    overlap_rows: 2
```

## 📈 项目进度跟踪

### 🟢 近期完成（最近更新）
- [x] **多线程批量处理** - 支持并发处理多个文件
- [x] **种子标签转换** - `#?xxx/yyy` → `#seed/xxx/yyy`
- [x] **文件后缀白名单** - 可配置的文件类型过滤
- [x] **编码自动检测** - 支持UTF-8、GBK、UTF-16等
- [x] **可变参数API** - 灵活的接口设计

### 🟡 当前重点（1-2周）
- [ ] **性能基准测试** - 建立性能基准，优化处理速度
- [ ] **测试覆盖率提升** - 目标覆盖率达到80%+
- [ ] **错误处理完善** - 更健壮的错误恢复机制

### 🔵 中期规划（1个月）
- [ ] **向量存储模块集成** - 连接向量数据库（OpenAI、Milvus等）
- [ ] **超长表格优化切分** - 改进表格的特殊切分策略
- [ ] **Web API接口** - 提供HTTP服务接口
- [ ] **更多Markdown元素支持** - 引用块、列表等

### 🟣 长期愿景
- [ ] **多格式文档支持** - PDF、HTML等格式的文本提取
- [ ] **图形化配置界面** - 可视化配置和管理
- [ ] **预训练模型集成** - 自动识别文档结构
- [ ] **云服务部署** - 提供SaaS服务

### 🔴 代码优化TODO

基于代码审查，发现以下冗余逻辑和无效代码，将按顺序优化：

- [x] **移除占位模式代码** - 删除connector.py中的无效占位模式，失败时直接报错
- [x] **统一令牌估算函数** - 合并RateLimiter和EmbeddingNode中的重复_estimate_tokens方法
- [x] **替换print为logger** - 将embedding.py中的print语句替换为项目logger（其他文件待后续优化）
- [x] **移除冗余单块处理方法** - 删除pipeline.py中的process_single方法
- [x] **优化配置一致性** - 更新config manager默认值以匹配实际配置
- [ ] **清理未使用的导入** - 检查并删除所有未使用的导入语句
- [x] **优化错误信息** - 根据配置优先级调整embedding.py中的错误提示

每个优化点将单独提交，确保代码质量。

## 🏗️ 架构设计

### 模块化流水线
```
Markdown 文件
     ↓
RowParserNode（行解析）
     ↓  
TagExtractorNode（标签提取）
     ↓
ScopeBuilderNode（作用域构建）
     ↓
ParsedBlock 列表
```

### 核心组件
1. **RowParserNode**: 单行文本解析，识别标题、标签、代码块、表格行
2. **TagExtractorNode**: 标签提取与清洗，实现种子标签转换
3. **ScopeBuilderNode**: 上下文作用域管理，实现保护元素优先切块策略
4. **ParsingContext**: 解析状态机，维护标题栈、标签作用域等状态

### 数据流
```python
# 简单示例
pipeline = MarkdownParserPipeline()
blocks = pipeline.run("document.md")
# 输出: List[ParsedBlock] - 包含内容、标签、行号、切分状态等
```

## 📊 输出格式示例

```json
{
  "block_id": "d8bcbcc94ee359639c9745e3e1a363b4",
  "content": "# Test with Seed Tags\\n\\nSome content here...",
  "start_line": 1,
  "end_line": 9,
  "tags": [
    {
      "key": "seed",
      "value": "city/beijing",
      "original_text": "#seed/city/beijing"
    },
    {
      "key": "topic", 
      "value": "python",
      "original_text": "#topic/python"
    }
  ],
  "is_splited": false,
  "protected_element_type": null,
  "protected_element_overlength": false
}
```

## 🔍 详细使用指南

### 命令行方式
```bash
# 处理单个文件
python src/main.py document.md

# 处理多个文件
python src/main.py file1.md file2.md file3.md

# 处理整个目录
python src/main.py --dir /path/to/files

# 不保存JSON输出
python src/main.py --no-json

# 不进行向量化
python src/main.py --no-vectorize
```

### Python API方式
```python
from src.modules.md_parser.pipeline import MarkdownParserPipeline

# 创建管道
pipeline = MarkdownParserPipeline()

# 处理单个文件
blocks = pipeline.run("document.md")

# 批量处理（多线程）
blocks = pipeline.process_files("file1.md", "file2.md", "file3.md")

# 处理目录
blocks = pipeline.process_directory("/path/to/documents")
```

### Docker方式
```bash
# 启动服务
docker-compose up -d

# 执行解析
docker-compose exec parser python src/main.py document.md
```

## ⚙️ 配置详解

### 解析器配置
```yaml
parser:
  input_dir: "./data"           # 默认输入目录
  output_dir: "./output"        # 输出目录
  file_extensions: [".md", ".markdown"]  # 处理的文件类型
  chunk_strategy:
    max_chars: 1000             # 每个块的最大字符数
    overlap_rows: 2             # 切分时的重叠行数（避免语义断裂）
```

### 标签配置
```yaml
tags:
  prefix: "?"                   # 种子标签前缀
  exclude_regex:                # 排除的标签模式
    - "^#ignore/.*"             # 忽略所有#ignore/开头的标签
    - "^#temp$"                 # 忽略#temp标签
```

## 🤝 贡献指南

### 开发环境
```bash
# 设置开发环境
git clone <repository>
cd tag_rag
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install black flake8 mypy pytest  # 开发工具
```

### 代码规范
- **格式化**: Black
- **代码检查**: Flake8  
- **类型检查**: mypy
- **测试**: pytest

### 提交规范
- 遵循Conventional Commits规范
- 每个功能/修复应有对应测试
- 重大更改需更新文档

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 📞 联系与支持

- **问题报告**: GitHub Issues
- **功能请求**: Issues标签`enhancement`
- **贡献代码**: Pull Requests
- **文档改进**: 直接编辑README

---

*文档设计目标：让LLM和人类用户都能在10分钟内了解项目全貌、设计意图和当前进度*  
*最后更新: 2025-12-27 | 版本: 1.0.0*
