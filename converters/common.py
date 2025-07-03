# converters/common.py
import os
from converters.epub_converter import epub_to_json
from converters.pdf_converter import pdf_to_json
from converters.html_converter import html_to_json

def file_to_json(file_path, chunk_size=1000, include_toc=True, advanced_metadata=True, gpt_optimized=True):
    """파일 유형에 따라 적절한 변환 함수를 호출합니다."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.epub':
        return epub_to_json(file_path, chunk_size, include_toc, advanced_metadata, gpt_optimized)
    elif ext == '.pdf':
        # PDF 변환 시 목차는 무시 (PDF의 목차 추출은 더 복잡함)
        return pdf_to_json(file_path, chunk_size, advanced_metadata, gpt_optimized)
    elif ext in ['.html', '.htm']:
        # HTML 변환 시 목차는 무시
        return html_to_json(file_path, chunk_size, advanced_metadata, gpt_optimized)
    else:
        return None, f"지원하지 않는 파일 형식: {ext}"
