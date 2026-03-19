-- 金融研报助手 - 数据库设计
-- SQLite 兼容版本（PostgreSQL 版本见 schema_pg.sql）

-- 启用向量扩展（可选，用于向量检索）
-- CREATE EXTENSION IF NOT EXISTS vector;  -- SQLite 不支持，已注释

-- 行业表
CREATE TABLE IF NOT EXISTS industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES industries(id),  -- 行业层级
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 公司表
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    ticker VARCHAR(20) UNIQUE,  -- 股票代码
    industry_id INTEGER REFERENCES industries(id),
    market_cap INTEGER,  -- 市值（元）
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 研报表
CREATE TABLE IF NOT EXISTS research_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(500) NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    publish_date DATE,
    source VARCHAR(200),  -- 券商名称
    sentiment_score FLOAT,  -- 情感得分 (-1 到 1)
    content TEXT,  -- 完整内容
    summary TEXT,  -- 摘要
    keywords TEXT[],  -- 关键词数组
    file_path VARCHAR(500),  -- PDF 文件路径
    page_count INTEGER,  -- 页数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实体表（NER 提取）
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES research_reports(id) ON DELETE CASCADE,
    entity_name VARCHAR(200) NOT NULL,
    entity_type VARCHAR(50),  -- COMPANY/PERSON/LOCATION/AMOUNT/DATE
    sentiment FLOAT,  -- 实体情感得分
    context TEXT,  -- 上下文
    position INTEGER,  -- 在文中的位置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 问答记录表
CREATE TABLE IF NOT EXISTS qa_logs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT,
    sources TEXT[],  -- 引用的研报 ID
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引（性能优化）
CREATE INDEX IF NOT EXISTS idx_reports_company ON research_reports(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_date ON research_reports(publish_date);
CREATE INDEX IF NOT EXISTS idx_reports_sentiment ON research_reports(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_report ON entities(report_id);
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_industries_parent ON industries(parent_id);

-- 创建视图（常用查询）
CREATE OR REPLACE VIEW v_report_summary AS
SELECT 
    r.id,
    r.title,
    c.name as company_name,
    c.ticker,
    i.name as industry_name,
    r.publish_date,
    r.source,
    r.sentiment_score,
    r.keywords,
    r.created_at
FROM research_reports r
LEFT JOIN companies c ON r.company_id = c.id
LEFT JOIN industries i ON c.industry_id = i.id;

-- 插入示例数据
INSERT INTO industries (name, parent_id) VALUES
    ('科技', NULL),
    ('金融', NULL),
    ('消费', NULL),
    ('医疗', NULL),
    ('半导体', 1),
    ('银行', 2),
    ('白酒', 3)
ON CONFLICT (name) DO NOTHING;

-- 插入示例公司
INSERT INTO companies (name, ticker, industry_id) VALUES
    ('贵州茅台', '600519', 7),
    ('宁德时代', '300750', 1),
    ('中国平安', '601318', 2),
    ('招商银行', '600036', 6)
ON CONFLICT (ticker) DO NOTHING;

-- 注释
COMMENT ON TABLE research_reports IS '金融研报主表，存储解析后的研报内容';
COMMENT ON TABLE entities IS '命名实体识别结果表';
COMMENT ON TABLE qa_logs IS '用户问答记录表，用于追踪和分析';
