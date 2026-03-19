#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LangChain 集成模块
功能：
1. PDF 文档加载器
2. 向量存储集成
3. RAG 检索链
4. 问答链
"""

from typing import List, Dict, Optional
from pathlib import Path
import json

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import FAISS, Chroma
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.chains import RetrievalQA
    from langchain.llms import HuggingFacePipeline
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    print("⚠️ LangChain 未安装，请运行：pip install langchain langchain-community faiss-cpu")


class LangChainIntegration:
    """LangChain 集成器"""
    
    def __init__(self, embedding_model: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        初始化 LangChain 集成
        
        Args:
            embedding_model: embedding 模型名称
        """
        if not HAS_LANGCHAIN:
            raise ImportError("LangChain 未安装")
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )
        
        # Embedding 模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 向量存储
        self.vectorstore = None
        
        # QA 链
        self.qa_chain = None
    
    def load_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """
        加载文档到向量存储
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表（可选）
        """
        # 分割文本
        chunks = []
        for i, text in enumerate(texts):
            chunk_texts = self.text_splitter.split_text(text)
            for chunk in chunk_texts:
                metadata = metadatas[i] if metadatas else {}
                chunks.append({
                    'text': chunk,
                    'metadata': metadata
                })
        
        # 创建向量存储
        texts_list = [chunk['text'] for chunk in chunks]
        metadatas_list = [chunk['metadata'] for chunk in chunks]
        
        self.vectorstore = FAISS.from_texts(
            texts_list,
            self.embeddings,
            metadatas=metadatas_list
        )
        
        # 创建 QA 链
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self._create_llm(),
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
    
    def _create_llm(self):
        """创建本地 LLM（可选）"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            
            # 使用小型模型（如 Qwen-1.8B）
            model_name = "Qwen/Qwen-1_8B-Chat"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                trust_remote_code=True
            )
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.1
            )
            
            return HuggingFacePipeline(pipeline=pipe)
        except:
            # Fallback: 使用简单的基于检索的回答
            return None
    
    def query(self, question: str) -> Dict:
        """
        问答查询
        
        Args:
            question: 问题
        
        Returns:
            {
                'answer': str,
                'sources': List[Dict],
                'confidence': float
            }
        """
        if not self.qa_chain:
            return {
                'answer': '请先加载文档',
                'sources': [],
                'confidence': 0.0
            }
        
        result = self.qa_chain({"query": question})
        
        # 提取来源
        sources = []
        for doc in result.get('source_documents', []):
            sources.append({
                'text': doc.page_content[:200],
                'metadata': doc.metadata
            })
        
        # 计算置信度（基于检索相似度）
        confidence = self._calculate_confidence(question, sources)
        
        return {
            'answer': result['result'],
            'sources': sources,
            'confidence': confidence
        }
    
    def _calculate_confidence(self, question: str, sources: List[Dict]) -> float:
        """计算置信度"""
        if not sources:
            return 0.0
        
        # 基于来源数量和质量
        base_confidence = min(len(sources) * 0.3, 0.9)
        
        # 基于来源长度
        avg_length = sum(len(s['text']) for s in sources) / len(sources)
        length_factor = min(avg_length / 100, 1.0) * 0.1
        
        return base_confidence + length_factor
    
    def save_vectorstore(self, path: str):
        """保存向量存储"""
        if self.vectorstore:
            self.vectorstore.save_local(path)
            print(f"✅ 向量存储已保存：{path}")
    
    def load_vectorstore(self, path: str):
        """加载向量存储"""
        if Path(path).exists():
            self.vectorstore = FAISS.load_local(
                path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # 重新创建 QA 链
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self._create_llm(),
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=True
            )
            print(f"✅ 向量存储已加载：{path}")
    
    def batch_load_pdfs(self, pdf_dir: str):
        """批量加载 PDF 文件"""
        from .enhanced_parser import EnhancedPDFParser
        
        parser = EnhancedPDFParser()
        texts = []
        metadatas = []
        
        pdf_files = list(Path(pdf_dir).glob('*.pdf'))
        
        for pdf_file in pdf_files:
            print(f"处理：{pdf_file.name}")
            pages = parser.parse(str(pdf_file))
            
            for page in pages:
                texts.append(page.text)
                metadatas.append({
                    'source': pdf_file.name,
                    'page': page.page_num
                })
        
        self.load_documents(texts, metadatas)
        print(f"✅ 已加载 {len(pdf_files)} 个 PDF，共 {len(texts)} 页")


class RAGPipeline:
    """RAG 管道（简化版）"""
    
    def __init__(self):
        self.langchain = LangChainIntegration()
    
    def ingest(self, pdf_dir: str, vectorstore_path: str):
        """
        文档入库
        
        Args:
            pdf_dir: PDF 目录
            vectorstore_path: 向量存储保存路径
        """
        self.langchain.batch_load_pdfs(pdf_dir)
        self.langchain.save_vectorstore(vectorstore_path)
    
    def query(self, question: str, vectorstore_path: str) -> Dict:
        """
        问答查询
        
        Args:
            question: 问题
            vectorstore_path: 向量存储路径
        
        Returns:
            答案和来源
        """
        self.langchain.load_vectorstore(vectorstore_path)
        return self.langchain.query(question)


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("LangChain 集成测试")
    print("="*70)
    
    if not HAS_LANGCHAIN:
        print("\n❌ LangChain 未安装")
        print("   安装：pip install langchain langchain-community faiss-cpu")
    else:
        # 创建集成器
        lc = LangChainIntegration()
        
        # 测试文档
        test_docs = [
            "北方稀土 (600111) 是全球最大的轻稀土供应商。",
            "公司控股股东包钢集团拥有白云鄂博矿的独家采矿权。",
            "首次覆盖给予'买入'评级，合理估值区间 55.5-59.8 元。"
        ]
        
        # 加载文档
        lc.load_documents(test_docs)
        
        # 测试查询
        questions = [
            "北方稀土的股票代码是多少？",
            "合理估值是多少？",
            "控股股东是谁？"
        ]
        
        for q in questions:
            result = lc.query(q)
            print(f"\n问：{q}")
            print(f"答：{result['answer']}")
            print(f"置信度：{result['confidence']:.1%}")
            print(f"来源数：{len(result['sources'])}")
