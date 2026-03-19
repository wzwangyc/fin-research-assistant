#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报 PDF 解析器（增强版）
支持：文本提取、表格提取、元数据识别
"""

import pdfplumber
import re
from pathlib import Path
from typing import Dict, List, Optional

class PDFParser:
    """增强版 PDF 解析器"""
    
    def __init__(self):
        pass
    
    def parse(self, pdf_path: str) -> Dict:
        """
        解析 PDF 文件
        Returns: {
            'title': str,
            'content': str,
            'page_count': int,
            'tables': List,
            'metadata': Dict
        }
        """
        result = {
            'title': '',
            'content': '',
            'page_count': 0,
            'tables': [],
            'metadata': {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result['page_count'] = len(pdf.pages)
                
                all_text = []
                
                for i, page in enumerate(pdf.pages):
                    # 提取文本
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                        
                        # 第 1 页尝试提取标题
                        if i == 0:
                            result['title'] = self._extract_title(text)
                            result['metadata'] = self._extract_metadata(text)
                    
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        result['tables'].extend(tables)
                
                result['content'] = '\n'.join(all_text)
                
        except Exception as e:
            print(f"[ERROR] PDF 解析失败：{e}")
            result['error'] = str(e)
        
        return result
    
    def _extract_title(self, text: str) -> str:
        """从文本中提取标题"""
        # 尝试匹配常见研报标题格式
        patterns = [
            r'证券研究报告.*?—.*?(.+?)(?:\n|$)',
            r'(深度报告 | 点评报告 | 研究报告).*?\n(.+?)(?:\n|$)',
            r'([^\n]{10,50}研报[^\n]{0,20})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配，返回第一行非空文本
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            return lines[0][:100]
        
        return ''
    
    def _extract_metadata(self, text: str) -> Dict:
        """提取元数据（日期、评级等）"""
        metadata = {}
        
        # 日期
        date_pattern = re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日)')
        date_match = date_pattern.search(text)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # 评级
        rating_pattern = re.compile(r'(买入 | 增持 | 中性 | 减持 | 卖出)')
        rating_match = rating_pattern.search(text)
        if rating_match:
            metadata['rating'] = rating_match.group(1)
        
        # 股票代码
        stock_pattern = re.compile(r'[（(](\d{6})[）)]')
        stock_match = stock_pattern.search(text)
        if stock_match:
            metadata['stock_code'] = stock_match.group(1)
        
        return metadata


if __name__ == '__main__':
    # 测试
    parser = PDFParser()
    result = parser.parse('data/raw/test.pdf')
    
    print(f"标题：{result['title']}")
    print(f"页数：{result['page_count']}")
    print(f"内容长度：{len(result['content'])}")
    print(f"元数据：{result['metadata']}")
    print(f"表格数量：{len(result['tables'])}")
