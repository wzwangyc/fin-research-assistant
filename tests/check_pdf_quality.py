#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 PDF 文本质量"""
import pdfplumber

pdf_path = 'data/raw/test.pdf'

print("="*70)
print("PDF 文本质量检查")
print("="*70)

with pdfplumber.open(pdf_path) as pdf:
    print(f"\n总页数：{len(pdf.pages)}")
    
    # 检查前 3 页
    for i in range(min(3, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()
        
        print(f"\n{'='*70}")
        print(f"第 {i+1} 页")
        print(f"{'='*70}")
        
        # 检查文本质量
        if text:
            print(f"文本长度：{len(text)} 字符")
            
            # 检测乱码
            has_garbled = any(ord(c) > 127 and c not in ' \n\t，。；："' for c in text[:500])
            print(f"疑似乱码：{'是' if has_garbled else '否'}")
            
            # 检测股票代码格式
            import re
            stock_codes = re.findall(r'[（(](\d{6})[）)]', text)
            print(f"括号内股票代码：{stock_codes}")
            
            # 显示前 500 字
            print(f"\n前 500 字预览:")
            print("-"*70)
            print(text[:500])
            print("-"*70)
        else:
            print("⚠️ 无法提取文本（可能是扫描件）")
