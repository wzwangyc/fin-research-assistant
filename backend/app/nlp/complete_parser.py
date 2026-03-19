#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报完整解析器
目标：将 PDF 100% 转换为文本 + 表格
- 能直接提取的直接提取
- 不能提取的用 OCR
- 保留原文档结构（页码、标题、段落、表格）
"""

import pdfplumber
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


@dataclass
class PageContent:
    """单页内容"""
    page_num: int
    text: str
    tables: List[List[List[str]]]  # 每页可能有多个表格
    parse_method: str  # 'text' 或 'ocr'


@dataclass
class FullDocument:
    """完整文档"""
    title: str
    total_pages: int
    pages: List[PageContent]
    metadata: Dict
    all_text: str  # 合并后的全文
    all_tables: List[Dict]  # 所有表格


class CompletePDFParser:
    """完整 PDF 解析器"""
    
    def __init__(self, use_ocr: bool = True):
        self.use_ocr = use_ocr and HAS_OCR
        
        if not HAS_OCR and use_ocr:
            print("⚠️ OCR 库未安装，将使用纯文本提取")
            print("   安装：pip install pytesseract pdf2image opencv-python")
    
    def parse(self, pdf_path: str) -> FullDocument:
        """
        完整解析 PDF
        """
        pages_content = []
        all_tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"开始解析 PDF，共{total_pages}页...")
            
            all_text_parts = []
            
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # 进度显示
                if page_num % 5 == 0 or page_num == total_pages:
                    print(f"  已处理 {page_num}/{total_pages} 页")
                
                # 1. 尝试文本提取
                text = page.extract_text()
                parse_method = 'text'
                
                # 2. 文本质量检查
                if not text or len(text) < 50 or self._has_garbled_text(text):
                    if self.use_ocr:
                        # 使用 OCR
                        text = self._ocr_page(page)
                        parse_method = 'ocr'
                        print(f"    第{page_num}页：使用 OCR")
                    else:
                        text = text or ""
                
                # 3. 提取表格
                tables = page.extract_tables()
                if not tables and self.use_ocr:
                    # 尝试 OCR 提取表格
                    tables = self._ocr_tables(page)
                
                # 保存页面内容
                page_content = PageContent(
                    page_num=page_num,
                    text=text,
                    tables=tables if tables else [],
                    parse_method=parse_method
                )
                pages_content.append(page_content)
                
                # 合并文本
                all_text_parts.append(text)
                
                # 保存表格
                if tables:
                    for j, table in enumerate(tables):
                        all_tables.append({
                            'page': page_num,
                            'table_index': j + 1,
                            'data': table,
                            'parse_method': parse_method
                        })
            
            # 合并全文
            all_text = '\n\n'.join(all_text_parts)
            
            # 提取元数据（从第 1 页）
            metadata = {}
            if pages_content:
                first_page_text = pages_content[0].text
                metadata = self._extract_metadata(first_page_text)
            
            return FullDocument(
                title=metadata.get('title', '未命名'),
                total_pages=total_pages,
                pages=pages_content,
                metadata=metadata,
                all_text=all_text,
                all_tables=all_tables
            )
    
    def _has_garbled_text(self, text: str) -> bool:
        """检查是否有乱码"""
        if not text:
            return True
        
        # 检测乱码模式（字母数字混合）
        garbled_pattern = re.compile(r'[a-zA-Z]\d+[a-zA-Z]')
        matches = garbled_pattern.findall(text[:500])
        
        return len(matches) > 5
    
    def _ocr_page(self, page) -> str:
        """OCR 识别单页"""
        if not HAS_OCR:
            return ""
        
        try:
            images = convert_from_path(
                page.doc.stream,
                dpi=300,
                first_page=page.page_number,
                last_page=page.page_number
            )
            
            if images:
                img = images[0]
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                return text
        except Exception as e:
            print(f"    OCR 失败：{e}")
        
        return ""
    
    def _ocr_tables(self, page) -> List:
        """OCR 提取表格"""
        # 简化版本：返回空列表
        # 完整实现需要检测表格区域并 OCR
        return []
    
    def _extract_metadata(self, text: str) -> Dict:
        """提取元数据"""
        metadata = {}
        
        # 标题
        title_patterns = [
            r'证券研究报告.*?—.*?(.+?)(?:\n|$)',
            r'(深度报告 | 点评报告).*?\n(.+?)(?:\n|$)',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                metadata['title'] = match.group(1).strip()
                break
        
        # 日期
        date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # 评级
        rating_match = re.search(r'(买入 | 增持 | 中性 | 减持 | 卖出)', text)
        if rating_match:
            metadata['rating'] = rating_match.group(1)
        
        # 公司
        companies = ['北方稀土', '包钢股份', '中国稀土', '盛和资源']
        for company in companies:
            if company in text:
                metadata['company'] = company
                break
        
        return metadata
    
    def save_to_files(self, doc: FullDocument, output_dir: str):
        """
        保存解析结果到文件
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 保存全文文本
        text_file = os.path.join(output_dir, 'full_text.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"# {doc.title}\n\n")
            f.write(f"总页数：{doc.total_pages}\n")
            f.write(f"元数据：{doc.metadata}\n\n")
            f.write("="*70 + "\n\n")
            
            for page in doc.pages:
                f.write(f"【第{page.page_num}页】\n")
                f.write(f"解析方式：{page.parse_method}\n\n")
                f.write(page.text)
                f.write("\n\n" + "="*70 + "\n\n")
        
        print(f"✅ 全文文本已保存：{text_file}")
        
        # 2. 保存所有表格
        tables_file = os.path.join(output_dir, 'all_tables.json')
        tables_data = []
        for table in doc.all_tables:
            tables_data.append({
                'page': table['page'],
                'table_index': table['table_index'],
                'headers': table['data'][0] if table['data'] else [],
                'rows': table['data'][1:] if len(table['data']) > 1 else [],
                'parse_method': table['parse_method']
            })
        
        with open(tables_file, 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 表格数据已保存：{tables_file}")
        
        # 3. 保存结构化数据
        struct_file = os.path.join(output_dir, 'structured_data.json')
        with open(struct_file, 'w', encoding='utf-8') as f:
            json.dump({
                'title': doc.title,
                'total_pages': doc.total_pages,
                'metadata': doc.metadata,
                'table_count': len(doc.all_tables),
                'text_length': len(doc.all_text)
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结构化数据已保存：{struct_file}")
        
        # 返回输出目录
        return output_dir


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("金融研报完整解析器")
    print("="*70)
    
    parser = CompletePDFParser(use_ocr=False)  # 暂时不用 OCR
    doc = parser.parse('data/raw/test.pdf')
    
    print("\n" + "="*70)
    print("解析结果")
    print("="*70)
    print(f"标题：{doc.title}")
    print(f"总页数：{doc.total_pages}")
    print(f"全文长度：{len(doc.all_text)} 字符")
    print(f"表格数量：{len(doc.all_tables)} 个")
    print(f"元数据：{doc.metadata}")
    
    # 统计解析方式
    text_pages = sum(1 for p in doc.pages if p.parse_method == 'text')
    ocr_pages = sum(1 for p in doc.pages if p.parse_method == 'ocr')
    print(f"\n解析方式统计:")
    print(f"  文本提取：{text_pages} 页")
    print(f"  OCR 识别：{ocr_pages} 页")
    
    # 保存文件
    output_dir = 'data/processed/test_pdf'
    parser.save_to_files(doc, output_dir)
    
    print("\n" + "="*70)
    print("✅ 解析完成！")
    print("="*70)
