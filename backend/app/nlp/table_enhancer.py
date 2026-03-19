#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表格提取增强模块
功能：
1. 合并单元格检测
2. 表格结构验证
3. 表格类型识别
4. 表格内容补全
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TableCell:
    """表格单元格"""
    text: str
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    is_merged: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'row': self.row,
            'col': self.col,
            'rowspan': self.rowspan,
            'colspan': self.colspan,
            'is_merged': self.is_merged
        }


class TableEnhancer:
    """表格增强器"""
    
    def __init__(self):
        self.empty_markers = ['', ' ', '-', '—', '–', 'N/A', 'n/a', 'null', 'None']
    
    def detect_merged_cells(self, table: List[List[str]]) -> List[Tuple[int, int, int, int]]:
        """
        检测合并单元格
        
        Returns:
            List of (row, col, rowspan, colspan)
        """
        if not table or len(table) < 2:
            return []
        
        merged_cells = []
        rows = len(table)
        cols = max(len(row) for row in table)
        
        # 检测逻辑：
        # 1. 空单元格可能是合并的结果
        # 2. 检查相邻单元格内容
        
        for i in range(rows):
            for j in range(cols):
                if j >= len(table[i]):
                    continue
                
                cell = table[i][j]
                
                # 检测水平合并（colspan）
                if cell and j + 1 < cols:
                    colspan = self._detect_colspan(table, i, j)
                    if colspan > 1:
                        merged_cells.append((i, j, 1, colspan))
                
                # 检测垂直合并（rowspan）
                if cell and i + 1 < rows:
                    rowspan = self._detect_rowspan(table, i, j)
                    if rowspan > 1:
                        merged_cells.append((i, j, rowspan, 1))
        
        return merged_cells
    
    def _detect_colspan(self, table: List[List[str]], row: int, col: int) -> int:
        """检测水平合并（列跨度）"""
        if col >= len(table[row]):
            return 1
        
        base_cell = table[row][col].strip()
        if not base_cell:
            return 1
        
        colspan = 1
        for j in range(col + 1, len(table[row])):
            cell = table[row][j].strip()
            # 如果相邻单元格为空或包含相同内容，可能是合并
            if cell in self.empty_markers or base_cell in cell:
                colspan += 1
            else:
                break
        
        return colspan
    
    def _detect_rowspan(self, table: List[List[str]], row: int, col: int) -> int:
        """检测垂直合并（行跨度）"""
        if row >= len(table) or col >= len(table[row]):
            return 1
        
        base_cell = table[row][col].strip()
        if not base_cell:
            return 1
        
        rowspan = 1
        for i in range(row + 1, len(table)):
            if col >= len(table[i]):
                break
            
            cell = table[i][col].strip()
            # 如果下方单元格为空或包含相同内容，可能是合并
            if cell in self.empty_markers or base_cell in cell:
                rowspan += 1
            else:
                break
        
        return rowspan
    
    def fill_empty_cells(self, table: List[List[str]]) -> List[List[str]]:
        """填充空单元格（基于上下文）"""
        if not table:
            return []
        
        rows = len(table)
        cols = max(len(row) for row in table)
        filled_table = [row[:] for row in table]  # 深拷贝
        
        for i in range(rows):
            for j in range(cols):
                if j >= len(filled_table[i]):
                    filled_table[i].append('')
                    continue
                
                cell = filled_table[i][j].strip()
                
                # 如果是空单元格
                if cell in self.empty_markers:
                    # 1. 尝试从上方单元格继承
                    if i > 0 and j < len(filled_table[i-1]):
                        filled_table[i][j] = filled_table[i-1][j]
                    # 2. 尝试从左侧单元格继承
                    elif j > 0:
                        filled_table[i][j] = filled_table[i][j-1]
        
        return filled_table
    
    def identify_headers(self, table: List[List[str]]) -> List[int]:
        """识别表头行"""
        if not table or len(table) < 2:
            return [0]
        
        header_rows = []
        
        # 启发式规则：
        # 1. 第一行通常是表头
        # 2. 包含特定关键词（如"名称"、"代码"、"日期"等）
        # 3. 字体加粗（如果有格式信息）
        
        header_keywords = ['名称', '代码', '日期', '时间', '金额', '数量', '比例', 
                          'Name', 'Code', 'Date', 'Amount', 'Number', 'Ratio',
                          '202', '201', '编号', '序号']
        
        for i, row in enumerate(table[:3]):  # 只检查前 3 行
            row_text = ' '.join(str(cell) for cell in row if cell)
            
            # 检查是否包含表头关键词
            if any(kw in row_text for kw in header_keywords):
                header_rows.append(i)
            # 第一行默认是表头
            elif i == 0:
                header_rows.append(i)
        
        return header_rows
    
    def validate_structure(self, table: List[List[str]]) -> Dict:
        """验证表格结构"""
        if not table:
            return {'valid': False, 'issues': ['空表格']}
        
        issues = []
        cols = len(table[0])
        
        # 1. 检查列数一致性
        for i, row in enumerate(table):
            if len(row) != cols:
                issues.append(f'第{i+1}行列数不一致：期望{cols}，实际{len(row)}')
        
        # 2. 检查空行
        for i, row in enumerate(table):
            if all(cell.strip() in self.empty_markers for cell in row):
                issues.append(f'第{i+1}行为空行')
        
        # 3. 检查空列
        for j in range(cols):
            col_values = [row[j].strip() if j < len(row) else '' for row in table]
            if all(val in self.empty_markers for val in col_values):
                issues.append(f'第{j+1}列为空列')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'rows': len(table),
            'cols': cols
        }
    
    def enhance(self, table: List[List[str]]) -> Dict:
        """
        完整表格增强流程
        
        Returns:
            {
                'headers': List[int],
                'merged_cells': List[Tuple],
                'filled_table': List[List[str]],
                'validation': Dict
            }
        """
        # 1. 验证结构
        validation = self.validate_structure(table)
        
        # 2. 识别表头
        headers = self.identify_headers(table)
        
        # 3. 检测合并单元格
        merged_cells = self.detect_merged_cells(table)
        
        # 4. 填充空单元格
        filled_table = self.fill_empty_cells(table)
        
        return {
            'headers': headers,
            'merged_cells': merged_cells,
            'filled_table': filled_table,
            'validation': validation,
            'original_rows': len(table),
            'original_cols': max(len(row) for row in table) if table else 0
        }
    
    def to_structured_format(self, table: List[List[str]]) -> Dict:
        """
        转换为结构化格式
        
        Returns:
            {
                'headers': List[str],
                'rows': List[Dict[str, str]],
                'metadata': Dict
            }
        """
        if not table or len(table) < 2:
            return {'headers': [], 'rows': [], 'metadata': {}}
        
        # 增强表格
        enhanced = self.enhance(table)
        filled_table = enhanced['filled_table']
        headers = enhanced['headers']
        
        # 提取表头
        header_row = filled_table[0] if headers and 0 in headers else []
        
        # 转换为行字典
        rows = []
        for row_data in filled_table[1:]:
            row_dict = {}
            for j, value in enumerate(row_data):
                key = header_row[j] if j < len(header_row) else f'col_{j}'
                row_dict[key] = value.strip()
            rows.append(row_dict)
        
        return {
            'headers': [str(h).strip() for h in header_row],
            'rows': rows,
            'metadata': {
                'total_rows': len(rows),
                'total_cols': len(header_row),
                'merged_cells_count': len(enhanced['merged_cells']),
                'validation': enhanced['validation']
            }
        }


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("表格增强模块测试")
    print("="*70)
    
    enhancer = TableEnhancer()
    
    # 测试表格（带合并单元格）
    test_table = [
        ['公司名称', '股票代码', '营收（亿元）', '营收'],
        ['北方稀土', '600111', '297.78', ''],  # 合并单元格
        ['包钢股份', '600010', '150.50', ''],   # 合并单元格
        ['中国稀土', '000831', '85.20', '85.20']
    ]
    
    print("\n原始表格:")
    for i, row in enumerate(test_table):
        print(f"  行{i}: {row}")
    
    # 增强
    enhanced = enhancer.enhance(test_table)
    
    print(f"\n增强结果:")
    print(f"  表头行：{enhanced['headers']}")
    print(f"  合并单元格：{enhanced['merged_cells']}")
    print(f"  验证：{enhanced['validation']}")
    
    # 结构化格式
    structured = enhancer.to_structured_format(test_table)
    
    print(f"\n结构化格式:")
    print(f"  表头：{structured['headers']}")
    print(f"  行数：{len(structured['rows'])}")
    for i, row in enumerate(structured['rows']):
        print(f"  行{i}: {row}")
