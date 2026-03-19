# 核心功能文档

## 功能架构

```
金融研报助手
├── PDF 完整解析模块
├── 反幻觉核心模块
├── 金融实体识别模块
├── RAG 检索增强模块
├── 智能问答模块
└── Streamlit 界面模块
```

---

## 模块一：PDF 完整解析

### 功能说明

将金融研报 PDF 100% 转换为结构化文本和表格数据，支持扫描件 OCR 识别。

### 核心类

- `CompletePDFParser` - 完整 PDF 解析器
- `PDFParserWithOCR` - 支持 OCR 的解析器
- `TableOCRExtractor` - 表格 OCR 提取器

### 主要方法

```python
class CompletePDFParser:
    def parse(pdf_path: str) -> FullDocument:
        """解析 PDF 文件"""
        
    def save_to_files(doc: FullDocument, output_dir: str):
        """保存解析结果到文件"""
```

### 输出文件

| 文件 | 格式 | 说明 |
|------|------|------|
| full_text.txt | TXT | 完整文本（带页码） |
| all_tables.json | JSON | 所有表格数据 |
| structured_data.json | JSON | 文档元数据 |

### 使用示例

```python
from backend.app.nlp.complete_parser import CompletePDFParser

parser = CompletePDFParser(use_ocr=False)
doc = parser.parse('report.pdf')
parser.save_to_files(doc, 'output/')
```

---

## 模块二：反幻觉核心

### 功能说明

提供引用溯源、置信度评分、交叉验证等反幻觉机制，确保信息准确性。

### 核心类

- `AntiHallucinationChecker` - 反幻觉检查器
- `ConfidenceLevel` - 置信度等级枚举
- `Evidence` - 证据数据结构
- `ExtractedEntity` - 提取的实体

### 置信度等级

| 等级 | 说明 | 置信度 |
|------|------|--------|
| HIGH | 90%+ 确定 | ✅ |
| MEDIUM | 70-90% 确定 | ⚠️ |
| LOW | 50-70% 确定 | ❌ |
| UNKNOWN | 低于 50% | 🔄 |

### 幻觉风险评估

| 等级 | 说明 | 处理建议 |
|------|------|----------|
| LOW | 无低置信度信息 | 可以安全使用 |
| MEDIUM | 1-2 个低置信度 | 部分需要复核 |
| HIGH | 3 个以上低置信度 | 建议人工审核 |

### 使用示例

```python
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker

checker = AntiHallucinationChecker()
entities = checker.extract_with_evidence(text, page=1)
report = checker.generate_report(entities)

print(f"幻觉风险：{report['hallucination_risk']}")
```

---

## 模块三：金融实体识别

### 功能说明

识别金融研报中的关键实体，包括公司、股票代码、财务指标等。

### 核心类

- `NERExtractor` - 实体识别提取器

### 识别的实体类型

| 类型 | 说明 | 验证规则 |
|------|------|----------|
| 公司名称 | 北方稀土、包钢股份等 | 金融词典匹配 |
| 股票代码 | 600111、600010 等 | 6 位数字 + 前缀验证 |
| 金额 | 营收、利润、估值 | 数字 + 单位（亿/万/元） |
| 百分比 | 增长率、占比 | 数字+% |
| 日期 | 报告日期、财务年度 | YYYY 年 MM 月 DD 日 |
| 分析师 | 姓名、邮箱、电话 | 正则匹配 |

### 使用示例

```python
from backend.app.nlp.ner import NERExtractor

ner = NERExtractor()
entities = ner.extract(text)

print(f"股票代码：{entities['stock_codes']}")
print(f"公司名称：{entities['companies']}")
```

---

## 模块四：RAG 检索增强

### 功能说明

基于向量检索和关键词搜索的混合检索引擎，支持语义搜索。

### 核心类

- `RAGEngine` - RAG 检索引擎
- `Chunk` - 文本块数据结构
- `SearchResult` - 搜索结果

### 检索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 向量检索 | SentenceTransformer 语义搜索 | 语义理解 |
| 关键词搜索 | 传统关键词匹配 | 精确匹配 |
| 混合搜索 | 向量 + 关键词加权 | 最佳效果 |

### 使用示例

```python
from backend.app.llm.rag import RAGEngine

engine = RAGEngine()
engine.load_document(text)

results = engine.search("北方稀土的估值", top_k=5)
```

---

## 模块五：智能问答

### 功能说明

基于 RAG 的多轮对话问答系统，支持意图识别和推荐追问。

### 核心类

- `ChatBot` - 基础问答机器人
- `ResearchChatBot` - 研报专用机器人
- `Message` - 对话消息

### 意图类型

| 意图 | 说明 | 示例问题 |
|------|------|----------|
| valuation | 估值类 | "目标价是多少？" |
| rating | 评级类 | "什么评级？" |
| financial | 财务类 | "营收增长多少？" |
| business | 业务类 | "主要产品有哪些？" |
| general | 通用类 | "公司怎么样？" |

### 使用示例

```python
from backend.app.llm.chatbot import ResearchChatBot

bot = ResearchChatBot()
bot.load_document(pdf_text)

result = bot.chat("北方稀土的估值是多少？")
print(result['answer'])
print(result['follow_up'])  # 推荐追问
```

---

## 模块六：Streamlit 界面

### 功能说明

基于 Streamlit 的 Web 界面，提供 PDF 上传、智能问答、引用显示等功能。

### 启动方式

```bash
streamlit run frontend/streamlit_app.py
```

### 界面功能

| 功能 | 说明 |
|------|------|
| PDF 上传 | 拖拽上传，自动解析 |
| 智能问答 | 对话式界面 |
| 引用显示 | 可折叠面板 |
| 对话管理 | 清空、导出 |

---

## API 参考

### 完整流程 API

```python
# 1. 解析 PDF
from backend.app.nlp.complete_parser import CompletePDFParser
parser = CompletePDFParser()
doc = parser.parse('report.pdf')

# 2. 反幻觉检查
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker
checker = AntiHallucinationChecker()
entities = checker.extract_with_evidence(doc.all_text)

# 3. 智能问答
from backend.app.llm.chatbot import ResearchChatBot
bot = ResearchChatBot()
bot.load_document(doc.all_text)
answer = bot.chat("问题？")
```

---

## 性能优化建议

1. **批量处理** - 多个 PDF 分批处理，避免内存溢出
2. **缓存机制** - 对已解析的 PDF 缓存结果
3. **OCR 可选** - 仅在需要时启用 OCR
4. **embedding 模型** - 使用轻量级模型提高速度

---

## 常见问题

### Q: 如何处理扫描版 PDF？

A: 启用 OCR 支持：
```bash
pip install pytesseract pdf2image opencv-python
```
```python
parser = CompletePDFParser(use_ocr=True)
```

### Q: 如何提高检索准确率？

A: 调整 RAG 参数：
```python
engine = RAGEngine(embedding_model='paraphrase-multilingual-MiniLM-L12-v2')
results = engine.search(query, top_k=10)  # 增加返回数量
```

### Q: 如何自定义实体识别？

A: 在 `NERExtractor` 中添加规则：
```python
self.known_companies['新公司'] = '股票代码'
```
