#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基准测试框架
功能：
1. PDF 解析性能测试
2. 表格提取准确率测试
3. 实体识别 F1 分数
4. 批量处理速度测试
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    metric: str
    value: float
    unit: str
    timestamp: str
    details: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            'test_name': self.test_name,
            'metric': self.metric,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp,
            'details': self.details or {}
        }


class PDFParserBenchmark:
    """PDF 解析基准测试"""
    
    def __init__(self):
        self.results = []
    
    def test_parse_speed(self, pdf_files: List[str]) -> BenchmarkResult:
        """
        测试解析速度
        
        Returns:
            BenchmarkResult (pages/second)
        """
        from backend.app.nlp.enhanced_parser import EnhancedPDFParser
        
        parser = EnhancedPDFParser()
        
        start = time.time()
        total_pages = 0
        
        for pdf_file in pdf_files:
            pages = parser.parse(pdf_file)
            total_pages += len(pages)
        
        elapsed = time.time() - start
        speed = total_pages / elapsed if elapsed > 0 else 0
        
        result = BenchmarkResult(
            test_name='PDF 解析速度',
            metric='pages_per_second',
            value=speed,
            unit='页/秒',
            timestamp=datetime.now().isoformat(),
            details={
                'total_pages': total_pages,
                'total_files': len(pdf_files),
                'elapsed_seconds': elapsed
            }
        )
        
        self.results.append(result)
        return result
    
    def test_memory_usage(self, pdf_file: str) -> BenchmarkResult:
        """测试内存使用"""
        import tracemalloc
        from backend.app.nlp.enhanced_parser import EnhancedPDFParser
        
        tracemalloc.start()
        
        parser = EnhancedPDFParser()
        pages = parser.parse(pdf_file)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        result = BenchmarkResult(
            test_name='内存使用',
            metric='peak_memory',
            value=peak / 1024 / 1024,
            unit='MB',
            timestamp=datetime.now().isoformat(),
            details={
                'current_memory': current / 1024 / 1024,
                'peak_memory': peak / 1024 / 1024,
                'pages': len(pages)
            }
        )
        
        self.results.append(result)
        return result


class TableExtractionBenchmark:
    """表格提取基准测试"""
    
    def __init__(self):
        self.results = []
    
    def test_accuracy(self, test_cases: List[Tuple[str, List[List[str]]]]) -> BenchmarkResult:
        """
        测试表格提取准确率
        
        Args:
            test_cases: [(pdf_path, expected_table), ...]
        
        Returns:
            BenchmarkResult (accuracy)
        """
        from backend.app.nlp.enhanced_parser import EnhancedPDFParser
        
        parser = EnhancedPDFParser()
        
        correct_cells = 0
        total_cells = 0
        
        for pdf_path, expected_table in test_cases:
            pages = parser.parse(pdf_path)
            
            # 简单比较（实际应该更复杂）
            for page in pages:
                for table in page.tables:
                    for i, row in enumerate(table):
                        if i < len(expected_table):
                            for j, cell in enumerate(row):
                                if j < len(expected_table[i]):
                                    total_cells += 1
                                    if cell and cell.strip() == expected_table[i][j].strip():
                                        correct_cells += 1
        
        accuracy = correct_cells / total_cells if total_cells > 0 else 0
        
        result = BenchmarkResult(
            test_name='表格提取准确率',
            metric='accuracy',
            value=accuracy,
            unit='%',
            timestamp=datetime.now().isoformat(),
            details={
                'correct_cells': correct_cells,
                'total_cells': total_cells,
                'test_cases': len(test_cases)
            }
        )
        
        self.results.append(result)
        return result


class EntityRecognitionBenchmark:
    """实体识别基准测试"""
    
    def __init__(self):
        self.results = []
    
    def test_f1_score(self, test_texts: List[Tuple[str, Dict]]) -> BenchmarkResult:
        """
        测试实体识别 F1 分数
        
        Args:
            test_texts: [(text, expected_entities), ...]
        
        Returns:
            BenchmarkResult (f1_score)
        """
        from backend.app.nlp.ner import NERExtractor
        
        ner = NERExtractor()
        
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        for text, expected in test_texts:
            result = ner.extract(text)
            
            # 比较简单版本（实际应该更复杂）
            expected_companies = set(expected.get('companies', []))
            predicted_companies = set(result['companies'])
            
            true_positives += len(expected_companies & predicted_companies)
            false_positives += len(predicted_companies - expected_companies)
            false_negatives += len(expected_companies - predicted_companies)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        result = BenchmarkResult(
            test_name='实体识别 F1 分数',
            metric='f1_score',
            value=f1,
            unit='score',
            timestamp=datetime.now().isoformat(),
            details={
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
        )
        
        self.results.append(result)
        return result


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self):
        self.parser_benchmark = PDFParserBenchmark()
        self.table_benchmark = TableExtractionBenchmark()
        self.entity_benchmark = EntityRecognitionBenchmark()
        self.results = []
    
    def run_all(self, test_data_dir: str = 'data/benchmark'):
        """运行所有基准测试"""
        test_path = Path(test_data_dir)
        
        print("="*70)
        print("运行基准测试套件")
        print("="*70)
        
        # 1. PDF 解析速度测试
        print("\n【1/4】PDF 解析速度测试...")
        pdf_files = list(test_path.glob('*.pdf'))
        if pdf_files:
            result = self.parser_benchmark.test_parse_speed([str(f) for f in pdf_files])
            print(f"   ✅ {result.value:.2f} {result.unit}")
            self.results.append(result)
        
        # 2. 内存使用测试
        print("\n【2/4】内存使用测试...")
        if pdf_files:
            result = self.parser_benchmark.test_memory_usage(str(pdf_files[0]))
            print(f"   ✅ {result.value:.2f} {result.unit}")
            self.results.append(result)
        
        # 3. 表格提取准确率测试
        print("\n【3/4】表格提取准确率测试...")
        # TODO: 添加测试用例
        
        # 4. 实体识别 F1 测试
        print("\n【4/4】实体识别 F1 测试...")
        # TODO: 添加测试用例
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成基准测试报告"""
        print("\n" + "="*70)
        print("基准测试报告")
        print("="*70)
        print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总测试数：{len(self.results)}")
        
        for result in self.results:
            print(f"\n{result.test_name}:")
            print(f"  结果：{result.value:.2f} {result.unit}")
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
        
        # 保存报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'results': [r.to_dict() for r in self.results]
        }
        
        report_path = Path('data/benchmark/report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 报告已保存：{report_path}")


if __name__ == '__main__':
    # 运行基准测试
    suite = BenchmarkSuite()
    suite.run_all('data/raw')
