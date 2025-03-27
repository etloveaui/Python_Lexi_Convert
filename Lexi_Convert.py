import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import subprocess

# PyMuPDF 추가 (PDF 지원용)
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    fitz = None
    PDF_SUPPORT = False

###############################################################################
# Section 객체 직렬화를 위한 사용자 정의 JSON 인코더
###############################################################################
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Section 객체나 기타 직렬화할 수 없는 객체 처리
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        # 기타 직렬화 불가능한 객체에 대한 처리
        try:
            return str(obj)
        except:
            return None
        return json.JSONEncoder.default(self, obj)

###############################################################################
# 필요한 모듈 체크 및 설치
###############################################################################
def check_required_modules():
    required_modules = {
        "ebooklib": "ebooklib",
        "beautifulsoup4": "bs4",
        "pymupdf": "fitz"  # PDF 처리 추가
    }
    
    for module_name, import_name in required_modules.items():
        try:
            __import__(import_name)
        except ImportError:
            if messagebox.askyesno(f"{module_name} 설치 필요", 
                               f"이 프로그램은 {module_name} 모듈이 필요합니다. 설치하시겠습니까?"):
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", module_name], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    messagebox.showinfo("설치 완료", f"{module_name}가 성공적으로 설치되었습니다. 프로그램을 재시작해주세요.")
                    exit(0)
                except Exception as e:
                    messagebox.showerror("설치 실패", f"{module_name} 설치 중 오류가 발생했습니다: {str(e)}")
                    exit(1)
            else:
                exit(1)

###############################################################################
# EPUB -> JSON 변환 함수
###############################################################################
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

###############################################################################
# PDF -> JSON 변환 함수 추가
###############################################################################
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

###############################################################################
# 통합 파일 처리 함수
###############################################################################
def file_to_json(file_path, chunk_size=1000, include_toc=True, advanced_metadata=True, gpt_optimized=True):
    """파일 유형에 따라 적절한 변환 함수를 호출합니다."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.epub':
        return epub_to_json(file_path, chunk_size, include_toc, advanced_metadata, gpt_optimized)
    elif ext == '.pdf':
        # PDF 변환 시 목차는 무시 (PDF의 목차 추출은 더 복잡함)
        return pdf_to_json(file_path, chunk_size, advanced_metadata, gpt_optimized)
    else:
        return None, f"지원하지 않는 파일 형식: {ext}"

def split_text_into_chunks(text, chunk_size=1000):
    """텍스트를 적절한 크기의 청크로 분할합니다."""
    chunks = []
    current_chunk = ""
    
    # 단락 또는 문장 단위로 분할 시도
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        if not para.strip():
            continue
        
        # 현재 청크에 현재 단락을 추가했을 때 청크 크기를 초과하는 경우
        if len(current_chunk) + len(para) > chunk_size:
            # 현재 청크가 있으면 추가
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # 단락이 너무 큰 경우 문장 단위로 분할
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        
                        # 문장이 여전히 너무 큰 경우 강제 분할
                        if len(sentence) > chunk_size:
                            while sentence:
                                chunk_part = sentence[:chunk_size]
                                chunks.append(chunk_part.strip())
                                sentence = sentence[chunk_size:]
                        else:
                            current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    # 마지막 청크 추가
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

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

###############################################################################
# 메인 UI 클래스
###############################################################################
class DoctoJSONApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # 필요한 모듈 확인
        check_required_modules()
        self.title("Lexi Convert by El Fenomeno")
        self.geometry("800x850")
        self.resizable(True, True)

        # 애플리케이션 아이콘 설정 (작업 표시줄 포함)
        try:
            from PIL import Image, ImageTk
            import sys
            
            # 아이콘 파일 경로
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Lexi_Convert.png")
            
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                # Windows 작업 표시줄용 아이콘 준비
                if sys.platform == 'win32':
                    icon_image = icon_image.resize((32, 32), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, icon_photo)
                
                # Windows에서 작업 표시줄 아이콘도 설정
                if sys.platform == 'win32':
                    try:
                        import ctypes
                        app_id = "ElFenomeno.LexiConvert.App"
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                    except Exception as e:
                        print(f"작업 표시줄 아이콘 설정 실패: {e}")
            else:
                print(f"아이콘 파일을 찾을 수 없습니다: {icon_path}")
        except Exception as e:
            print(f"아이콘 설정 실패: {e}")

        # 테마 및 스타일 설정
        self.setup_styles()

        # 경로 및 작업 상태 변수
        self.input_folder = ""   # 파일들이 들어있는 폴더
        self.output_folder = ""  # JSON 파일을 저장할 폴더
        self.document_files = []  # 변환할 파일 목록
        self.is_converting = False
        self.stop_flag = False   # 변환 중단 플래그
        
        # 입력 모드 선택 변수 (파일 또는 폴더)
        self.input_mode = tk.StringVar(value="files")
        
        # 설정 변수들
        self.chunk_size = tk.IntVar(value=1000)
        self.include_toc = tk.BooleanVar(value=True)
        self.advanced_metadata = tk.BooleanVar(value=True)
        self.gpt_optimized = tk.BooleanVar(value=True)
        self.output_format = tk.StringVar(value="json")  # json, markdown, text
        self.merge_output = tk.BooleanVar(value=False)  # 모든 파일을 하나로 병합
        self.merge_filename = tk.StringVar(value="merged_output")
        
        # 디버그 모드 추가
        self.debug_mode = tk.BooleanVar(value=False)
        
        # 마지막 경로 저장
        self.save_last_paths = tk.BooleanVar(value=True)
        self.load_last_paths()

        self.create_widgets()
        
    def setup_styles(self):
        """UI 테마 및 스타일 설정"""
        style = ttk.Style()
        
        # 현대적인 테마 사용
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        bg_color = '#f0f0f0'
        accent_color = '#4e73df'  # 보다 현대적인 파란색
        text_color = '#333333'
        
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=text_color, font=('Segoe UI', 10))
        style.configure("TButton", background=accent_color, foreground="white", font=('Segoe UI', 10))
        style.map("TButton", background=[('active', '#375bc8')])
        style.configure("TRadiobutton", background=bg_color, foreground=text_color, font=('Segoe UI', 10))
        style.configure("TCheckbutton", background=bg_color, foreground=text_color, font=('Segoe UI', 10))
        
        style.configure("Primary.TButton", background=accent_color, foreground="white", font=('Segoe UI', 10, 'bold'))
        style.map("Primary.TButton", background=[('active', '#375bc8')])
        
        # 프로그레스 바 스타일 개선
        style.configure("TProgressbar", thickness=8, background=accent_color)
        
        # 라벨프레임 스타일 개선
        style.configure("TLabelframe", background=bg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=text_color, font=('Segoe UI', 10, 'bold'))
        
        # 콤보박스 스타일
        style.configure("TCombobox", background=bg_color, fieldbackground='white')
        
        self.configure(bg=bg_color)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 노트북(탭) 생성
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 기본 탭
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="기본 설정")
        
        # 고급 탭
        advanced_tab = ttk.Frame(notebook)
        notebook.add(advanced_tab, text="고급 설정")
        
        # 기본 탭 위젯 구성
        self.setup_basic_tab(basic_tab)
        
        # 고급 탭 위젯 구성
        self.setup_advanced_tab(advanced_tab)
        
        # 공통 하단 영역: 변환/취소 버튼, 진행 바, 로그 출력
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 버튼 영역
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.convert_btn = ttk.Button(button_frame, text="변환 시작", 
                                     style="Primary.TButton", command=self.start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.cancel_btn = ttk.Button(button_frame, text="변환 중단", 
                                    command=self.stop_conversion, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 진행 상황 표시 영역
        progress_frame = ttk.Frame(bottom_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_status = ttk.Label(progress_frame, text="준비됨")
        self.progress_status.pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          orient="horizontal", 
                                          mode="determinate", 
                                          length=400)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress_percent = ttk.Label(progress_frame, text="0%")
        self.progress_percent.pack(side=tk.LEFT, padx=(10, 0))
        
        # 로그 출력 (ScrolledText)
        log_frame = ttk.LabelFrame(bottom_frame, text="변환 로그")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15, 
                                                wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("info", foreground="blue")
        self.log_text.tag_configure("warning", foreground="orange")
        
        # 초기 로그 메시지
        self.log("✨ 문서 변환기가 준비되었습니다.", "info")
        self.log("문서 선택 방식을 지정한 후 변환할 파일을 준비해주세요.")

    def setup_basic_tab(self, parent):
        """기본 탭 위젯 구성"""
        # 1) 입력 부분 (좌측)
        input_frame = ttk.LabelFrame(parent, text="입력 설정")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # 입력 방식 선택 (파일 또는 폴더)
        input_mode_frame = ttk.Frame(input_frame)
        input_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_mode_frame, text="문서 선택 방식:").pack(side=tk.LEFT)
        ttk.Radiobutton(input_mode_frame, text="개별 파일 선택", 
                       variable=self.input_mode, value="files",
                       command=self.input_mode_changed).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Radiobutton(input_mode_frame, text="폴더 선택", 
                       variable=self.input_mode, value="folder",
                       command=self.input_mode_changed).pack(side=tk.LEFT, padx=5)
        
        # 파일 선택 영역 (개별 파일 선택 모드)
        self.files_frame = ttk.Frame(input_frame)
        self.files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        file_buttons_frame = ttk.Frame(self.files_frame)
        file_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_buttons_frame, text="파일 선택", 
                 command=self.select_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="파일 목록 초기화", 
                 command=self.clear_files).pack(side=tk.LEFT)
        
        # 선택된 파일 목록
        file_list_frame = ttk.Frame(self.files_frame)
        file_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(file_list_frame, text="선택된 파일:").pack(anchor=tk.W)
        
        file_list_scroll = ttk.Scrollbar(file_list_frame)
        file_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(file_list_frame, height=6, 
                                       yscrollcommand=file_list_scroll.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_list_scroll.config(command=self.file_listbox.yview)
        
        # 폴더 선택 영역 (폴더 선택 모드)
        self.folder_frame = ttk.Frame(input_frame)
        # 처음에는 숨김 상태
        
        folder_select_frame = ttk.Frame(self.folder_frame)
        folder_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_select_frame, text="문서 폴더:").pack(side=tk.LEFT, padx=(0, 5))
        self.input_folder_entry = ttk.Entry(folder_select_frame, width=50)
        self.input_folder_entry.insert(0, self.input_folder)
        self.input_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(folder_select_frame, text="찾아보기", 
                 command=self.select_input_folder).pack(side=tk.LEFT)
        
        # 폴더 내 파일 탐색 버튼
        ttk.Button(self.folder_frame, text="폴더 내 모든 EPUB/PDF 파일 찾기", 
                 command=self.find_files_in_folder).pack(fill=tk.X, pady=5)
        
        # 찾은 파일 정보 표시
        self.folder_files_label = ttk.Label(self.folder_frame, text="발견된 파일: 0개")
        self.folder_files_label.pack(anchor=tk.W, pady=5)
        
        # 2) 출력 부분
        output_frame = ttk.LabelFrame(parent, text="출력 설정")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # 출력 폴더 선택
        out_folder_frame = ttk.Frame(output_frame)
        out_folder_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(out_folder_frame, text="출력 폴더:").pack(side=tk.LEFT, padx=(0, 5))
        self.output_folder_entry = ttk.Entry(out_folder_frame, width=50)
        self.output_folder_entry.insert(0, self.output_folder)
        self.output_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(out_folder_frame, text="찾아보기", 
                 command=self.select_output_folder).pack(side=tk.LEFT)
        
        # 출력 포맷 선택
        format_frame = ttk.LabelFrame(output_frame, text="출력 포맷")
        format_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Radiobutton(format_frame, text="JSON (기본)", 
                      variable=self.output_format, value="json").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(format_frame, text="마크다운 (.md)", 
                      variable=self.output_format, value="markdown").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(format_frame, text="텍스트 (.txt)", 
                      variable=self.output_format, value="text").pack(anchor=tk.W, padx=10, pady=2)
        
        # GPT 최적화 옵션
        gpt_frame = ttk.Frame(output_frame)
        gpt_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Checkbutton(gpt_frame, text="GPT 분석에 최적화된 형식으로 변환 (청크 분할, 인덱싱 적용)", 
                       variable=self.gpt_optimized).pack(anchor=tk.W)
        
        # 초기 모드에 따라 UI 조정
        self.input_mode_changed()

    def setup_advanced_tab(self, parent):
        """고급 탭 위젯 구성"""
        # 1) 텍스트 청크 사이즈 설정
        chunk_frame = ttk.LabelFrame(parent, text="텍스트 분할 설정")
        chunk_frame.pack(fill=tk.X, pady=10, padx=5)
        
        chunk_info = ttk.Label(chunk_frame, 
                             text="텍스트 청크 크기는 문서를 작은 단위로 나누는 기준 문자 수입니다.\n"
                                  "GPT와 같은 AI 모델에서 활용하기 좋은 크기로 설정하세요.")
        chunk_info.pack(anchor=tk.W, padx=10, pady=5)
        
        chunk_size_frame = ttk.Frame(chunk_frame)
        chunk_size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(chunk_size_frame, text="텍스트 청크 크기 (문자 수):").pack(side=tk.LEFT, padx=5)
        chunk_values = [500, 1000, 1500, 2000, 3000, 5000]
        chunk_combo = ttk.Combobox(chunk_size_frame, textvariable=self.chunk_size, 
                                  values=chunk_values, width=10)
        chunk_combo.pack(side=tk.LEFT, padx=5)
        
        # 2) 추가 옵션들
        options_frame = ttk.LabelFrame(parent, text="추가 옵션")
        options_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Checkbutton(options_frame, text="목차 정보 포함 (EPUB만 해당)", 
                       variable=self.include_toc).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Checkbutton(options_frame, text="확장 메타데이터 추가 (파일 경로, 크기, 변환 일시 등)", 
                       variable=self.advanced_metadata).pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Checkbutton(options_frame, text="마지막 사용 경로 저장", 
                       variable=self.save_last_paths).pack(anchor=tk.W, padx=10, pady=2)
        
        # 3) 병합 옵션
        merge_frame = ttk.LabelFrame(parent, text="병합 옵션")
        merge_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Checkbutton(merge_frame, text="모든 문서 파일을 하나의 출력 파일로 병합", 
                       variable=self.merge_output).pack(anchor=tk.W, padx=10, pady=2)
        
        merge_name_frame = ttk.Frame(merge_frame)
        merge_name_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(merge_name_frame, text="병합 파일 이름:").pack(side=tk.LEFT, padx=(0, 5))
        self.merge_name_entry = ttk.Entry(merge_name_frame, textvariable=self.merge_filename, width=30)
        self.merge_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 4) 디버그 옵션 추가
        debug_frame = ttk.LabelFrame(parent, text="개발자 옵션")
        debug_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Checkbutton(debug_frame, text="디버그 모드 활성화 (상세 로그 출력)", 
                       variable=self.debug_mode).pack(anchor=tk.W, padx=10, pady=2)

    def input_mode_changed(self):
        """입력 모드(파일/폴더) 변경 시 UI 업데이트"""
        mode = self.input_mode.get()
        
        if mode == "files":
            # 파일 선택 모드 활성화
            self.folder_frame.pack_forget()
            self.files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 선택된 파일 목록이 있다면 표시
            self.update_file_listbox()
            
        else:  # folder mode
            # 폴더 선택 모드 활성화
            self.files_frame.pack_forget()
            self.folder_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 이미 선택된 파일이 있을 경우 확인 메시지
            if self.document_files and messagebox.askyesno("선택된 파일 초기화", 
                                                 "폴더 모드로 전환합니다. 현재 선택된 파일 목록을 초기화할까요?"):
                self.document_files = []
                self.update_file_listbox()
                self.folder_files_label.config(text="발견된 파일: 0개")
    
    def update_file_listbox(self):
        """파일 목록 리스트박스 업데이트"""
        self.file_listbox.delete(0, tk.END)
        for file in self.document_files:
            self.file_listbox.insert(tk.END, os.path.basename(file))

    def select_files(self):
        """파일 선택 대화상자를 표시합니다."""
        files = filedialog.askopenfilenames(
            title="변환할 파일 선택",
            filetypes=[("문서 파일", "*.epub *.pdf"), ("EPUB 파일", "*.epub"), ("PDF 파일", "*.pdf"), ("모든 파일", "*.*")]
        )
        
        if files:
            # 선택한 파일 중 지원되는 형식만 필터링
            self.document_files = [f for f in files if f.lower().endswith(('.epub', '.pdf'))]
            
            # 첫 번째 파일의 디렉토리를 입력 폴더로 설정 (아직 설정되지 않은 경우)
            if not self.input_folder and self.document_files:
                self.input_folder = os.path.dirname(self.document_files[0])
                self.input_folder_entry.delete(0, tk.END)
                self.input_folder_entry.insert(0, self.input_folder)
            
            # 파일 목록 업데이트
            self.update_file_listbox()
            
            # 선택된 파일 로그
            self.log(f"📂 {len(self.document_files)}개 파일이 선택되었습니다.", "success")
            
            # 파일 목록 표시 (디버그 모드에서만)
            if self.debug_mode.get() and self.document_files:
                self.log("선택된 파일 목록:", "info")
                for idx, file in enumerate(self.document_files, 1):
                    filename = os.path.basename(file)
                    self.log(f"  {idx}. {filename}")

    def clear_files(self):
        """선택된 파일 목록 초기화"""
        if self.document_files:
            if messagebox.askyesno("파일 목록 초기화", "선택된 모든 파일을 목록에서 제거하시겠습니까?"):
                self.document_files = []
                self.update_file_listbox()
                self.log("📄 파일 목록이 초기화되었습니다.", "info")

    def select_input_folder(self):
        """입력 폴더 선택"""
        folder_path = filedialog.askdirectory(title="문서 폴더 선택")
        if folder_path:
            self.input_folder = folder_path
            self.input_folder_entry.delete(0, tk.END)
            self.input_folder_entry.insert(0, folder_path)
            self.log(f"📁 입력 폴더가 설정되었습니다: {folder_path}", "info")

    def find_files_in_folder(self):
        """입력 폴더에서 EPUB/PDF 파일 찾기"""
        self.input_folder = self.input_folder_entry.get().strip()
        
        if not self.input_folder or not os.path.isdir(self.input_folder):
            messagebox.showwarning("경고", "유효한 입력 폴더를 먼저 선택해주세요.")
            return
            
        # 폴더 내 파일 검색
        self.document_files = []
        self.search_docs_in_folder(self.input_folder)
        
        # 결과 표시
        self.folder_files_label.config(text=f"발견된 파일: {len(self.document_files)}개")
        
        if self.document_files:
            self.log(f"📚 {len(self.document_files)}개의 EPUB/PDF 파일을 발견했습니다.", "success")
            # 디버그 모드에서 파일 목록 표시
            if self.debug_mode.get():
                self.log("발견된 파일 목록:", "info")
                for idx, file in enumerate(self.document_files, 1):
                    filename = os.path.basename(file)
                    self.log(f"  {idx}. {filename}")
        else:
            self.log("⚠️ 폴더에서 EPUB/PDF 파일을 찾을 수 없습니다.", "warning")

    def select_output_folder(self):
        """출력 폴더 선택"""
        folder_path = filedialog.askdirectory(title="출력 폴더 선택")
        if folder_path:
            self.output_folder = folder_path
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folder_path)
            self.log(f"📁 출력 폴더가 설정되었습니다: {folder_path}", "info")

    def search_docs_in_folder(self, folder):
        """해당 폴더(하위 폴더 포함) 내의 모든 EPUB/PDF 파일을 찾아 self.document_files에 추가"""
        count_before = len(self.document_files)
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith((".epub", ".pdf")):
                    self.document_files.append(os.path.join(root, file))
        
        count_added = len(self.document_files) - count_before
        if count_added > 0:
            self.log(f"📚 입력 폴더에서 {count_added}개의 파일이 추가되었습니다.", "info")

    ############################################################################
    # 마지막 경로 저장/로드
    ############################################################################
    def save_paths(self):
        """마지막 사용 경로 저장"""
        try:
            config = {
                "input_folder": self.input_folder,
                "output_folder": self.output_folder
            }
            
            # 프로그램 디렉토리에 설정 파일 저장
            config_dir = os.path.join(os.path.expanduser("~"), ".epub_converter")
            os.makedirs(config_dir, exist_ok=True)
            
            config_path = os.path.join(config_dir, "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False)
        except Exception as e:
            self.log(f"⚠️ 설정 저장 중 오류 발생: {e}", "warning")
    
    def load_last_paths(self):
        """마지막 사용 경로 로드"""
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".epub_converter", "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                self.input_folder = config.get("input_folder", "")
                self.output_folder = config.get("output_folder", "")
        except Exception as e:
            self.log(f"⚠️ 설정 로드 중 오류 발생: {e}", "warning")

    ############################################################################
    # 변환 시작 / 취소
    ############################################################################
    def start_conversion(self):
        # 입력 방식에 따라 필요한 변수 업데이트
        if self.input_mode.get() == "folder":
            self.input_folder = self.input_folder_entry.get().strip()
            
            # 폴더에서 아직 파일을 검색하지 않았다면
            if not self.document_files:
                self.find_files_in_folder()
        
        self.output_folder = self.output_folder_entry.get().strip()
        
        # 경로 저장
        if self.save_last_paths.get():
            self.save_paths()

        # 파일 검증
        if not self.document_files:
            messagebox.showwarning("경고", "변환할 파일이 없습니다. 파일을 선택하거나 폴더에서 파일을 검색해주세요.")
            return
        
        # 출력 폴더 검증
        if not self.output_folder:
            messagebox.showwarning("경고", "출력 폴더를 선택해주세요.")
            return

        # 변환 시작
        self.is_converting = True
        self.stop_flag = False
        self.convert_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.progress_bar["value"] = 0
        self.progress_percent.config(text="0%")
        self.progress_status.config(text="변환 중...")
        
        self.log("🔄 변환 작업을 시작합니다...", "info")
        
        if self.merge_output.get() and len(self.document_files) > 1:
            self.log(f"📦 {len(self.document_files)}개의 파일을 하나로 병합합니다.", "info")

        threading.Thread(target=self.convert_process, daemon=True).start()

    def stop_conversion(self):
        if self.is_converting:
            self.stop_flag = True
            self.log("⚠️ 사용자가 변환 중단을 요청했습니다. 현재 작업 이후 중단됩니다...", "warning")
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress_status.config(text="중단 중...")

    ############################################################################
    # 변환 스레드
    ############################################################################
    def convert_process(self):
        total_files = len(self.document_files)
        self.log(f"📚 총 {total_files}개의 문서 파일 변환을 시작합니다.\n", "info")
        
        # 병합 옵션이 켜져 있는 경우를 위한 변수
        merged_data = None
        if self.merge_output.get() and len(self.document_files) > 1:
            if self.gpt_optimized.get():
                merged_data = {
                    'metadata': {
                        'title': f"병합된 문서 파일 ({total_files}개)",
                        'creator': "Document to JSON Converter",
                        'merged_count': total_files,
                        'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    'chunks': [],
                    'total_chunks': 0,
                    'merged_files': [],
                    'gpt_knowledge': True,
                    'format_version': "2.0",
                    'chunked': True
                }
            else:
                merged_data = {
                    'metadata': {
                        'title': f"병합된 문서 파일 ({total_files}개)",
                        'creator': "Document to JSON Converter",
                        'merged_count': total_files,
                        'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    'chapters': [],
                    'total_chapters': 0,
                    'merged_files': [],
                    'gpt_knowledge': True,
                    'format_version': "1.0",
                    'chunked': False
                }

        for idx, doc_file in enumerate(self.document_files, start=1):
            if self.stop_flag:
                break

            file_ext = os.path.splitext(doc_file)[1].lower()
            file_type = "EPUB" if file_ext == ".epub" else "PDF"
            base_name = os.path.splitext(os.path.basename(doc_file))[0]
            
            self.log(f"[{idx}/{total_files}] 📖 변환 중: {doc_file}")
            self.progress_status.config(text=f"변환 중... ({idx}/{total_files})")
            
            # 변환 함수 호출 - 통합 함수 사용
            data, error = file_to_json(
                doc_file, 
                chunk_size=self.chunk_size.get(),
                include_toc=self.include_toc.get(),
                advanced_metadata=self.advanced_metadata.get(),
                gpt_optimized=self.gpt_optimized.get()
            )
            
            if error:
                self.log(f"❌ 변환 실패: {error}\n", "error")
                continue
                
            # 디버그 모드에서 상세 정보 로깅
            if self.debug_mode.get():
                if file_type == "EPUB":
                    chunks_count = len(data.get('chunks', [])) or len(data.get('chapters', []))
                    self.log(f"📊 데이터 통계: {chunks_count}개 항목 추출됨 (타입: {file_type})", "info")
                else:  # PDF
                    chunks_count = len(data.get('chunks', [])) or len(data.get('pages', []))
                    self.log(f"📊 데이터 통계: {chunks_count}개 페이지/청크 추출됨 (타입: {file_type})", "info")
                self.log(f"📋 변환된 구조: {', '.join(data.keys())}", "info")
                
            # 병합 로직
            if self.merge_output.get() and merged_data is not None:
                if 'chunks' in data and 'chunks' in merged_data:
                    # 기존 청크 인덱스 조정
                    chunk_offset = len(merged_data['chunks'])
                    for i, chunk in enumerate(data['chunks']):
                        # 오프셋 적용해서 새 ID 생성 (파일 타입에 따라 ID 형식 다름)
                        prefix = "ch" if file_type == "EPUB" else "pg"
                        new_id = f"{prefix}{chunk_offset + i + 1}"
                        chunk['id'] = new_id
                        # 파일 소스 정보 추가
                        chunk['source_file'] = base_name
                        merged_data['chunks'].append(chunk)
                    
                    merged_data['total_chunks'] += len(data['chunks'])
                    
                elif 'chapters' in data and 'chapters' in merged_data:
                    merged_data['chapters'].extend(data['chapters'])
                    merged_data['total_chapters'] += len(data['chapters'])
                elif 'pages' in data and 'chapters' in merged_data:
                    # PDF 페이지를 EPUB 챕터처럼 처리
                    for page in data['pages']:
                        merged_data['chapters'].append(page['content'])
                    merged_data['total_chapters'] += len(data['pages'])
                
                # 병합된 파일 목록에 추가
                merged_data['merged_files'].append({
                    'file_name': os.path.basename(doc_file),
                    'file_type': file_type,
                    'title': data['metadata']['title'],
                    'creator': data['metadata']['creator']
                })
                
                self.log(f"✅ {base_name} 파일이 병합 데이터에 추가되었습니다.", "success")
            
            # 개별 파일 저장
            if not self.merge_output.get() or total_files == 1:
                try:
                    # 출력 포맷에 따라 처리
                    if self.output_format.get() == "json":
                        output_ext = ".json"
                        output_filename = base_name + output_ext
                        output_path = os.path.join(self.output_folder, output_filename)
                        
                        # JSON 직렬화 - 사용자 정의 인코더 사용
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False, cls=CustomJSONEncoder)
                            
                            # 디버그 모드일 경우 파일 크기 체크
                            if self.debug_mode.get():
                                f.flush()  # 파일에 변경사항 즉시 기록
                                file_size = os.path.getsize(output_path)
                                self.log(f"  - 생성된 파일 크기: {file_size / 1024:.2f} KB", "info")
                        
                    elif self.output_format.get() == "markdown":
                        output_ext = ".md"
                        output_filename = base_name + output_ext
                        output_path = os.path.join(self.output_folder, output_filename)
                        
                        success, error = convert_to_markdown(data, output_path)
                        if not success:
                            self.log(f"❌ 마크다운 변환 실패: {error}", "error")
                            continue
                            
                    elif self.output_format.get() == "text":
                        output_ext = ".txt"
                        output_filename = base_name + output_ext
                        output_path = os.path.join(self.output_folder, output_filename)
                        
                        success, error = convert_to_text(data, output_path)
                        if not success:
                            self.log(f"❌ 텍스트 변환 실패: {error}", "error")
                            continue
                            
                    self.log(f"✅ 파일 변환 완료: {output_filename}", "success")
                    
                except Exception as e:
                    self.log(f"❌ 파일 저장 실패: {str(e)}", "error")
                    if self.debug_mode.get():
                        import traceback
                        self.log(f"상세 오류: {traceback.format_exc()}", "error")
            
            # 진행 상황 업데이트
            progress_value = (idx / total_files) * 100
            self.progress_bar["value"] = progress_value
            self.progress_percent.config(text=f"{int(progress_value)}%")
            self.update_idletasks()
        
        # 병합 파일 저장 (병합 옵션이 켜져 있고 여러 파일이 있는 경우)
        if self.merge_output.get() and merged_data is not None and len(self.document_files) > 1 and not self.stop_flag:
            try:
                self.progress_status.config(text="병합 파일 생성 중...")
                merge_filename = self.merge_filename.get()
                
                # 출력 포맷에 따라 처리
                if self.output_format.get() == "json":
                    if not merge_filename.endswith('.json'):
                        merge_filename += '.json'
                    
                    output_path = os.path.join(self.output_folder, merge_filename)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(merged_data, f, indent=4, ensure_ascii=False, cls=CustomJSONEncoder)
                    
                elif self.output_format.get() == "markdown":
                    if not merge_filename.endswith('.md'):
                        merge_filename += '.md'
                    
                    output_path = os.path.join(self.output_folder, merge_filename)
                    success, error = convert_to_markdown(merged_data, output_path)
                    if not success:
                        self.log(f"❌ 병합 마크다운 변환 실패: {error}", "error")
                
                elif self.output_format.get() == "text":
                    if not merge_filename.endswith('.txt'):
                        merge_filename += '.txt'
                    
                    output_path = os.path.join(self.output_folder, merge_filename)
                    success, error = convert_to_text(merged_data, output_path)
                    if not success:
                        self.log(f"❌ 병합 텍스트 변환 실패: {error}", "error")
                
                self.log(f"✅ 병합된 파일 저장 완료: {merge_filename}", "success")
                
            except Exception as e:
                self.log(f"❌ 병합 파일 저장 중 오류 발생: {str(e)}", "error")
                if self.debug_mode.get():
                    import traceback
                    self.log(f"상세 오류: {traceback.format_exc()}", "error")
        
        # 작업 완료 메시지 및 UI 상태 업데이트
        if self.stop_flag:
            self.log("⚠️ 사용자 요청으로 일부 파일만 변환되었습니다.", "warning")
            self.progress_status.config(text="중단됨")
        else:
            self.log("🎉 모든 변환 작업이 완료되었습니다!", "success")
            self.progress_status.config(text="완료")
            self.progress_bar["value"] = 100
            self.progress_percent.config(text="100%")
        
        # 완료 시 파일 탐색기에서 출력 폴더 열기 옵션 제공
        if not self.stop_flag:
            if messagebox.askyesno("변환 완료", f"변환이 완료되었습니다.\n출력 폴더({self.output_folder})를 탐색기에서 열까요?"):
                try:
                    if sys.platform == 'win32':
                        os.startfile(self.output_folder)
                    elif sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', self.output_folder])
                    else:  # linux
                        subprocess.run(['xdg-open', self.output_folder])
                except Exception as e:
                    self.log(f"⚠️ 폴더 열기 실패: {str(e)}", "warning")
        
        # UI 상태 복원
        self.is_converting = False
        self.stop_flag = False
        self.convert_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def log(self, message, tag=None):
        """로그 메시지를 로그 창에 추가합니다."""
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)

###############################################################################
# 메인 실행
###############################################################################
if __name__ == "__main__":
    app = DoctoJSONApp()
    app.mainloop()
