#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用实际 PDF 文本测试 NER"""
import sys
sys.path.insert(0, '.')

from backend.app.nlp.ner import NERExtractor
import pdfplumber

# 读取实际 PDF 内容
pdf_path = 'data/raw/test.pdf'
with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()

print("="*60)
print("使用实际 PDF 内容测试 NER")
print("="*60)

# 显示前 1000 字
print(f"\n📄 PDF 前 1000 字:\n{text[:1000]}\n")

# 测试 NER
ner = NERExtractor()
result = ner.extract(text)

print("="*60)
print("📊 识别结果:")
print("="*60)
print(f"\n股票代码：{[(c[0], c[1][:50]) for c in result['stock_codes']]}")
print(f"公司名称：{result['companies'][:5]}")
print(f"百分比：{result['percentages'][:5]}")
print(f"日期：{result['dates'][:3]}")
