# converters/html_converter.py

from io import StringIO
import os
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime
from utils.text_utils import split_text_into_chunks
import pandas as pd

def parse_table_to_json(table_soup):
    """HTML 테이블(soup)을 JSON 친화적인 리스트-딕셔너리 형태로 변환합니다."""
    try:
        # pandas를 사용하여 HTML 테이블을 DataFrame으로 읽어옵니다.
        df = pd.read_html(StringIO(str(table_soup)), flavor='bs4')[0]
        return df.to_dict(orient='records')
    except Exception:
        # pandas로 파싱 실패 시, 수동으로 파싱 시도
        headers = [th.get_text(strip=True) for th in table_soup.find_all('th')]
        rows = []
        for tr in table_soup.find('tbody').find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            rows.append(dict(zip(headers, cells)))
        return rows


def html_to_json(html_path, chunk_size=1000, advanced_metadata=True, gpt_optimized=True):
    """
    구조화된 리포트 HTML 파일을 분석하여 계층적인 JSON으로 변환합니다.
    """
    try:
        with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        return None, f"HTML 파일을 읽는 중 오류 발생: {str(e)}"

    book_data = {}

    # 1. 메타데이터 추출
    title_tag = soup.find('div', class_='text-[22px]')
    title = title_tag.get_text(strip=True) if title_tag else os.path.basename(html_path)
    book_data['metadata'] = { 'title': title, 'file_type': 'HTML' }

    if advanced_metadata:
        book_data['metadata'].update({
            'file_path': html_path,
            'file_name': os.path.basename(html_path),
            'file_size': os.path.getsize(html_path),
            'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'converter_version': "2.2.1" # 최종 버전
        })

    # 2. 본문 섹션 구조적으로 파싱 (개선된 최종 로직)
    main_content_divs = soup.find_all('div', class_='markdown-body')
    sections = []
    current_section = None
    
    for content_div in main_content_divs:
        # div 바로 아래의 태그들만 순회하여 계층 구조를 명확히 함
        for element in content_div.find_all(['h2', 'h3', 'p', 'table']):
            if element.name == 'h2':
                # 새로운 h2가 나오면, 이전 h2 섹션을 리스트에 추가
                if current_section:
                    sections.append(current_section)
                # 새로운 h2 섹션 시작
                current_section = {'title': element.get_text(strip=True), 'content': [], 'subsections': []}
            
            elif element.name == 'h3':
                # h2가 없는 상태에서 h3가 나올 경우 무시
                if not current_section: continue
                # 새로운 h3를 subsections에 추가
                subsection = {'subtitle': element.get_text(strip=True), 'content': []}
                current_section['subsections'].append(subsection)

            elif element.name == 'p' or element.name == 'table':
                # h2가 없는 상태에서 p나 table이 나올 경우 무시
                if not current_section: continue

                # 콘텐츠 아이템 생성
                if element.name == 'p':
                    text = element.get_text(strip=True)
                    if not text: continue
                    content_item = {'type': 'paragraph', 'text': text}
                else: # table
                    table_data = parse_table_to_json(element)
                    content_item = {'type': 'table', 'data': table_data}

                # h3가 있으면 h3에, 없으면 h2에 콘텐츠 추가
                if current_section['subsections']:
                    current_section['subsections'][-1]['content'].append(content_item)
                else:
                    current_section['content'].append(content_item)

    # 마지막으로 작업 중이던 h2 섹션을 리스트에 추가
    if current_section:
        sections.append(current_section)
    
    book_data['sections'] = sections

    # 3. 참고문헌(References) 파싱
    references_section = soup.find('div', id='h0-References')
    if references_section:
        references_list = []
        for ref_div in references_section.find_next_siblings('div', class_='text-[14px]'):
            ref_id_tag = ref_div.find('a', class_='no-underline')
            ref_id = ref_id_tag.get_text(strip=True) if ref_id_tag else ''
            
            source_tag = ref_div.find('span')
            source = source_tag.get_text(strip=True) if source_tag else ''

            link_tag = ref_div.find('a', target='_blank')
            link_text = link_tag.get_text(strip=True) if link_tag else ''
            link_href = link_tag['href'] if link_tag and link_tag.has_attr('href') else ''

            references_list.append({
                'id': ref_id,
                'source': source,
                'title': link_text,
                'url': link_href
            })
        book_data['references'] = references_list

    book_data['gpt_knowledge'] = True
    book_data['book_converter'] = "Lexi Convert by El Fenomeno"

    return book_data, None