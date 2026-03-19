#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF OCR 解析模块（处理扫描件和复杂表格）
使用 pytesseract 进行 OCR 识别
"""

import pdfplumber
import re
from typing import Dict, List, Optional

try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️ 未安装 OCR 库，如需 OCR 支持请运行：pip install pytesseract pdf2image")


class PDFParserWithOCR:
    """支持 OCR 的 PDF 解析器"""
    
    def __init__(self, use_ocr: bool = False):
        self.use_ocr = use_ocr and HAS_OCR
        
        # 已知公司词典（用于校正）
        self.known_companies = {
            '北方稀土': '600111',
            '包钢股份': '600010',
            '包钢集团': '600010',
        }
    
    def parse(self, pdf_path: str) -> Dict:
        """
        解析 PDF（优先文本提取，失败则使用 OCR）
        """
        result = {
            'title': '',
            'content': '',
            'page_count': 0,
            'tables': [],
            'metadata': {},
            'parse_method': 'text'  # text 或 ocr
        }
        
        # 1. 尝试普通文本提取
        with pdfplumber.open(pdf_path) as pdf:
            result['page_count'] = len(pdf.pages)
            all_text = []
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                
                # 检查文本质量
                if text and self._is_text_valid(text):
                    all_text.append(text)
                    
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        result['tables'].extend(tables)
                        # 表格也转换为文本
                        table_text = self._table_to_text(tables)
                        if table_text:
                            all_text.append(table_text)
                    
                    # 第 1 页提取元数据
                    if i == 0:
                        result['title'] = self._extract_title(text)
                        result['metadata'] = self._extract_metadata(text)
                else:
                    # 文本质量差，标记需要 OCR
                    result['parse_method'] = 'mixed'
                    print(f"⚠️ 第{i+1}页文本质量差，建议 OCR")
            
            result['content'] = '\n'.join(all_text)
        
        # 2. 如果文本质量太差，使用 OCR
        if self.use_ocr and HAS_OCR:
            ocr_text = self._ocr_pdf(pdf_path)
            if ocr_text and len(ocr_text) > len(result['content']):
                result['content'] = ocr_text
                result['parse_method'] = 'ocr'
                print("✅ 已切换到 OCR 模式")
        
        # 3. 后处理：校正乱码
        result['content'] = self._post_process(result['content'])
        
        return result
    
    def _is_text_valid(self, text: str) -> bool:
        """检查文本质量"""
        if len(text) < 50:
            return False
        
        # 检查是否有太多乱码字符
        garbled_pattern = re.compile(r'[a-zA-Z]\d+[a-zA-Z]')
        garbled_matches = garbled_pattern.findall(text)
        
        if len(garbled_matches) > 10:
            return False
        
        return True
    
    def _table_to_text(self, tables: List) -> str:
        """将表格转换为文本"""
        text_parts = []
        for table in tables:
            for row in table:
                if row:
                    row_text = ' | '.join(str(cell) for cell in row if cell)
                    if row_text.strip():
                        text_parts.append(row_text)
        return '\n'.join(text_parts)
    
    def _ocr_pdf(self, pdf_path: str) -> str:
        """OCR 识别 PDF"""
        if not HAS_OCR:
            return ""
        
        print("🔄 开始 OCR 识别...")
        all_text = []
        
        try:
            # 转换 PDF 为图片
            images = convert_from_path(pdf_path, dpi=300)
            
            for i, image in enumerate(images[:5]):  # 只 OCR 前 5 页（测试用）
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                if text.strip():
                    all_text.append(f"--- 第{i+1}页 ---\n{text}")
            
            print(f"✅ OCR 完成，识别{len(all_text)}页")
            return '\n'.join(all_text)
        
        except Exception as e:
            print(f"❌ OCR 失败：{e}")
            return ""
    
    def _post_process(self, text: str) -> str:
        """后处理：校正乱码"""
        # 校正已知乱码模式
        if '[北 Tab 方 le_稀 Sto 土 ckIn(f6o]0 0111)' in text:
            text = text.replace('[北 Tab 方 le_稀 Sto 土 ckIn(f6o]0 0111)', '北方稀土 (600111)')
        
        if '[一 Ta 年 b 该 le 股_B 与 a 上 base 证 In 综 fo 指]' in text:
            text = text.replace('[一 Ta 年 b 该 le 股_B 与 a 上 base 证 In 综 fo 指]', '本年该股与上证综指')
        
        # 校正股票代码格式
        text = re.sub(r'[（(](\d)\s*(\d{5})[）)]', r'(\1\2)', text)
        
        return text
    
    def _extract_title(self, text: str) -> str:
        """提取标题"""
        patterns = [
            r'证券研究报告.*?—.*?(.+?)(?:\n|$)',
            r'(深度报告 | 点评报告).*?\n(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_metadata(self, text: str) -> Dict:
        """提取元数据"""
        metadata = {}
        
        # 日期
        date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # 评级
        rating_match = re.search(r'(买入 | 增持 | 中性 | 减持 | 卖出)', text)
        if rating_match:
            metadata['rating'] = rating_match.group(1)
        
        # 尝试从上下文中提取股票代码
        if '北方稀土' in text:
            metadata['company'] = '北方稀土'
            metadata['stock_code'] = '600111'
        
        return metadata


if __name__ == '__main__':
    # 测试
    parser = PDFParserWithOCR(use_ocr=False)  # 先不用 OCR
    result = parser.parse('data/raw/test.pdf')
    
    print("="*70)
    print("PDF 解析结果（增强版）")
    print("="*70)
    print(f"解析方式：{result['parse_method']}")
    print(f"标题：{result['title']}")
    print(f"页数：{result['page_count']}")
    print(f"内容长度：{len(result['content'])}")
    print(f"表格数量：{len(result['tables'])}")
    print(f"元数据：{result['metadata']}")
