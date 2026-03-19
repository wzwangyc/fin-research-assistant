#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多语言 OCR 模块
功能：
1. 80+ 语言支持
2. 低质量扫描优化
3. 批量 OCR 处理
4. OCR 结果后处理
"""

import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

try:
    import pytesseract
    from pdf2image import convert_from_path
    import cv2
    import numpy as np
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️ OCR 库未安装，请运行：pip install pytesseract pdf2image opencv-python")


@dataclass
class OCRResult:
    """OCR 结果"""
    text: str
    confidence: float
    language: str
    page: int
    bbox: Optional[Tuple[int, int, int, int]] = None
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'language': self.language,
            'page': self.page,
            'bbox': self.bbox
        }


class MultiLangOCR:
    """多语言 OCR 识别器"""
    
    # 支持的语言代码
    SUPPORTED_LANGS = {
        '中文简体': 'chi_sim',
        '中文繁体': 'chi_tra',
        '英语': 'eng',
        '日语': 'jpn',
        '韩语': 'kor',
        '法语': 'fra',
        '德语': 'deu',
        '西班牙语': 'spa',
        '葡萄牙语': 'por',
        '俄语': 'rus',
        '阿拉伯语': 'ara',
        '印地语': 'hin',
        '泰语': 'tha',
        '越南语': 'vie',
        '印尼语': 'ind',
        '意大利语': 'ita',
        '荷兰语': 'nld',
        '土耳其语': 'tur',
        '波兰语': 'pol',
        '瑞典语': 'swe'
    }
    
    def __init__(self, default_lang: str = 'chi_sim+eng'):
        """
        初始化 OCR
        
        Args:
            default_lang: 默认语言，支持多语言组合（如'chi_sim+eng'）
        """
        if not HAS_OCR:
            raise ImportError("OCR 库未安装")
        
        self.default_lang = default_lang
        
        # OCR 配置
        self.config = {
            'psm': 6,  # 假设是统一的文本块
            'oem': 3,  # LSTM OCR 引擎
        }
    
    def ocr_image(self, image, lang: Optional[str] = None) -> OCRResult:
        """
        OCR 识别单张图像
        
        Args:
            image: PIL Image 或 numpy array
            lang: 语言代码，默认使用 default_lang
        
        Returns:
            OCRResult
        """
        lang = lang or self.default_lang
        
        # 执行 OCR
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            config=f'--psm {self.config["psm"]} --oem {self.config["oem"]}',
            output_type=pytesseract.Output.DICT
        )
        
        # 合并文本
        text_parts = []
        confidences = []
        
        for i, text in enumerate(data['text']):
            if text.strip():
                text_parts.append(text)
                conf = int(data['conf'][i])
                if conf > 0:
                    confidences.append(conf)
        
        text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return OCRResult(
            text=text,
            confidence=avg_confidence,
            language=lang,
            page=0
        )
    
    def ocr_pdf(self, pdf_path: str, lang: Optional[str] = None, 
                dpi: int = 300) -> List[OCRResult]:
        """
        OCR 识别 PDF
        
        Args:
            pdf_path: PDF 文件路径
            lang: 语言代码
            dpi: DPI（推荐 300+ 用于扫描件）
        
        Returns:
            List[OCRResult]
        """
        lang = lang or self.default_lang
        results = []
        
        # PDF 转图像
        images = convert_from_path(pdf_path, dpi=dpi)
        
        for page_num, image in enumerate(images, 1):
            result = self.ocr_image(image, lang)
            result.page = page_num
            results.append(result)
        
        return results
    
    def preprocess_image(self, image) -> np.ndarray:
        """
        图像预处理（优化 OCR 准确率）
        
        处理步骤：
        1. 转灰度
        2. 去噪
        3. 二值化
        4. 对比度增强
        """
        # 转 numpy array
        if not isinstance(image, np.ndarray):
            image = np.array(image)
        
        # 1. 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # 2. 去噪
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        
        # 3. 二值化（自适应阈值）
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 4. 对比度增强
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(binary)
        
        return enhanced
    
    def ocr_with_preprocess(self, image, lang: Optional[str] = None) -> OCRResult:
        """
        OCR 识别（带预处理）
        
        适用于低质量扫描件
        """
        # 预处理
        processed = self.preprocess_image(image)
        
        # OCR
        result = self.ocr_image(processed, lang)
        
        return result
    
    def batch_ocr(self, pdf_files: List[str], output_dir: str, 
                  lang: Optional[str] = None, max_workers: int = 2):
        """
        批量 OCR 处理
        
        Args:
            pdf_files: PDF 文件列表
            output_dir: 输出目录
            lang: 语言代码
            max_workers: 最大工作线程数
        
        Returns:
            List[Dict] - 处理结果统计
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        def process_single(pdf_path: str):
            try:
                results = self.ocr_pdf(pdf_path, lang)
                
                # 保存结果
                base_name = Path(pdf_path).stem
                output_file = output_path / f"{base_name}_ocr.txt"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    for result in results:
                        f.write(f"=== Page {result.page} ===\n")
                        f.write(f"Confidence: {result.confidence:.1f}%\n")
                        f.write(f"Text:\n{result.text}\n\n")
                
                return {
                    'file': pdf_path,
                    'pages': len(results),
                    'status': 'success',
                    'avg_confidence': sum(r.confidence for r in results) / len(results)
                }
            except Exception as e:
                return {
                    'file': pdf_path,
                    'pages': 0,
                    'status': f'error: {str(e)}'
                }
        
        # 并行处理
        stats = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single, pdf): pdf for pdf in pdf_files}
            
            for future in as_completed(futures):
                result = future.result()
                stats.append(result)
                print(f"✅ {Path(result['file']).name}: {result['pages']}页 - {result['status']}")
        
        return stats
    
    def get_installed_languages(self) -> List[str]:
        """获取已安装的语言包"""
        try:
            langs = pytesseract.get_languages(config='')
            return langs
        except:
            return []
    
    def install_language(self, lang_code: str):
        """
        提示安装语言包
        
        不同系统安装方法：
        - Ubuntu: sudo apt-get install tesseract-ocr-<lang>
        - macOS: brew install tesseract-lang
        - Windows: 下载训练数据到 tessdata 目录
        """
        print(f"语言包 '{lang_code}' 未安装")
        print("\n安装方法:")
        print("  Ubuntu: sudo apt-get install tesseract-ocr-{lang_code}")
        print("  macOS:  brew install tesseract-lang")
        print("  Windows: 下载 https://github.com/tesseract-ocr/tessdata/")


if __name__ == '__main__':
    # 测试
    print("="*70)
    print("多语言 OCR 模块测试")
    print("="*70)
    
    if not HAS_OCR:
        print("\n❌ OCR 库未安装，跳过测试")
        print("   安装：pip install pytesseract pdf2image opencv-python")
    else:
        ocr = MultiLangOCR(default_lang='chi_sim+eng')
        
        # 查看已安装语言
        langs = ocr.get_installed_languages()
        print(f"\n已安装语言：{langs}")
        
        # 测试 OCR（如果有测试文件）
        test_pdf = 'data/raw/test.pdf'
        if os.path.exists(test_pdf):
            print(f"\n开始 OCR 识别：{test_pdf}")
            results = ocr.ocr_pdf(test_pdf)
            
            for result in results[:3]:  # 只显示前 3 页
                print(f"\n第{result.page}页:")
                print(f"  置信度：{result.confidence:.1f}%")
                print(f"  文本：{result.text[:100]}...")
        else:
            print(f"\n⚠️ 测试文件不存在：{test_pdf}")
