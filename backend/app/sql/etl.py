#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ETL 数据管道"""

from pathlib import Path
from typing import List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.nlp.parser import PDFParser
from backend.app.nlp.ner import NERExtractor
from backend.app.nlp.sentiment import SentimentAnalyzer
from backend.app.sql.database import get_database


class ResearchETL:
    """研报 ETL 处理器"""
    
    def __init__(self):
        self.parser = PDFParser()
        self.ner = NERExtractor()
        self.sentiment = SentimentAnalyzer()
        self.db = get_database(use_sqlite=True)
    
    def process(self, pdf_path: str) -> int:
        """完整 ETL 流程"""
        print(f"\n[ETL] {pdf_path}")
        
        # 1. 解析 PDF
        data = self.parser.parse(pdf_path)
        if 'error' in data:
            return -1
        
        # 2. 实体识别 + 情感分析
        entities = self.ner.extract(data['content'])
        sentiment = self.sentiment.analyze(data['content'])
        
        # 3. 入库
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO research_reports (title, content, sentiment_score, file_path, page_count)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """, (data['title'], data['content'], sentiment['score'], data['file_path'], data['page_count']))
            
            report_id = cursor.fetchone()[0]
            
            # 插入实体
            for name, type_, _ in entities:
                cursor.execute("""
                    INSERT INTO entities (report_id, entity_name, entity_type)
                    VALUES (?, ?, ?)
                """, (report_id, name, type_))
        
        print(f"[完成] ID={report_id}\n")
        return report_id
    
    def process_batch(self, pdf_dir: str) -> List[int]:
        """批量处理"""
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))
        print(f"[批量] 发现 {len(pdf_files)} 个文件")
        
        ids = []
        for pdf in pdf_files:
            rid = self.process(str(pdf))
            if rid > 0:
                ids.append(rid)
        
        print(f"[完成] {len(ids)}/{len(pdf_files)}\n")
        return ids


# 测试
if __name__ == "__main__":
    etl = ResearchETL()
    
    # 初始化数据库
    etl.db.init_db("database/schema.sql")
    
    # 测试文件
    test_pdf = "data/raw/test.pdf"
    if Path(test_pdf).exists():
        report_id = etl.process(test_pdf)
        print(f"\n研报 ID: {report_id}")
    else:
        print(f"[WARNING] 测试文件不存在：{test_pdf}")
        print(f"[INFO] 请将 PDF 文件放入 data/raw/ 目录")
