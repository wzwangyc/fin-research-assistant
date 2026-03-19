#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
金融研报反幻觉模块
核心原则：拒绝幻觉，只输出有依据的信息
功能：
1. 引用溯源 - 每个信息标注来源页码
2. 置信度评分 - 对识别结果给出置信度
3. 交叉验证 - 多数据源验证
4. 未知标记 - 不确定的信息标注为未知
5. 人工复核标记 - 标注哪些需要人工确认
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"       # 90%+ 确定
    MEDIUM = "medium"   # 70-90% 确定
    LOW = "low"         # 50-70% 确定
    UNKNOWN = "unknown" # 低于 50%，需要人工复核


@dataclass
class Evidence:
    """证据类"""
    text: str           # 原文内容
    page: int           # 页码
    position: int       # 在文本中的位置
    source_type: str    # 来源类型：text/table/image


@dataclass
class ExtractedEntity:
    """提取的实体"""
    entity_type: str    # 实体类型：stock_code/company/amount/date
    value: str          # 提取的值
    confidence: ConfidenceLevel  # 置信度
    evidence: List[Evidence]     # 支持证据
    needs_review: bool  # 是否需要人工复核
    cross_validated: bool = False  # 是否已交叉验证


class AntiHallucinationChecker:
    """反幻觉检查器"""
    
    def __init__(self):
        # 已知公司 - 股票代码映射（权威数据）
        self.known_companies = {
            '北方稀土': '600111',
            '包钢股份': '600010',
            '包钢集团': '600010',
            '中国稀土': '000831',
            '盛和资源': '600392',
            '厦门钨业': '600549',
            '国信证券': '002736',
        }
        
        # 股票代码前缀验证
        self.valid_prefixes = ['600', '601', '603', '605', 
                               '000', '001', '002', '003',
                               '300', '301', '688']
    
    def validate_stock_code(self, code: str, context: str = "") -> Tuple[bool, ConfidenceLevel]:
        """
        验证股票代码
        Returns: (是否有效，置信度)
        """
        # 1. 格式验证
        if not re.match(r'^\d{6}$', code):
            return False, ConfidenceLevel.UNKNOWN
        
        # 2. 前缀验证
        valid_prefix = any(code.startswith(p) for p in self.valid_prefixes)
        if not valid_prefix:
            return False, ConfidenceLevel.UNKNOWN
        
        # 3. 上下文验证
        stock_keywords = ['股票', '代码', '公司', '买入', '评级', '证券', '研报']
        has_context = any(kw in context for kw in stock_keywords)
        
        # 4. 已知公司验证
        known_company = any(company in context for company in self.known_companies.keys())
        expected_code = None
        for company, expected in self.known_companies.items():
            if company in context:
                expected_code = expected
                break
        
        # 综合判断
        if expected_code and code != expected_code:
            return False, ConfidenceLevel.LOW  # 与已知信息冲突
        
        if has_context or known_company:
            return True, ConfidenceLevel.HIGH
        
        return True, ConfidenceLevel.MEDIUM  # 格式正确但缺少上下文
    
    def validate_company(self, name: str, context: str = "") -> Tuple[bool, ConfidenceLevel]:
        """
        验证公司名称
        Returns: (是否有效，置信度)
        """
        # 1. 长度验证
        if len(name) < 3 or len(name) > 30:
            return False, ConfidenceLevel.UNKNOWN
        
        # 2. 关键词验证
        company_keywords = ['公司', '集团', '股份', '有限', '责任']
        has_keyword = any(kw in name for kw in company_keywords)
        
        # 3. 排除常见非公司词
        exclude_words = ['这个', '那个', '我们', '他们', '认为', '表示']
        has_exclude = any(word in name for word in exclude_words)
        
        if has_exclude:
            return False, ConfidenceLevel.LOW
        
        # 4. 已知公司验证
        if name in self.known_companies:
            return True, ConfidenceLevel.HIGH
        
        # 5. 上下文验证
        if has_keyword:
            return True, ConfidenceLevel.MEDIUM
        
        return True, ConfidenceLevel.LOW  # 缺少公司关键词
    
    def validate_amount(self, amount: str, context: str = "") -> Tuple[bool, ConfidenceLevel]:
        """
        验证金额
        Returns: (是否有效，置信度)
        """
        # 1. 格式验证
        amount_pattern = re.compile(r'^\d+(?:\.\d+)?[亿万千百]?元$')
        if not amount_pattern.match(amount):
            return False, ConfidenceLevel.UNKNOWN
        
        # 2. 上下文验证
        finance_keywords = ['收入', '利润', '资产', '负债', '营收', '净利润']
        has_context = any(kw in context for kw in finance_keywords)
        
        if has_context:
            return True, ConfidenceLevel.HIGH
        
        return True, ConfidenceLevel.MEDIUM
    
    def cross_validate(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """
        交叉验证：多个信息源验证同一实体
        """
        # 按实体类型分组
        by_type = {}
        for entity in entities:
            if entity.entity_type not in by_type:
                by_type[entity.entity_type] = []
            by_type[entity.entity_type].append(entity)
        
        # 交叉验证
        validated_entities = []
        for entity_type, type_entities in by_type.items():
            # 同一类型的实体互相验证
            for i, entity in enumerate(type_entities):
                # 检查是否有其他证据支持
                supporting_evidence_count = len(entity.evidence)
                
                if supporting_evidence_count >= 2:
                    entity.cross_validated = True
                    if entity.confidence != ConfidenceLevel.HIGH:
                        entity.confidence = ConfidenceLevel.MEDIUM
                elif supporting_evidence_count == 1:
                    entity.cross_validated = False
                    if entity.confidence == ConfidenceLevel.UNKNOWN:
                        entity.needs_review = True
                
                validated_entities.append(entity)
        
        return validated_entities
    
    def extract_with_evidence(self, text: str, page: int) -> List[ExtractedEntity]:
        """
        提取实体并附带证据
        """
        entities = []
        
        # 1. 提取股票代码
        stock_pattern = re.compile(r'[（(](\d{6})[）)]')
        for match in stock_pattern.finditer(text):
            code = match.group(1)
            context_start = max(0, match.start() - 50)
            context = text[context_start:match.end()]
            
            is_valid, confidence = self.validate_stock_code(code, context)
            
            if is_valid or confidence != ConfidenceLevel.UNKNOWN:
                entity = ExtractedEntity(
                    entity_type='stock_code',
                    value=code,
                    confidence=confidence,
                    evidence=[Evidence(
                        text=context,
                        page=page,
                        position=match.start(),
                        source_type='text'
                    )],
                    needs_review=(confidence == ConfidenceLevel.LOW)
                )
                entities.append(entity)
        
        # 2. 提取公司名称
        for company_name in self.known_companies.keys():
            if company_name in text:
                position = text.find(company_name)
                context_start = max(0, position - 30)
                context_end = min(len(text), position + len(company_name) + 30)
                context = text[context_start:context_end]
                
                is_valid, confidence = self.validate_company(company_name, context)
                
                entity = ExtractedEntity(
                    entity_type='company',
                    value=company_name,
                    confidence=confidence,
                    evidence=[Evidence(
                        text=context,
                        page=page,
                        position=position,
                        source_type='text'
                    )],
                    needs_review=False
                )
                entities.append(entity)
        
        # 3. 提取金额
        amount_pattern = re.compile(r'(\d+(?:\.\d+)?[亿万千百]?元)')
        for match in amount_pattern.finditer(text):
            amount = match.group(1)
            context_start = max(0, match.start() - 50)
            context = text[context_start:match.end()]
            
            is_valid, confidence = self.validate_amount(amount, context)
            
            if is_valid or confidence != ConfidenceLevel.UNKNOWN:
                entity = ExtractedEntity(
                    entity_type='amount',
                    value=amount,
                    confidence=confidence,
                    evidence=[Evidence(
                        text=context,
                        page=page,
                        position=match.start(),
                        source_type='text'
                    )],
                    needs_review=(confidence == ConfidenceLevel.LOW)
                )
                entities.append(entity)
        
        return entities
    
    def generate_report(self, entities: List[ExtractedEntity]) -> Dict:
        """
        生成反幻觉报告
        """
        report = {
            'total_entities': len(entities),
            'high_confidence': sum(1 for e in entities if e.confidence == ConfidenceLevel.HIGH),
            'medium_confidence': sum(1 for e in entities if e.confidence == ConfidenceLevel.MEDIUM),
            'low_confidence': sum(1 for e in entities if e.confidence == ConfidenceLevel.LOW),
            'unknown': sum(1 for e in entities if e.confidence == ConfidenceLevel.UNKNOWN),
            'needs_review': [e for e in entities if e.needs_review],
            'cross_validated': sum(1 for e in entities if e.cross_validated),
            'entities_by_type': {}
        }
        
        # 按类型统计
        for entity in entities:
            if entity.entity_type not in report['entities_by_type']:
                report['entities_by_type'][entity.entity_type] = []
            report['entities_by_type'][entity.entity_type].append({
                'value': entity.value,
                'confidence': entity.confidence.value,
                'needs_review': entity.needs_review,
                'cross_validated': entity.cross_validated,
                'evidence': [{
                    'text': ev.text[:100],
                    'page': ev.page,
                    'source_type': ev.source_type
                } for ev in entity.evidence]
            })
        
        return report


if __name__ == '__main__':
    # 测试
    checker = AntiHallucinationChecker()
    
    test_text = """
    北方稀土 (600111) 发布 2021 年年报，实现营业收入 297.78 亿元，
    同比增长 40.2%。公司是全球最大的轻稀土供应商。
    包钢股份 (600010) 为其控股股东。
    """
    
    entities = checker.extract_with_evidence(test_text, page=1)
    entities = checker.cross_validate(entities)
    report = checker.generate_report(entities)
    
    print("="*60)
    print("反幻觉检查报告")
    print("="*60)
    print(f"\n总实体数：{report['total_entities']}")
    print(f"高置信度：{report['high_confidence']}")
    print(f"中置信度：{report['medium_confidence']}")
    print(f"低置信度：{report['low_confidence']}")
    print(f"需要复核：{len(report['needs_review'])}")
    print(f"已交叉验证：{report['cross_validated']}")
    
    print("\n📊 实体详情:")
    for entity_type, type_entities in report['entities_by_type'].items():
        print(f"\n  {entity_type}:")
        for entity in type_entities:
            print(f"    - {entity['value']} (置信度：{entity['confidence']}, 需复核：{entity['needs_review']})")
