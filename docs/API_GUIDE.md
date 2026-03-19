# API 使用指南

## 快速开始

### 1. 基础使用 - PDF 解析

```python
from backend.app.nlp.complete_parser import CompletePDFParser

# 创建解析器
parser = CompletePDFParser(use_ocr=False)

# 解析 PDF
doc = parser.parse('data/raw/report.pdf')

# 查看结果
print(f"页数：{doc.total_pages}")
print(f"文本长度：{len(doc.all_text)}")
print(f"表格数量：{len(doc.all_tables)}")

# 保存文件
parser.save_to_files(doc, 'data/processed/output')
```

### 2. 反幻觉检查

```python
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker

checker = AntiHallucinationChecker()
entities = checker.extract_with_evidence(text, page=1)
report = checker.generate_report(entities)

print(f"总实体数：{report['total_entities']}")
print(f"高置信度：{report['high_confidence']}")
print(f"幻觉风险：{report['hallucination_risk']}")
```

### 3. 智能问答

```python
from backend.app.llm.chatbot import ResearchChatBot

bot = ResearchChatBot()
bot.load_document(pdf_text)

result = bot.chat("北方稀土的估值是多少？")
print(f"回答：{result['answer']}")
print(f"置信度：{result['confidence']}")
print(f"来源：{result['sources']}")
```

---

## 高级用法

### 批量处理 PDF

```python
from pathlib import Path
from backend.app.nlp.complete_parser import CompletePDFParser

parser = CompletePDFParser()
pdf_files = list(Path('data/raw').glob('*.pdf'))

for pdf_file in pdf_files:
    doc = parser.parse(str(pdf_file))
    parser.save_to_files(doc, f'data/processed/{pdf_file.stem}')
```

### 自定义 RAG 检索

```python
from backend.app.llm.rag import RAGEngine

engine = RAGEngine(embedding_model='paraphrase-multilingual-MiniLM-L12-v2')
engine.load_document(text)

# 语义搜索
results = engine.search("估值目标价", top_k=5)

for result in results:
    print(f"第{result.chunk.page}页：{result.chunk.text[:100]}")
    print(f"相似度：{result.score:.3f}")
```

### 多轮对话

```python
from backend.app.llm.chatbot import ResearchChatBot

bot = ResearchChatBot()
bot.load_document(pdf_text)

# 第一轮
result1 = bot.chat("公司的股票代码？")
print(result1['answer'])

# 第二轮（保留上下文）
result2 = bot.chat("估值是多少？")
print(result2['answer'])

# 导出对话
bot.export_conversation('conversation.json')
```

---

## 配置选项

### PDF 解析配置

```python
parser = CompletePDFParser(
    use_ocr=False,        # 是否启用 OCR
    use_table_ocr=False   # 是否使用表格 OCR
)
```

### RAG 配置

```python
engine = RAGEngine(
    embedding_model='paraphrase-multilingual-MiniLM-L12-v2',
    page_size=500  # 文本块大小
)
```

### 问答配置

```python
bot = ResearchChatBot()
bot.max_history = 10  # 保留对话轮数
```

---

## 错误处理

```python
from backend.app.nlp.complete_parser import CompletePDFParser

parser = CompletePDFParser()

try:
    doc = parser.parse('report.pdf')
except FileNotFoundError:
    print("文件不存在")
except Exception as e:
    print(f"解析失败：{e}")
```

---

## 性能优化

### 1. 使用缓存

```python
import pickle

# 保存
with open('cache.pkl', 'wb') as f:
    pickle.dump(doc, f)

# 加载
with open('cache.pkl', 'rb') as f:
    doc = pickle.load(f)
```

### 2. 分批处理

```python
# 大文件分批处理
for i in range(0, len(pdf_files), 10):
    batch = pdf_files[i:i+10]
    for pdf in batch:
        process(pdf)
```

### 3. 禁用不必要的功能

```python
# 仅需要文本提取
parser = CompletePDFParser(use_ocr=False)

# 不需要表格
doc = parser.parse(pdf)
# 忽略 doc.all_tables
```

---

## 最佳实践

### 1. 文件组织

```
project/
├── data/
│   ├── raw/           # 原始 PDF
│   └── processed/     # 处理结果
├── cache/             # 缓存文件
└── output/            # 最终输出
```

### 2. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    doc = parser.parse(pdf)
    logger.info(f"解析成功：{doc.total_pages}页")
except Exception as e:
    logger.error(f"解析失败：{e}")
```

### 3. 异常处理

```python
def safe_parse(pdf_path):
    try:
        parser = CompletePDFParser()
        return parser.parse(pdf_path)
    except Exception as e:
        print(f"解析失败：{e}")
        return None
```

---

## 常见问题

### Q: 如何提取特定页的内容？

A: 使用分块信息：
```python
for page in doc.pages:
    if page.page_num == 5:
        print(page.text)
```

### Q: 如何提高实体识别准确率？

A: 添加自定义词典：
```python
checker = AntiHallucinationChecker()
checker.known_companies['新公司'] = '600XXX'
```

### Q: 如何处理大文件？

A: 使用流式处理：
```python
parser = CompletePDFParser()
with open(pdf_path, 'rb') as f:
    for page in parser.parse_stream(f):
        process(page)
```

---

## 完整示例

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""金融研报解析完整示例"""

from backend.app.nlp.complete_parser import CompletePDFParser
from backend.app.nlp.anti_hallucination import AntiHallucinationChecker
from backend.app.llm.chatbot import ResearchChatBot

def main():
    # 1. 解析 PDF
    parser = CompletePDFParser()
    doc = parser.parse('report.pdf')
    parser.save_to_files(doc, 'output/')
    
    # 2. 反幻觉检查
    checker = AntiHallucinationChecker()
    entities = checker.extract_with_evidence(doc.all_text)
    report = checker.generate_report(entities)
    print(f"幻觉风险：{report['hallucination_risk']}")
    
    # 3. 智能问答
    bot = ResearchChatBot()
    bot.load_document(doc.all_text)
    
    questions = [
        "股票代码是多少？",
        "评级是什么？",
        "估值是多少？"
    ]
    
    for q in questions:
        result = bot.chat(q)
        print(f"问：{q}")
        print(f"答：{result['answer']}")
    
    # 4. 导出结果
    bot.export_conversation('output/conversation.json')

if __name__ == '__main__':
    main()
```
