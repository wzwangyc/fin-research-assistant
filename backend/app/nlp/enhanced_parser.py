#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版 PDF 解析器
整合 OpenDataLoader-PDF 的优秀功能：
1. XY-Cut 阅读顺序算法
2. Markdown 输出格式（RAG 友好）
3. 边界框支持
4. 批量处理优化
5. 混合提取模式（本地+AI）
"""

import pdfplumber
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime


@dataclass
class BoundingBox:
    """边界框"""
    x0: float  # 左上角 x
    y0: float  # 左上角 y
    x1: float  # 右下角 x
    y1: float  # 右下角 y
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    def to_dict(self) -> Dict:
        return {
            'x0': self.x0,
            'y0': self.y0,
            'x1': self.x1,
            'y1': self.y1
        }


@dataclass
class Element:
    """文档元素（带边界框）"""
    text: str
    bbox: BoundingBox
    page: int
    element_type: str  # heading/paragraph/table/image/list
    order: int = 0  # 阅读顺序
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'bbox': self.bbox.to_dict(),
            'page': self.page,
            'type': self.element_type,
            'order': self.order
        }


@dataclass
class Page:
    """页面（带元素列表）"""
    page_num: int
    elements: List[Element] = field(default_factory=list)
    width: float = 0
    height: float = 0
    text: str = ""
    tables: List[List[List[str]]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'page_num': self.page_num,
            'width': self.width,
            'height': self.height,
            'elements': [e.to_dict() for e in self.elements],
            'tables': self.tables
        }


class XYCutSorter:
    """XY-Cut 阅读顺序排序器"""
    
    @staticmethod
    def sort(blocks: List[Dict]) -> List[Dict]:
        """
        XY-Cut 算法：按阅读顺序排序
        1. 按 Y 坐标分组（行）
        2. 每行内按 X 坐标排序（从左到右）
        3. 按 Y 坐标排序行（从上到下）
        """
        if not blocks:
            return []
        
        # 1. 按 Y 坐标分组（容差 10 像素）
        tolerance = 10
        rows = []
        current_row = []
        current_y = None
        
        sorted_by_y = sorted(blocks, key=lambda b: b.get('y0', 0))
        
        for block in sorted_by_y:
            y0 = block.get('y0', 0)
            
            if current_y is None or abs(y0 - current_y) > tolerance:
                if current_row:
                    # 按 X 坐标排序当前行
                    current_row.sort(key=lambda b: b.get('x0', 0))
                    rows.append(current_row)
                current_row = [block]
                current_y = y0
            else:
                current_row.append(block)
        
        # 添加最后一行
        if current_row:
            current_row.sort(key=lambda b: b.get('x0', 0))
            rows.append(current_row)
        
        # 2. 展平
        return [block for row in rows for block in row]


class EnhancedPDFParser:
    """增强版 PDF 解析器（整合 OpenDataLoader 功能）"""
    
    def __init__(self, use_xy_cut: bool = True, use_bbox: bool = True):
        self.use_xy_cut = use_xy_cut
        self.use_bbox = use_bbox
        
        # 元素类型分类器
        self.type_keywords = {
            'heading': ['摘要', '引言', '结论', '目录', '图表', '表', 'Figure', 'Table'],
            'list': ['•', '·', '-', '*', '1.', '2.', '①', '②'],
            'table': [],  # 表格单独处理
        }
    
    def parse(self, pdf_path: str) -> List[Page]:
        """解析 PDF，返回带边界框的页面列表"""
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # 创建页面对象
                page_obj = Page(
                    page_num=page_num,
                    width=page.width,
                    height=page.height
                )
                
                # 1. 提取文本块（带边界框）
                blocks = self._extract_blocks(page)
                
                # 2. XY-Cut 排序
                if self.use_xy_cut:
                    blocks = XYCutSorter.sort(blocks)
                
                # 3. 转换为 Element 对象
                for order, block in enumerate(blocks):
                    element = Element(
                        text=block.get('text', ''),
                        bbox=BoundingBox(
                            x0=block.get('x0', 0),
                            y0=block.get('y0', 0),
                            x1=block.get('x1', 0),
                            y1=block.get('y1', 0)
                        ),
                        page=page_num,
                        element_type=self._classify_block(block),
                        order=order
                    )
                    page_obj.elements.append(element)
                
                # 4. 提取表格
                tables = page.extract_tables()
                if tables:
                    page_obj.tables = tables
                
                # 5. 合并全文
                page_obj.text = '\n'.join(b.get('text', '') for b in blocks)
                
                pages.append(page_obj)
        
        return pages
    
    def _extract_blocks(self, page) -> List[Dict]:
        """提取文本块（带坐标）"""
        blocks = []
        
        # 使用 chars 获取更细粒度的文本块
        chars = page.chars
        
        # 按行分组
        lines = {}
        for char in chars:
            y0 = round(char['y0'], 1)  # 四舍五入到 0.1 像素
            if y0 not in lines:
                lines[y0] = []
            lines[y0].append(char)
        
        # 合并每行的字符
        for y0, line_chars in lines.items():
            # 按 x0 排序
            line_chars.sort(key=lambda c: c['x0'])
            
            # 合并相邻字符
            text_parts = []
            current_x1 = None
            
            for char in line_chars:
                if current_x1 is None or char['x0'] > current_x1 + 2:
                    text_parts.append(char['text'])
                else:
                    text_parts[-1] += char['text']
                current_x1 = char['x1']
            
            if text_parts:
                blocks.append({
                    'text': ''.join(text_parts),
                    'x0': line_chars[0]['x0'],
                    'y0': y0,
                    'x1': line_chars[-1]['x1'],
                    'y1': line_chars[0]['top']
                })
        
        return blocks
    
    def _classify_block(self, block: Dict) -> str:
        """分类文本块类型"""
        text = block.get('text', '').strip()
        
        # 检查是否为标题
        for keyword in self.type_keywords['heading']:
            if keyword in text:
                return 'heading'
        
        # 检查是否为列表
        for keyword in self.type_keywords['list']:
            if text.startswith(keyword):
                return 'list'
        
        # 默认段落
        return 'paragraph'
    
    def export_to_markdown(self, pages: List[Page], output_path: str):
        """导出为 Markdown（RAG 友好）"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for page in pages:
                f.write(f"<!-- Page {page.page_num} -->\n\n")
                
                for element in page.elements:
                    if element.element_type == 'heading':
                        f.write(f"## {element.text}\n\n")
                    elif element.element_type == 'list':
                        f.write(f"- {element.text}\n")
                    else:
                        f.write(f"{element.text}\n\n")
                
                # 添加表格
                if page.tables:
                    f.write(f"\n<!-- Tables on page {page.page_num} -->\n\n")
                    for i, table in enumerate(page.tables):
                        f.write(f"### Table {i+1}\n\n")
                        # Markdown 表格格式
                        if table:
                            headers = table[0]
                            f.write("| " + " | ".join(str(h) for h in headers if h) + " |\n")
                            f.write("|" + "|".join("---" for _ in headers if _) + "|\n")
                            for row in table[1:]:
                                f.write("| " + " | ".join(str(c) for c in row if c) + " |\n")
                        f.write("\n")
    
    def export_to_json(self, pages: List[Page], output_path: str):
        """导出为 JSON（带边界框）"""
        data = {
            'total_pages': len(pages),
            'pages': [p.to_dict() for p in pages]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def batch_parse(pdf_files: List[str], output_dir: str, max_workers: int = 4):
    """批量解析（并行处理）"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    parser = EnhancedPDFParser()
    
    def process_single(pdf_path: str):
        try:
            pages = parser.parse(pdf_path)
            
            # 导出
            base_name = Path(pdf_path).stem
            parser.export_to_markdown(pages, str(output_path / f"{base_name}.md"))
            parser.export_to_json(pages, str(output_path / f"{base_name}.json"))
            
            return pdf_path, len(pages), "success"
        except Exception as e:
            return pdf_path, 0, str(e)
    
    # 并行处理
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single, pdf): pdf for pdf in pdf_files}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            pdf_path, page_count, status = result
            print(f"✅ {Path(pdf_path).name}: {page_count}页 - {status}")
    
    return results


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("增强版 PDF 解析器（整合 OpenDataLoader 功能）")
    print("="*70)
    
    parser = EnhancedPDFParser()
    pages = parser.parse('data/raw/test.pdf')
    
    print(f"\n✅ 解析完成")
    print(f"   页数：{len(pages)}")
    print(f"   元素总数：{sum(len(p.elements) for p in pages)}")
    print(f"   表格总数：{sum(len(p.tables) for p in pages)}")
    
    # 导出测试
    parser.export_to_markdown(pages, 'data/processed/test_enhanced.md')
    parser.export_to_json(pages, 'data/processed/test_enhanced.json')
    
    print(f"\n💾 文件已导出:")
    print(f"   - data/processed/test_enhanced.md")
    print(f"   - data/processed/test_enhanced.json")
    
    # 显示第一个元素示例
    if pages and pages[0].elements:
        elem = pages[0].elements[0]
        print(f"\n📋 元素示例:")
        print(f"   类型：{elem.element_type}")
        print(f"   文本：{elem.text[:50]}...")
        print(f"   边界框：({elem.bbox.x0:.1f}, {elem.bbox.y0:.1f}, {elem.bbox.x1:.1f}, {elem.bbox.y1:.1f})")
