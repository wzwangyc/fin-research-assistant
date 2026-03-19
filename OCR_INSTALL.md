# OCR 安装指南

## 安装步骤

### 1. 安装 Tesseract OCR

**Windows:**
```bash
# 下载安装程序
https://github.com/UB-Mannheim/tesseract/wiki

# 安装时选择中文语言包
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # 多语言支持
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
sudo apt-get install tesseract-ocr-chi-sim  # 中文简体
```

### 2. 安装 Python 库

```bash
pip install pytesseract pdf2image opencv-python
```

**Windows 额外步骤:**
```bash
# 安装 poppler（用于 pdf2image）
# 下载：http://blog.alivate.com.au/poppler-windows/
# 解压后添加到系统 PATH
```

### 3. 验证安装

```python
import pytesseract
from pdf2image import convert_from_path

# 测试 Tesseract
print(pytesseract.get_tesseract_version())

# 测试 PDF 转换
images = convert_from_path('test.pdf', dpi=300)
print(f"成功转换{len(images)}页")
```

### 4. 使用 OCR 解析

```python
from backend.app.nlp.parser_ocr import PDFParserWithOCR

parser = PDFParserWithOCR(use_ocr=True)
result = parser.parse('data/raw/test.pdf')
```

---

## 表格 OCR 增强

对于复杂表格，使用以下配置：

```python
parser = PDFParserWithOCR(
    use_ocr=True,
    ocr_config={
        'dpi': 300,  # 高分辨率
        'lang': 'chi_sim+eng',  # 中英文
        'psm': 6,  # 表格模式
    }
)
```

---

## 性能优化

**批量处理:**
```python
# 只 OCR 前 N 页（测试用）
images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=5)
```

**缓存:**
```python
# 保存 OCR 结果避免重复处理
import pickle
with open('ocr_cache.pkl', 'wb') as f:
    pickle.dump(ocr_text, f)
```

---

## 常见问题

**Q: 识别准确率低？**
A: 提高 DPI 到 300-600，确保 PDF 清晰

**Q: 中文识别错误？**
A: 确保安装了中文语言包 `tesseract-ocr-chi-sim`

**Q: 内存不足？**
A: 分批处理，每次处理 5-10 页
