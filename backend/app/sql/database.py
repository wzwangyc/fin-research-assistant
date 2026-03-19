#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据库连接模块"""

import os
from contextlib import contextmanager


class Database:
    """数据库管理器（默认 SQLite）"""
    
    def __init__(self, use_sqlite: bool = True):
        if use_sqlite:
            import sqlite3
            self.db_path = "data/fin_research.db"
            self.conn = sqlite3.connect(self.db_path)
            print(f"[DB] SQLite: {self.db_path}")
        else:
            import psycopg2
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'fin_research'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '')
            )
            print(f"[DB] PostgreSQL")
    
    @contextmanager
    def get_cursor(self):
        """获取游标"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def init_db(self, schema_path: str = "database/schema.sql"):
        """初始化数据库（创建表）"""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # SQLite 需要逐条执行语句
        statements = [s.strip() for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        with self.get_cursor() as cursor:
            for stmt in statements:
                if stmt:
                    cursor.execute(stmt)
        
        print(f"[DB] 初始化完成")
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


# 全局实例
_db_instance = None


def get_database(use_sqlite: bool = True):
    """获取数据库实例（单例）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(use_sqlite)
    return _db_instance
