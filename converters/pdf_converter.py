# converters/pdf_converter.py

import os
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime
from io import StringIO

# PDF 지원 체크
try:
    import fitz
    PDF_SUPPORT = True
except ImportError:
    fitz = None
    PDF_SUPPORT = False

def parse_pdf_table(table, page_height):
    """PyMuPDF의 Table 객체를 JSON 친화적인 형태로 변환"""
    header_names = [cell for cell in table.header.names]
    rows_data = []
    for row in table.rows:
        row_dict = {}
        for i, cell_text in enumerate(row.cells):
            header = header_names[i] if i < len(header_names) else f"column_{i+1}"
            row_dict[header] = cell_text
        rows_data.append(row_dict)
    return rows_data

def pdf_to_json(pdf_path, chunk_size=1000, advanced_metadata=True, gpt_optimized=True):
    """
    구조화된 리포트 PDF 파일을 분석하여 계층적인 JSON으로 변환합니다.
    """
    if not PDF_SUPPORT:
        return None, "PDF 변환을 위해 PyMuPDF(fitz) 모듈이 필요합니다."

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return None, f"PDF 파일을 열기 실패: {str(e)}"

    book_data = {}
    book_data['metadata'] = {
        'title': doc.metadata.get('title', os.path.basename(pdf_path)),
        'creator': doc.metadata.get('author', 'Unknown'),
        'pages': len(doc),
        'file_type': 'PDF'
    }

    if advanced_metadata:
        book_data['metadata'].update({
            'file_path': pdf_path,
            'file_name': os.path.basename(pdf_path),
            'file_size': os.path.getsize(pdf_path),
            'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'converter_version': "2.2.0"
        })

    sections = []
    current_section = {}
    current_subsection = {}

    for page_num, page in enumerate(doc, 1):
        tables = page.find_tables()
        table_bboxes = [table.bbox for table in tables]
        
        # ✅ 구버전과 호환되도록 flags 옵션을 사용하지 않습니다.
        blocks = page.get_text("dict")["blocks"]
        
        font_sizes = [span['size'] for b in blocks for l in b.get('lines', []) for span in l.get('spans', [])]
        if not font_sizes: continue
        
        common_font_size = max(set(font_sizes), key=font_sizes.count)
        h2_threshold = common_font_size * 1.5
        h3_threshold = common_font_size * 1.2

        for b in blocks:
            block_bbox = fitz.Rect(b['bbox'])
            in_table = any(block_bbox.intersects(table_bbox) for table_bbox in table_bboxes)
            if in_table or not b.get('lines'): continue

            block_text = ""
            block_font_size = 0
            for l in b['lines']:
                for s in l['spans']:
                    block_text += s['text'] + " "
                    if s['size'] > block_font_size:
                        block_font_size = s['size']
            
            block_text = block_text.strip()
            if not block_text: continue
            
            if block_font_size >= h2_threshold:
                if current_section: sections.append(current_section)
                current_section = {'title': block_text, 'subsections': [], 'content': []}
                current_subsection = {}
            elif block_font_size >= h3_threshold:
                if current_subsection: current_section.get('subsections', []).append(current_subsection)
                current_subsection = {'subtitle': block_text, 'content': []}
            else:
                content_item = {'type': 'paragraph', 'text': block_text}
                if current_subsection:
                    current_subsection.get('content', []).append(content_item)
                elif current_section:
                    current_section.get('content', []).append(content_item)
        
        for table in tables:
            table_data = parse_pdf_table(table, page.rect.height)
            table_item = {'type': 'table', 'data': table_data}
            if current_subsection:
                current_subsection.get('content', []).append(table_item)
            elif current_section:
                current_section.get('content', []).append(table_item)

    if current_subsection: current_section.get('subsections', []).append(current_subsection)
    if current_section: sections.append(current_section)

    book_data['sections'] = sections
    book_data['gpt_knowledge'] = True
    book_data['book_converter'] = "Lexi Convert by El Fenomeno"
    
    doc.close()
    
    return book_data, None