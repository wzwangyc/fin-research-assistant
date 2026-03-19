#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报 OCR 解析器（表格增强版）
专门针对金融研报的复杂表格进行优化
"""

import pdfplumber
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
    HAS_CV = True
    import cv2
    import numpy as np
except ImportError:
    HAS_OCR = False
    HAS_CV = False


@dataclass
class TableData:
    """表格数据结构"""
    page: int
    headers: List[str]
    rows: List[List[str]]
    caption: str = ""  # 表格标题
    source: str = ""   # 数据来源


class TableOCRExtractor:
    """表格 OCR 提取器"""
    
    def __init__(self):
        self.tesseract_config = {
            'lang': 'chi_sim+eng',
            'psm': 6,  # 表格模式
            'oem': 3,  # LSTM OCR 引擎
        }
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[TableData]:
        """
        从 PDF 提取表格（优先使用 pdfplumber，失败则用 OCR）
        """
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # 1. 尝试 pdfplumber 提取
                pdf_tables = page.extract_tables()
                
                if pdf_tables:
                    for table in pdf_tables:
                        table_data = self._process_table(table, i+1)
                        if table_data:
                            tables.append(table_data)
                else:
                    # 2. pdfplumber 失败，使用 OCR
                    if HAS_OCR:
                        ocr_tables = self._ocr_page_tables(page)
                        tables.extend(ocr_tables)
        
        return tables
    
    def _process_table(self, table: List, page: int) -> Optional[TableData]:
        """处理表格数据"""
        if not table or len(table) < 2:
            return None
        
        # 清理数据
        cleaned_rows = []
        for row in table:
            if row:
                cleaned_row = [str(cell).strip() if cell else '' for cell in row]
                if any(cleaned_row):  # 至少有一个非空单元格
                    cleaned_rows.append(cleaned_row)
        
        if len(cleaned_rows) < 2:
            return None
        
        # 假设第一行是表头
        headers = cleaned_rows[0]
        data_rows = cleaned_rows[1:]
        
        return TableData(
            page=page,
            headers=headers,
            rows=data_rows,
            caption="",
            source=""
        )
    
    def _ocr_page_tables(self, page) -> List[TableData]:
        """使用 OCR 提取页面中的表格"""
        if not HAS_OCR:
            return []
        
        tables = []
        
        try:
            # 获取页面图像
            images = convert_from_path(
                page.doc.stream,
                dpi=300,
                first_page=page.page_number,
                last_page=page.page_number
            )
            
            if images:
                img = np.array(images[0])
                
                # 检测表格区域
                table_regions = self._detect_table_regions(img)
                
                for region in table_regions:
                    # OCR 识别表格
                    table_img = img[region[1]:region[3], region[0]:region[2]]
                    table_text = pytesseract.image_to_string(
                        table_img,
                        lang=self.tesseract_config['lang'],
                        config=f'--psm {self.tesseract_config["psm"]}'
                    )
                    
                    if table_text.strip():
                        # 解析 OCR 文本为表格
                        table_data = self._parse_ocr_table(table_text, page.page_number)
                        if table_data:
                            tables.append(table_data)
        
        except Exception as e:
            print(f"OCR 表格提取失败：{e}")
        
        return tables
    
    def _detect_table_regions(self, img) -> List[Tuple[int, int, int, int]]:
        """检测图像中的表格区域"""
        if not HAS_CV:
            return []
        
        regions = []
        
        # 转换为灰度图
        import numpy as np
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 过滤太小的区域
            if w > 100 and h > 50:
                regions.append((x, y, w, h))
        
        return regions
    
    def _parse_ocr_table(self, text: str, page: int) -> Optional[TableData]:
        """解析 OCR 文本为表格"""
        lines = text.strip().split('\n')
        
        if len(lines) < 2:
            return None
        
        rows = []
        for line in lines:
            # 按空格或制表符分割
            cells = re.split(r'\s{2,}|\t', line.strip())
            if cells:
                rows.append(cells)
        
        if len(rows) < 2:
            return None
        
        headers = rows[0]
        data_rows = rows[1:]
        
        return TableData(
            page=page,
            headers=headers,
            rows=data_rows,
            caption="",
            source=""
        )


class PDFParserWithTableOCR:
    """支持表格 OCR 的 PDF 解析器"""
    
    def __init__(self, use_ocr: bool = False, use_table_ocr: bool = True):
        # 如果没有 OCR，创建简单的 TableData
        if not HAS_OCR:
            global TableData
            from dataclasses import dataclass
            @dataclass
            class SimpleTableData:
                page: int
                headers: List[str]
                rows: List[List[str]]
                caption: str = ""
                source: str = ""
            TableData = SimpleTableData
        self.use_ocr = use_ocr and HAS_OCR
        self.use_table_ocr = use_table_ocr and HAS_OCR
        self.table_extractor = TableOCRExtractor() if self.use_table_ocr else None
        
        # 已知公司词典
        self.known_companies = {
            '北方稀土': '600111',
            '包钢股份': '600010',
            '包钢集团': '600010',
        }
    
    def parse(self, pdf_path: str) -> Dict:
        """
        解析 PDF（文本 + 表格 OCR）
        """
        result = {
            'title': '',
            'content': '',
            'page_count': 0,
            'tables': [],
            'table_data': [],  # 结构化表格数据
            'metadata': {},
            'parse_method': 'text'
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            result['page_count'] = len(pdf.pages)
            all_text = []
            
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                text = page.extract_text()
                
                # 提取文本
                if text:
                    all_text.append(text)
                elif self.use_ocr:
                    # 文本提取失败，使用 OCR
                    ocr_text = self._ocr_page(page)
                    if ocr_text:
                        all_text.append(ocr_text)
                        result['parse_method'] = 'ocr'
                
                # 提取表格
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if self.table_extractor:
                            table_data = self.table_extractor._process_table(table, page_num)
                        else:
                            # 简单处理
                            table_data = TableData(
                                page=page_num,
                                headers=[str(c) for c in table[0]] if table else [],
                                rows=[[str(c) for c in row] for row in table[1:]] if len(table) > 1 else []
                            )
                        
                        if table_data:
                            result['tables'].append(table)
                            result['table_data'].append(table_data)
                            # 表格转文本
                            table_text = self._table_to_text(table)
                            all_text.append(f"\n【表格 第{page_num}页】\n{table_text}\n")
                elif self.use_table_ocr and self.table_extractor:
                    # 表格提取失败，使用 OCR
                    ocr_tables = self.table_extractor._ocr_page_tables(page)
                    for table_data in ocr_tables:
                        result['table_data'].append(table_data)
                        all_text.append(f"\n【表格 第{page_num}页】\n{table_data.caption}\n")
                
                # 第 1 页提取元数据
                if i == 0 and text:
                    result['title'] = self._extract_title(text)
                    result['metadata'] = self._extract_metadata(text)
            
            result['content'] = '\n'.join(all_text)
        
        # 后处理
        result['content'] = self._post_process(result['content'])
        
        return result
    
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
            print(f"OCR 失败：{e}")
        
        return ""
    
    def _table_to_text(self, table: List) -> str:
        """表格转文本"""
        lines = []
        for row in table:
            if row:
                line = ' | '.join(str(cell) for cell in row if cell)
                if line.strip():
                    lines.append(line)
        return '\n'.join(lines)
    
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
        
        # 公司
        for company, code in self.known_companies.items():
            if company in text:
                metadata['company'] = company
                metadata['stock_code'] = code
                break
        
        return metadata
    
    def _post_process(self, text: str) -> str:
        """后处理"""
        # 校正乱码
        if '[北 Tab 方 le_稀 Sto 土 ckIn(f6o]0 0111)' in text:
            text = text.replace('[北 Tab 方 le_稀 Sto 土 ckIn(f6o]0 0111)', '北方稀土 (600111)')
        
        return text


if __name__ == '__main__':
    # 测试
    if HAS_OCR:
        print("✅ OCR 库已安装")
    else:
        print("⚠️ OCR 库未安装，请运行：pip install pytesseract pdf2image opencv-python")
    
    parser = PDFParserWithTableOCR(use_ocr=False, use_table_ocr=False)
    result = parser.parse('data/raw/test.pdf')
    
    print("\n" + "="*70)
    print("PDF 解析结果（表格 OCR 增强版）")
    print("="*70)
    print(f"解析方式：{result['parse_method']}")
    print(f"标题：{result['title']}")
    print(f"页数：{result['page_count']}")
    print(f"内容长度：{len(result['content'])}")
    print(f"表格数量：{len(result['tables'])}")
    print(f"结构化表格：{len(result['table_data'])}")
    print(f"元数据：{result['metadata']}")
    
    # 显示前 3 个表格
    if result['table_data']:
        print("\n【前 3 个表格】")
        for i, table in enumerate(result['table_data'][:3]):
            print(f"\n表格{i+1} (第{table.page}页):")
            print(f"  表头：{table.headers}")
            print(f"  行数：{len(table.rows)}")
