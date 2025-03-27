# converters/pdf_converter.py
import os
import fitz  # PyMuPDF
from datetime import datetime
from utils.text_utils import split_text_into_chunks

# PDF 지원 체크
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    fitz = None
    PDF_SUPPORT = False

def pdf_to_json(pdf_path, chunk_size=1000, advanced_metadata=True, gpt_optimized=True):
    """PDF 파일을 JSON 형식으로 변환합니다."""
    try:
        if not PDF_SUPPORT:
            return None, "PDF 변환을 위해 PyMuPDF(fitz) 모듈이 필요합니다. 'pip install pymupdf'로 설치하세요."
        
        doc = fitz.open(pdf_path)
    except Exception as e:
        return None, f"PDF 파일을 열기 실패: {str(e)}"
    
    book_data = {}
    
    # 메타데이터 추출
    metadata = doc.metadata
    book_data['metadata'] = {
        'title': metadata.get('title', os.path.basename(pdf_path)),
        'creator': metadata.get('author', 'Unknown'),
        'subject': metadata.get('subject', ''),
        'keywords': metadata.get('keywords', ''),
        'language': '',  # PDF에서는 언어 메타데이터가 명확하지 않음
        'pages': len(doc),
        'file_type': 'PDF'
    }
    
    # 확장 메타데이터 추가
    if advanced_metadata:
        book_data['metadata'].update({
            'file_path': pdf_path,
            'file_name': os.path.basename(pdf_path),
            'file_size': os.path.getsize(pdf_path),
            'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'converter_version': "2.1.0"
        })
    
    # 텍스트 추출
    if gpt_optimized:
        # GPT 최적화: 청크로 분할
        chunks = []
        for page_idx, page in enumerate(doc, 1):
            text = page.get_text()
            if not text.strip():
                continue
                
            # 페이지별 텍스트를 청크로 분할
            text_chunks = split_text_into_chunks(text, chunk_size)
            
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    'id': f"pg{page_idx}_{i+1}",
                    'page_number': page_idx,
                    'chunk_index': i+1,
                    'content': chunk,
                    'char_count': len(chunk)
                })
        
        book_data['chunks'] = chunks
        book_data['total_chunks'] = len(chunks)
    
    else:
        # 페이지별 텍스트 전체 저장
        pages = []
        for page_idx, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                pages.append({
                    'page_number': page_idx,
                    'content': text
                })
        
        book_data['pages'] = pages
        book_data['total_pages'] = len(pages)
    
    # GPT 지식 파일에 활용 가능하도록 정보 추가
    book_data['gpt_knowledge'] = True
    book_data['format_version'] = "2.0" if gpt_optimized else "1.0"
    book_data['chunked'] = gpt_optimized
    book_data['book_converter'] = "Lexi Convert by El Fenomeno"
    
    doc.close()
    
    return book_data, None
