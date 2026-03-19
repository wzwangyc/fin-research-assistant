#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG（检索增强生成）模块
功能：基于研报内容的智能检索 + LLM 生成
特点：
1. 向量检索 - 语义搜索
2. 引用溯源 - 每个回答都有来源
3. 反幻觉 - 基于事实回答
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDING = True
except ImportError:
    HAS_EMBEDDING = False
    print("⚠️ 未安装 embedding 库，请运行：pip install sentence-transformers")

try:
    import google.generativeai as genai
    HAS_LLM = True
except ImportError:
    HAS_LLM = False


@dataclass
class Chunk:
    """文本块"""
    id: str
    text: str
    page: int
    section: str = ""
    embedding: Optional[np.ndarray] = None


@dataclass
class SearchResult:
    """搜索结果"""
    chunk: Chunk
    score: float
    relevance: str  # high/medium/low


class RAGEngine:
    """RAG 检索引擎"""
    
    def __init__(self, embedding_model: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.chunks: List[Chunk] = []
        self.chunk_index: Dict[str, Chunk] = {}
        
        # 初始化 embedding 模型
        if HAS_EMBEDDING:
            try:
                self.model = SentenceTransformer(embedding_model)
                print(f"✅ Embedding 模型已加载：{embedding_model}")
            except Exception as e:
                print(f"⚠️ Embedding 模型加载失败：{e}")
                self.model = None
        else:
            self.model = None
        
        # LLM 配置
        if HAS_LLM:
            # 从环境变量读取 API Key
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.llm = genai.GenerativeModel('gemini-2.5-flash')
                print("✅ LLM 已配置")
            else:
                self.llm = None
                print("⚠️ 未配置 LLM API Key")
        else:
            self.llm = None
    
    def load_document(self, text: str, page_size: int = 500):
        """
        加载文档，分块存储
        Args:
            text: 完整文档文本
            page_size: 每块大小（字符数）
        """
        print(f"开始加载文档，总长度：{len(text)} 字符...")
        
        # 按页分割
        pages = text.split('【第')
        
        chunk_id = 0
        for page_content in pages:
            if not page_content.strip():
                continue
            
            # 提取页码
            page_match = re.search(r'(\d+) 页】', page_content)
            page_num = int(page_match.group(1)) if page_match else 0
            
            # 提取内容（去掉页码标记）
            content = re.sub(r'\d+ 页】.*?\n', '', page_content)
            
            # 分块
            for i in range(0, len(content), page_size):
                chunk_text = content[i:i+page_size].strip()
                if not chunk_text:
                    continue
                
                chunk_id_str = f"chunk_{chunk_id}"
                chunk = Chunk(
                    id=chunk_id_str,
                    text=chunk_text,
                    page=page_num,
                    section=""
                )
                
                # 生成 embedding
                if self.model:
                    chunk.embedding = self.model.encode(chunk_text)
                
                self.chunks.append(chunk)
                self.chunk_index[chunk_id_str] = chunk
                chunk_id += 1
        
        print(f"✅ 文档加载完成，共{len(self.chunks)}个文本块")
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        语义搜索
        Args:
            query: 搜索查询
            top_k: 返回结果数量
        """
        if not self.chunks:
            return []
        
        # 生成查询 embedding
        if self.model:
            query_embedding = self.model.encode(query)
        else:
            # 简单关键词匹配（fallback）
            return self._keyword_search(query, top_k)
        
        # 计算相似度
        scores = []
        for chunk in self.chunks:
            if chunk.embedding is not None:
                # 余弦相似度
                similarity = np.dot(query_embedding, chunk.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk.embedding)
                )
                scores.append((chunk, similarity))
        
        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回 top_k
        results = []
        for chunk, score in scores[:top_k]:
            relevance = 'high' if score > 0.7 else ('medium' if score > 0.5 else 'low')
            results.append(SearchResult(
                chunk=chunk,
                score=score,
                relevance=relevance
            ))
        
        return results
    
    def _keyword_search(self, query: str, top_k: int) -> List[SearchResult]:
        """关键词搜索（fallback）"""
        results = []
        query_words = query.lower().split()
        
        for chunk in self.chunks:
            score = 0
            for word in query_words:
                if word in chunk.text.lower():
                    score += 1
            
            if score > 0:
                results.append(SearchResult(
                    chunk=chunk,
                    score=score / len(query_words),
                    relevance='medium' if score > 2 else 'low'
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def generate_answer(self, query: str, search_results: List[SearchResult]) -> Dict:
        """
        基于搜索结果生成答案
        Returns:
            {
                'answer': str,
                'sources': List[Dict],
                'confidence': str
            }
        """
        if not search_results:
            return {
                'answer': '抱歉，未找到相关信息。',
                'sources': [],
                'confidence': 'unknown'
            }
        
        # 构建上下文
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results):
            context_parts.append(f"[来源{i+1}] (第{result.chunk.page}页)\n{result.chunk.text}")
            sources.append({
                'page': result.chunk.page,
                'text': result.chunk.text[:200] + '...',
                'relevance': result.relevance,
                'score': result.score
            })
        
        context = '\n\n'.join(context_parts)
        
        # 使用 LLM 生成答案
        if self.llm:
            prompt = f"""基于以下信息回答问题。如果信息不足，请说明。

【背景信息】
{context}

【问题】
{query}

【要求】
1. 只基于提供的信息回答
2. 标注信息来源（页码）
3. 不确定的信息要说明
4. 简洁明了

【回答】
"""
            try:
                response = self.llm.generate_content(prompt)
                answer = response.text
            except Exception as e:
                answer = f"LLM 生成失败：{e}"
        else:
            # 无 LLM 时，直接返回搜索结果
            answer = "根据文档内容：\n\n"
            for i, result in enumerate(search_results[:3]):
                answer += f"第{result.chunk.page}页：{result.chunk.text[:200]}...\n\n"
        
        # 置信度评估
        high_relevance_count = sum(1 for r in search_results if r.relevance == 'high')
        if high_relevance_count >= 3:
            confidence = 'high'
        elif high_relevance_count >= 1:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': confidence
        }
    
    def query(self, query: str, top_k: int = 5) -> Dict:
        """
        完整查询流程：搜索 + 生成
        """
        # 1. 搜索
        search_results = self.search(query, top_k)
        
        # 2. 生成答案
        result = self.generate_answer(query, search_results)
        
        # 3. 添加搜索统计
        result['query'] = query
        result['search_stats'] = {
            'total_chunks': len(self.chunks),
            'results_found': len(search_results),
            'high_relevance': sum(1 for r in search_results if r.relevance == 'high')
        }
        
        return result


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("RAG 引擎测试")
    print("="*70)
    
    # 创建引擎
    engine = RAGEngine()
    
    # 加载测试文本
    test_text = """
    【第 1 页】
    北方稀土 (600111) 是全球最大的轻稀土供应商。
    公司控股股东包钢集团拥有白云鄂博矿的独家采矿权。
    
    【第 2 页】
    我们预计公司 2021-2023 年每股收益 1.16/1.55/2.15 元。
    合理估值区间 55.5-59.8 元，首次覆盖给予"买入"评级。
    """
    
    engine.load_document(test_text, page_size=200)
    
    # 测试查询
    print("\n【测试查询】")
    query = "北方稀土的估值是多少？"
    print(f"问题：{query}")
    
    result = engine.query(query)
    
    print(f"\n答案：{result['answer']}")
    print(f"置信度：{result['confidence']}")
    print(f"来源数量：{len(result['sources'])}")
