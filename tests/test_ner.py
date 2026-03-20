#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试增强版 NER"""
import sys
sys.path.insert(0, '.')

from backend.app.nlp.ner import NERExtractor

# 使用实际 PDF 内容测试
test_text = """
股票报告网
公司研究 Page 1
证券研究报告—深度报告
有色金属 北方稀土 (600111) 买入
有色金属冶炼 合理估值：55.5-59.8 元 昨收盘：40.36 元
2021 年 07 月 29 日

全球最大轻稀土供应商
公司是全球最大的轻稀土产品供应商，作为六大稀土集团之一
我们预计公司 2021-2023 年每股收益 1.16/1.55/2.15 元
利润增速分别为 404.7%/34.0%/38.6%
营业收入 21,246 百万元，净利润 833 百万元
"""

print("="*60)
print("测试增强版 NER 模块")
print("="*60)

ner = NERExtractor()
result = ner.extract(test_text)

print(f"\n📊 识别结果:")
print(f"\n股票代码：{result['stock_codes']}")
print(f"公司名称：{result['companies']}")
print(f"金额：{result['amounts']}")
print(f"百分比：{result['percentages']}")
print(f"日期：{result['dates']}")

print("\n" + "="*60)
if result['stock_codes']:
    print("✅ 股票代码识别成功！")
else:
    print("❌ 未识别到股票代码")
    
if result['companies']:
    print("✅ 公司名称识别成功！")
else:
    print("❌ 未识别到公司名称")
