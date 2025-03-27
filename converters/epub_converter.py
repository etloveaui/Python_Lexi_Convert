# converters/epub_converter.py
import os
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from datetime import datetime
from utils.text_utils import split_text_into_chunks

def epub_to_json(epub_path, chunk_size=1000, include_toc=True, advanced_metadata=True, gpt_optimized=True):
    """
    EPUB 파일을 읽어 메타데이터와 본문(챕터) 텍스트를 추출하여
    JSON 형식의 딕셔너리로 반환합니다.
    """
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        return None, f"EPUB 파일을 읽는 중 오류 발생: {str(e)}"
    
    book_data = {}
    
    # 기본 메타데이터 추출
    title = book.get_metadata('DC', 'title')
    creator = book.get_metadata('DC', 'creator')
    language = book.get_metadata('DC', 'language')
    identifier = book.get_metadata('DC', 'identifier')
    
    book_data['metadata'] = {
        'title': title[0][0] if title else 'Unknown',
        'creator': creator[0][0] if creator else 'Unknown',
        'language': language[0][0] if language else 'Unknown',
        'identifier': identifier[0][0] if identifier else 'Unknown',
        'file_type': 'EPUB'
    }
    
    # 확장 메타데이터 추가
    if advanced_metadata:
        book_data['metadata'].update({
            'file_path': epub_path,
            'file_name': os.path.basename(epub_path),
            'file_size': os.path.getsize(epub_path),
            'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'converter_version': "2.1.0"
        })
    
    # 목차 추출
    if include_toc:
        try:
            toc = []
            for item in book.toc:
                if isinstance(item, tuple) and len(item) >= 2:
                    title, href = item[0], item[1]
                    toc.append({'title': title, 'href': href})
                elif hasattr(item, 'title') and hasattr(item, 'href'):
                    toc.append({'title': item.title, 'href': item.href})
            book_data['toc'] = toc
        except Exception as e:
            book_data['toc_error'] = str(e)
            book_data['toc'] = []
    
    # 각 문서(챕터) 추출 및 텍스트만 추출
    if gpt_optimized:
        # GPT 최적화 형식: 청크로 분할하고 인덱스 부여
        chunks = []
        chapter_idx = 0
        
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                chapter_idx += 1
                content = item.get_content().decode('utf-8', errors='replace')  # 명시적 디코딩 추가
                soup = BeautifulSoup(content, 'html.parser')
                
                # 챕터 제목 추출 시도
                chapter_title = "Unknown"
                try:
                    if soup.title and soup.title.string:
                        chapter_title = soup.title.string.strip()
                    else:
                        h_tags = soup.find(['h1', 'h2', 'h3', 'h4'])
                        if h_tags and h_tags.text:
                            chapter_title = h_tags.text.strip()
                except:
                    pass
                
                text = soup.get_text().strip()
                if not text:
                    continue
                
                # 텍스트를 청크로 분할
                text_chunks = split_text_into_chunks(text, chunk_size)
                
                for i, chunk in enumerate(text_chunks):
                    chunks.append({
                        'id': f"ch{chapter_idx}_{i+1}",
                        'chapter_index': chapter_idx,
                        'chunk_index': i+1,
                        'chapter_title': chapter_title,
                        'content': chunk,
                        'char_count': len(chunk)
                    })
        
        book_data['chunks'] = chunks
        book_data['total_chunks'] = len(chunks)
    
    else:
        # 기존 형식: 챕터 텍스트 전체 저장
        chapters = []
        for item in book.get_items():
            if item.get_type() == ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='replace')  # 명시적 디코딩 추가
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text().strip()
                if text:
                    chapters.append(text)
        
        book_data['chapters'] = chapters
        book_data['total_chapters'] = len(chapters)
    
    # GPT 지식 파일에 활용 가능하도록 정보 추가
    book_data['gpt_knowledge'] = True
    book_data['format_version'] = "2.0" if gpt_optimized else "1.0"
    book_data['chunked'] = gpt_optimized
    book_data['book_converter'] = "Lexi Convert by El Fenomeno"
    
    return book_data, None
