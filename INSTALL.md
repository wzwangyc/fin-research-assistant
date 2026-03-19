# 金融研报助手 - 快速安装指南

## 🚀 一键安装（推荐）

### 步骤 1：安装依赖

```bash
cd fin-research-assistant
pip install -r requirements.txt
```

**如果 pip 慢，使用国内镜像：**

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 2：初始化数据库

```bash
python backend/app/sql/database.py
```

### 步骤 3：启动应用

**方式 A：仅前端（推荐）**

```bash
cd frontend
streamlit run app.py
```

浏览器自动打开：http://localhost:8501

**方式 B：前后端都启动**

终端 1（后端）：
```bash
cd backend
uvicorn app.main:app --reload
```

终端 2（前端）：
```bash
cd frontend
streamlit run app.py
```

---

## 📝 测试

### 测试 1：上传研报

1. 打开 http://localhost:8501
2. 点击"研报上传"标签
3. 上传 PDF 文件
4. 点击"开始解析"

### 测试 2：搜索研报

1. 点击"研报搜索"标签
2. 输入公司名称
3. 点击"搜索"

### 测试 3：智能问答

1. 点击"智能问答"标签
2. 输入问题
3. 点击"提问"

---

## ⚠️ 常见问题

### 问题 1：pip 安装失败

**解决：**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或手动安装
pip install pdfplumber PyMuPDF hanlp snownlp streamlit
```

### 问题 2：Streamlit 无法启动

**解决：**
```bash
# 检查端口占用
netstat -ano | findstr :8501

# 更换端口
streamlit run app.py --server.port 8502
```

### 问题 3：PDF 解析失败

**解决：**
```bash
# 检查文件是否存在
ls data/raw/

# 检查文件权限
chmod 644 data/raw/*.pdf
```

---

## 🎯 下一步

1. **上传研报**：将 PDF 放入 `data/raw/` 目录
2. **解析入库**：在界面点击"开始解析"
3. **智能问答**：体验 RAG+LLM 功能（开发中）

---

## 📚 详细文档

- **API 文档**：`docs/API 文档.md`
- **部署指南**：`docs/部署指南.md`
- **测试报告**：`docs/测试报告.md`

---

**祝使用愉快！** 🦁
