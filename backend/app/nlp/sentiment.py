#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""情感分析模块"""

from typing import Dict, Tuple


class SentimentAnalyzer:
    """情感分析器 - 词典方法"""
    
    def __init__(self):
        # 情感词典
        self.positive = ['增长', '突破', '超预期', '推荐', '买入', '利好', '强劲', '看好']
        self.negative = ['下滑', '风险', '警惕', '减持', '卖出', '亏损', '利空', '看空']
    
    def analyze(self, text: str) -> Dict:
        """情感分析（词典匹配）"""
        score = 0
        
        # 正面词 +1，负面词 -1
        for word in self.positive:
            if word in text:
                score += 1
        for word in self.negative:
            if word in text:
                score -= 1
        
        # 归一化到 0-1
        total = len(self.positive) + len(self.negative)
        norm_score = (score / total + 1) / 2
        
        # 判断情感
        if norm_score > 0.6:
            label = 'positive'
        elif norm_score < 0.4:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'label': label,
            'score': norm_score,
        }


# 测试
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # 测试文本
    test_text = """
    贵州茅台发布 2025 年年报，实现营业收入 1500 亿元，同比增长 15%，超预期增长。
    公司盈利能力强劲，继续保持行业领先地位。
    预计 2026 年营收目标为 1800 亿元，增速不低于 20%，看好公司长期价值。
    风险提示：宏观经济波动风险，行业竞争加剧风险。
    """
    
    result = analyzer.analyze_report(test_text)
    
    print("情感分析结果:")
    print(f"整体情感：{result['overall']['label']}")
    print(f"得分：{result['overall']['score']:.2f}")
    print(f"正面词：{result['overall']['positive_words']}")
    print(f"负面词：{result['overall']['negative_words']}")
    print(f"段落平均分：{result['avg_score']:.2f}")
