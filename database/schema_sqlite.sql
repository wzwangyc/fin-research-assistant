-- 金融研报助手 - SQLite 专用 Schema

-- 行业表
CREATE TABLE IF NOT EXISTS industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES industries(id),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 公司表
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    ticker VARCHAR(20) UNIQUE,
    industry_id INTEGER REFERENCES industries(id),
    market_cap INTEGER,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 研报表
CREATE TABLE IF NOT EXISTS research_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(500) NOT NULL,
    file_path VARCHAR(500),
    publish_date DATE,
    analyst VARCHAR(100),
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 实体表（NER 结果）
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER REFERENCES research_reports(id),
    text VARCHAR(200) NOT NULL,
    entity_type VARCHAR(50),
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 情感表
CREATE TABLE IF NOT EXISTS sentiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER REFERENCES research_reports(id),
    section VARCHAR(100),
    label VARCHAR(20),
    score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_reports_date ON research_reports(publish_date);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_sentiments_label ON sentiments(label);
