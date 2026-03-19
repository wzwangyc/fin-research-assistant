#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报 NER 实体识别模块（增强版）
使用规则 + 词典 + 上下文识别
支持：公司名称、股票代码、金额、百分比、日期等
"""

import re
from typing import List, Tuple, Dict

# A 股常见股票代码前缀
STOCK_CODE_PREFIXES = ['600', '601', '603', '605',  # 沪市主板
                       '000', '001', '002', '003',  # 深市主板/中小板
                       '300', '301',  # 创业板
                       '688',  # 科创板
                       '8', '4', '9']  # 北交所

# 金融关键词
FINANCE_KEYWORDS = [
    '公司', '集团', '股份', '有限', '责任', '科技', '发展',
    '实业', '国际', '控股', '投资', '能源', '资源',
    '稀土', '金属', '材料', '矿业', '冶炼'
]

class NERExtractor:
    """增强版金融实体识别器"""
    
    def __init__(self):
        # 股票代码正则（6 位数字）
        self.stock_code_pattern = re.compile(r'\b([0-9]{6})\b')
        # 带括号的股票代码 (600111)
        self.stock_code_bracket_pattern = re.compile(r'[（(]([0-9]{6})[）)]')
        # PDF 表格乱码中的股票代码 (f6o]0 0111) -> 600111
        self.stock_code_garbled_pattern = re.compile(r'[（(][a-zA-Z]+[\]\)]?\s*([0-9])\s*([0-9]{5})')
        # 公司名称关键词
        self.company_keywords = ['稀土', '北方', '公司', '集团', '股份']
        # 金额正则
        self.amount_pattern = re.compile(r'(\d+(?:\.\d+)?)[亿万千百]?元')
        # 百分比正则
        self.percent_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')
        # 日期正则
        self.date_pattern = re.compile(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日号]?)')
        
    def extract_stock_codes(self, text: str) -> List[Tuple[str, str, int]]:
        """
        提取股票代码
        Returns: [(代码，上下文，位置), ...]
        """
        results = []
        found_codes = set()  # 避免重复
        
        # 方法 1：匹配括号内的代码 (600111)
        for match in self.stock_code_bracket_pattern.finditer(text):
            code = match.group(1)
            if code not in found_codes and self._is_valid_stock_code(code):
                start = max(0, match.start() - 100)
                prefix = text[start:match.start()].replace('\n', ' ')
                results.append((code, prefix, match.start()))
                found_codes.add(code)
        
        # 方法 2：匹配 PDF 乱码中的股票代码
        for match in self.stock_code_garbled_pattern.finditer(text):
            # 尝试从乱码中提取数字
            digit1 = match.group(1)
            digit2 = match.group(2)
            code = digit1 + digit2
            if code not in found_codes and self._is_valid_stock_code(code):
                start = max(0, match.start() - 100)
                prefix = text[start:match.start()].replace('\n', ' ')
                results.append((code, prefix, match.start()))
                found_codes.add(code)
        
        # 方法 3：直接匹配 6 位数字（更严格，需要前后有金融相关词）
        for match in self.stock_code_pattern.finditer(text):
            code = match.group(1)
            if code not in found_codes and self._is_valid_stock_code(code):
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                
                if any(kw in context for kw in ['股票', '代码', '公司', '买入', '评级', '证券']):
                    results.append((code, context.replace('\n', ' '), match.start()))
                    found_codes.add(code)
        
        # 方法 4：从公司名推断（如果有"北方稀土"等知名公司）
        for keyword in self.company_keywords:
            if keyword in text:
                # 北方稀土 -> 600111
                if '北方稀土' in text and '600111' not in found_codes:
                    results.append(('600111', '北方稀土', text.find('北方稀土')))
                    found_codes.add('600111')
                # 包钢股份 -> 600010
                if '包钢股份' in text and '600010' not in found_codes:
                    results.append(('600010', '包钢股份', text.find('包钢股份')))
                    found_codes.add('600010')
        
        return results
    
    def _is_valid_stock_code(self, code: str) -> bool:
        """验证股票代码是否有效"""
        if len(code) != 6:
            return False
        for prefix in STOCK_CODE_PREFIXES:
            if code.startswith(prefix):
                return True
        return False
    
    def extract_company_names(self, text: str, stock_codes: List[str] = None) -> List[str]:
        """
        提取公司名称
        基于关键词和上下文
        """
        companies = []
        
        # 方法 1：直接匹配知名公司名
        known_companies = {
            '北方稀土': '600111',
            '包钢股份': '600010',
            '包钢集团': '600010',
            '国信证券': '002736'
        }
        for name in known_companies.keys():
            if name in text:
                companies.append(name)
        
        # 方法 2：查找包含金融关键词的短语
        for keyword in FINANCE_KEYWORDS:
            pattern = re.compile(r'([^\s,，.。]{2,20}' + keyword + r'[^\s,，.。]{0,10})')
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if self._is_likely_company(name) and name not in companies:
                    companies.append(name)
        
        # 方法 3：查找股票代码附近的公司名
        if stock_codes:
            for code in stock_codes:
                pattern = re.compile(r'([^\s,，.。]{2,15})[（(]' + code + r'[）)]')
                for match in pattern.finditer(text):
                    name = match.group(1).strip()
                    if len(name) >= 3 and name not in companies:
                        companies.append(name)
        
        # 去重，优先保留短的公司名
        return list(set(companies))[:10]
    
    def _is_likely_company(self, name: str) -> bool:
        """判断是否可能是公司名称"""
        if len(name) < 3 or len(name) > 30:
            return False
        # 排除一些常见非公司词汇
        exclude_words = ['这个', '那个', '我们', '他们', '公司', '企业']
        for word in exclude_words:
            if word in name:
                return False
        return True
    
    def extract_amounts(self, text: str) -> List[str]:
        """提取金额"""
        return self.amount_pattern.findall(text)
    
    def extract_percentages(self, text: str) -> List[str]:
        """提取百分比"""
        return self.percent_pattern.findall(text)
    
    def extract_dates(self, text: str) -> List[str]:
        """提取日期"""
        return self.date_pattern.findall(text)
    
    def extract(self, text: str) -> Dict:
        """
        完整提取所有实体
        Returns: {
            'stock_codes': [...],
            'companies': [...],
            'amounts': [...],
            'percentages': [...],
            'dates': [...]
        }
        """
        stock_codes = self.extract_stock_codes(text)
        code_list = [c[0] for c in stock_codes]
        
        return {
            'stock_codes': stock_codes,
            'companies': self.extract_company_names(text, code_list),
            'amounts': self.extract_amounts(text),
            'percentages': self.extract_percentages(text),
            'dates': self.extract_dates(text)
        }


if __name__ == '__main__':
    # 测试
    test_text = """
    北方稀土 (600111) 发布 2021 年年报，实现营业收入 297.78 亿元，
    同比增长 40.2%。公司是全球最大的轻稀土供应商。
    """
    
    ner = NERExtractor()
    result = ner.extract(test_text)
    
    print("测试结果：")
    print(f"股票代码：{result['stock_codes']}")
    print(f"公司名称：{result['companies']}")
    print(f"金额：{result['amounts']}")
    print(f"百分比：{result['percentages']}")
    print(f"日期：{result['dates']}")
