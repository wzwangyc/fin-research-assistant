#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能问答模块
功能：基于 RAG 的多轮对话问答系统
特点：
1. 多轮对话 - 支持上下文
2. 引用溯源 - 每个回答都有来源
3. 反幻觉 - 基于事实回答
4. 金融专用 - 支持金融术语理解
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .rag import RAGEngine


@dataclass
class Message:
    """对话消息"""
    role: str  # user/assistant
    content: str
    timestamp: str
    sources: Optional[List[Dict]] = None
    confidence: Optional[str] = None


class ChatBot:
    """智能问答机器人"""
    
    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        self.rag = rag_engine or RAGEngine()
        self.conversation_history: List[Message] = []
        self.max_history = 10  # 保留最近 10 轮对话
        
        # 金融词典
        self.finance_terms = {
            '估值': ['估值', '目标价', '合理价格', '价值'],
            '评级': ['评级', '推荐', '买入', '增持', '中性'],
            '财务': ['营收', '利润', '净利润', '每股收益', 'PE', 'PB'],
            '业务': ['业务', '产品', '产能', '产量', '市场'],
        }
    
    def load_document(self, text: str):
        """加载文档"""
        self.rag.load_document(text)
    
    def chat(self, query: str) -> Dict:
        """
        对话查询
        Returns:
            {
                'answer': str,
                'sources': List[Dict],
                'confidence': str,
                'follow_up': List[str]  # 推荐追问
            }
        """
        # 1. 识别意图
        intent = self._identify_intent(query)
        
        # 2. RAG 检索 + 生成
        rag_result = self.rag.query(query, top_k=5)
        
        # 3. 构建回答
        answer = rag_result['answer']
        
        # 4. 生成推荐追问
        follow_up = self._generate_follow_up(query, intent)
        
        # 5. 保存对话历史
        user_msg = Message(
            role='user',
            content=query,
            timestamp=datetime.now().isoformat()
        )
        
        assistant_msg = Message(
            role='assistant',
            content=answer,
            timestamp=datetime.now().isoformat(),
            sources=rag_result['sources'],
            confidence=rag_result.get('confidence', 'unknown')
        )
        
        self.conversation_history.append(user_msg)
        self.conversation_history.append(assistant_msg)
        
        # 保留最近 N 轮
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history*2:]
        
        return {
            'answer': answer,
            'sources': rag_result['sources'],
            'confidence': rag_result.get('confidence', 'unknown'),
            'follow_up': follow_up,
            'search_stats': rag_result.get('search_stats', {})
        }
    
    def _identify_intent(self, query: str) -> str:
        """识别用户意图"""
        query_lower = query.lower()
        
        # 估值类问题
        if any(term in query_lower for term in self.finance_terms['估值']):
            return 'valuation'
        
        # 评级类问题
        if any(term in query_lower for term in self.finance_terms['评级']):
            return 'rating'
        
        # 财务类问题
        if any(term in query_lower for term in self.finance_terms['财务']):
            return 'financial'
        
        # 业务类问题
        if any(term in query_lower for term in self.finance_terms['业务']):
            return 'business'
        
        # 通用问题
        return 'general'
    
    def _generate_follow_up(self, query: str, intent: str) -> List[str]:
        """生成推荐追问"""
        follow_ups = {
            'valuation': [
                "估值方法是什么？",
                "与同行业相比如何？",
                "目标价的上涨空间是多少？"
            ],
            'rating': [
                "评级的依据是什么？",
                "主要风险有哪些？",
                "何时调整评级？"
            ],
            'financial': [
                "营收增长主要来自哪里？",
                "利润率变化趋势如何？",
                "现金流情况怎样？"
            ],
            'business': [
                "主要产品有哪些？",
                "市场份额是多少？",
                "竞争优势是什么？"
            ],
            'general': [
                "公司的核心竞争力是什么？",
                "主要风险有哪些？",
                "未来发展前景如何？"
            ]
        }
        
        return follow_ups.get(intent, follow_ups['general'])[:3]
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            }
            for msg in self.conversation_history
        ]
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def export_conversation(self, filename: str):
        """导出对话记录"""
        data = {
            'export_time': datetime.now().isoformat(),
            'total_messages': len(self.conversation_history),
            'messages': self.get_conversation_history()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 对话记录已导出：{filename}")


class ResearchChatBot(ChatBot):
    """研报专用问答机器人"""
    
    def __init__(self):
        super().__init__()
        
        # 研报专用提示词
        self.system_prompt = """你是一个专业的金融研报问答助手。
基于提供的研报内容回答问题。
要求：
1. 只基于研报内容回答，不编造信息
2. 标注信息来源（页码）
3. 不确定的信息要说明
4. 使用专业但易懂的语言
5. 涉及数据要准确"""
    
    def chat(self, query: str) -> Dict:
        """研报专用对话"""
        # 调用父类方法
        result = super().chat(query)
        
        # 添加研报专用信息
        result['document_info'] = {
            'loaded': len(self.rag.chunks) > 0,
            'total_chunks': len(self.rag.chunks)
        }
        
        return result
    
    def summarize(self) -> Dict:
        """生成研报摘要"""
        queries = [
            "这份研报的核心观点是什么？",
            "公司的主要竞争优势有哪些？",
            "主要风险因素有哪些？",
            "盈利预测和估值是多少？"
        ]
        
        summary = {}
        for query in queries:
            result = self.chat(query)
            summary[query] = result['answer']
        
        return summary


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("智能问答机器人测试")
    print("="*70)
    
    # 创建机器人
    bot = ResearchChatBot()
    
    # 加载测试文档
    test_doc = """
    【第 1 页】
    北方稀土 (600111) 是全球最大的轻稀土供应商。
    公司控股股东包钢集团拥有白云鄂博矿的独家采矿权。
    首次覆盖给予"买入"评级，合理估值区间 55.5-59.8 元。
    
    【第 2 页】
    我们预计公司 2021-2023 年每股收益 1.16/1.55/2.15 元。
    利润增速分别为 404.7%/34.0%/38.6%。
    市盈率 (PE) 分别为 34.89/26.03/18.78 倍。
    """
    
    bot.load_document(test_doc)
    
    # 测试对话
    test_queries = [
        "北方稀土的评级是什么？",
        "估值是多少？",
        "未来三年的盈利预测？",
        "公司的竞争优势？"
    ]
    
    print("\n【对话测试】")
    for query in test_queries:
        print(f"\n问：{query}")
        result = bot.chat(query)
        print(f"答：{result['answer'][:200]}...")
        print(f"置信度：{result['confidence']}")
        print(f"推荐追问：{result['follow_up']}")
    
    # 导出对话
    bot.export_conversation('test_conversation.json')
