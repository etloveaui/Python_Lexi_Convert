# converters/exporters.py
import os
import json
from utils.json_encoder import CustomJSONEncoder

def convert_to_markdown(json_data, output_path):
    """JSON 데이터를 마크다운 형식으로 변환합니다."""
    try:
        with open(output_path, 'w', encoding='utf-8') as md_file:
            # 제목 및 메타데이터
            md_file.write(f"# {json_data['metadata']['title']}\n\n")
            
            # 작가 정보
            if 'creator' in json_data['metadata'] and json_data['metadata']['creator']:
                md_file.write(f"**작가**: {json_data['metadata']['creator']}\n\n")
            
            # 파일 유형
            file_type = json_data['metadata'].get('file_type', '')
            if file_type:
                md_file.write(f"**파일 유형**: {file_type}\n\n")
            
            md_file.write("---\n\n")
            
            # 목차가 있으면 목차 추가 (EPUB 전용)
            if 'toc' in json_data and json_data['toc']:
                md_file.write("## 목차\n\n")
                for item in json_data['toc']:
                    md_file.write(f"- {item['title']}\n")
                md_file.write("\n---\n\n")
            
            # 청크 또는 챕터/페이지 내용 출력
            if 'chunks' in json_data:
                # EPUB 처리 - 챕터별 구성
                if file_type == 'EPUB':
                    current_chapter = 0
                    for chunk in json_data['chunks']:
                        if 'chapter_index' in chunk and chunk['chapter_index'] != current_chapter:
                            current_chapter = chunk['chapter_index']
                            md_file.write(f"## {chunk.get('chapter_title', f'챕터 {current_chapter}')}\n\n")
                        md_file.write(f"{chunk['content']}\n\n")
                        md_file.write("---\n\n")
                # PDF 처리 - 페이지별 구성
                else:
                    current_page = 0
                    for chunk in json_data['chunks']:
                        if 'page_number' in chunk and chunk['page_number'] != current_page:
                            current_page = chunk['page_number']
                            md_file.write(f"## 페이지 {current_page}\n\n")
                        md_file.write(f"{chunk['content']}\n\n")
                        md_file.write("---\n\n")
            
            # 챕터 형식 (EPUB 용)
            elif 'chapters' in json_data:
                for i, chapter in enumerate(json_data['chapters'], 1):
                    md_file.write(f"## 챕터 {i}\n\n")
                    md_file.write(f"{chapter}\n\n")
                    md_file.write("---\n\n")
            
            # 페이지 형식 (PDF 용)
            elif 'pages' in json_data:
                for page in json_data['pages']:
                    page_num = page.get('page_number', 0)
                    md_file.write(f"## 페이지 {page_num}\n\n")
                    md_file.write(f"{page['content']}\n\n")
                    md_file.write("---\n\n")
        
        return True, None
    except Exception as e:
        return False, str(e)

def convert_to_text(json_data, output_path):
    """JSON 데이터를 일반 텍스트 형식으로 변환합니다."""
    try:
        with open(output_path, 'w', encoding='utf-8') as txt_file:
            # 제목 및 메타데이터
            txt_file.write(f"{json_data['metadata']['title']}\n")
            
            # 작가 정보
            if 'creator' in json_data['metadata'] and json_data['metadata']['creator']:
                txt_file.write(f"작가: {json_data['metadata']['creator']}\n")
            
            # 파일 유형
            file_type = json_data['metadata'].get('file_type', '')
            if file_type:
                txt_file.write(f"파일 유형: {file_type}\n")
            
            txt_file.write("="*50 + "\n\n")
            
            # 청크 또는 챕터/페이지 내용 출력
            if 'chunks' in json_data:
                # EPUB 처리
                if file_type == 'EPUB':
                    current_chapter = 0
                    for chunk in json_data['chunks']:
                        if 'chapter_index' in chunk and chunk['chapter_index'] != current_chapter:
                            current_chapter = chunk['chapter_index']
                            txt_file.write(f"=== {chunk.get('chapter_title', f'챕터 {current_chapter}')} ===\n\n")
                        txt_file.write(f"{chunk['content']}\n\n")
                        txt_file.write("-"*50 + "\n\n")
                # PDF 처리
                else:
                    current_page = 0
                    for chunk in json_data['chunks']:
                        if 'page_number' in chunk and chunk['page_number'] != current_page:
                            current_page = chunk['page_number']
                            txt_file.write(f"=== 페이지 {current_page} ===\n\n")
                        txt_file.write(f"{chunk['content']}\n\n")
                        txt_file.write("-"*50 + "\n\n")
            
            # 챕터 형식 (EPUB 용)
            elif 'chapters' in json_data:
                for i, chapter in enumerate(json_data['chapters'], 1):
                    txt_file.write(f"=== 챕터 {i} ===\n\n")
                    txt_file.write(f"{chapter}\n\n")
                    txt_file.write("-"*50 + "\n\n")
            
            # 페이지 형식 (PDF 용)
            elif 'pages' in json_data:
                for page in json_data['pages']:
                    page_num = page.get('page_number', 0)
                    txt_file.write(f"=== 페이지 {page_num} ===\n\n")
                    txt_file.write(f"{page['content']}\n\n")
                    txt_file.write("-"*50 + "\n\n")
        
        return True, None
    except Exception as e:
        return False, str(e)

def save_json_file(json_data, output_path):
    """JSON 데이터를 파일로 저장합니다."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False, cls=CustomJSONEncoder)
        
        return True, None
    except Exception as e:
        return False, str(e)
