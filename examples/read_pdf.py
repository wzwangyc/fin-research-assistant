#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""读取 PDF 内容"""
import pdfplumber
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'data/raw/test.pdf'

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"总页数：{len(pdf.pages)}")
        for i, page in enumerate(pdf.pages[:3]):  # 只读前 3 页
            text = page.extract_text()
            if text:
                print(f"\n=== 第 {i+1} 页 ===")
                print(text[:1500])
except Exception as e:
    print(f"错误：{e}")
