# ui/main_app.py
import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import platform
import subprocess
import sys

from utils.module_checker import check_required_modules
from utils.json_encoder import CustomJSONEncoder
from converters.common import file_to_json
from converters.exporters import convert_to_markdown, convert_to_text, save_json_file
from converters.file_merger import merge_text_files, merge_code_files, merge_json_files, merge_documents

from ui.basic_tab import BasicTab
from ui.advanced_tab import AdvancedTab
from ui.merger_tab import MergerTab  # 새로 추가된 병합 탭

class DoctoJSONApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 필요한 모듈 확인
        check_required_modules()
        
        self.title("Lexi Convert by El Fenomeno")
        self.geometry("800x850")
        self.resizable(True, True)
        
        # 경로 및 작업 상태 변수 초기화
        self.input_folder = ""  # 파일들이 들어있는 폴더
        self.output_folder = ""  # JSON 파일을 저장할 폴더
        self.document_files = []  # 변환할 파일 목록
        self.is_converting = False
        self.stop_flag = False  # 변환 중단 플래그
        
        # 병합 관련 변수 (NEW)
        self.merge_files = []   # 병합할 파일 목록
        self.is_merging = False  # 병합 작업 중 플래그
        self.merge_mode = tk.StringVar(value="directory")  # 병합 모드 (directory 또는 files)
        self.file_pattern = tk.StringVar(value="*.txt")    # 병합할 파일 패턴
        self.include_filenames = tk.BooleanVar(value=True) # 파일명 포함 여부
        self.merge_output_format = tk.StringVar(value="txt") # 병합 출력 포맷
        
        # 입력 모드 선택 변수 (파일 또는 폴더)
        self.input_mode = tk.StringVar(value="files")
        
        # 설정 변수들
        self.chunk_size = tk.IntVar(value=1000)
        self.include_toc = tk.BooleanVar(value=True)
        self.advanced_metadata = tk.BooleanVar(value=True)
        self.gpt_optimized = tk.BooleanVar(value=False)
        self.output_format = tk.StringVar(value="json")  # json, markdown, text
        self.merge_output = tk.BooleanVar(value=False)  # 모든 파일을 하나로 병합
        self.merge_filename = tk.StringVar(value="merged_output")
        
        # 디버그 모드 추가
        self.debug_mode = tk.BooleanVar(value=False)
        
        # 마지막 경로 저장
        self.save_last_paths = tk.BooleanVar(value=True)
        
        # 애플리케이션 아이콘 설정 (작업 표시줄 포함)
        self.setup_icon()
        
        # 테마 및 스타일 설정
        self.setup_styles()
        
        # UI 위젯 생성
        self.create_widgets()
        
        # 마지막 경로 로드 - UI 초기화 후 호출해야 오류가 발생하지 않음
        try:
            self.load_last_paths()
        except Exception as e:
            print(f"설정 로드 중 오류 발생: {e}")
    
    def setup_icon(self):
        """애플리케이션 아이콘 설정"""
        try:
            from PIL import Image, ImageTk
            
            # 아이콘 파일 경로
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "assets", "images", "Lexi_Convert.png")
            
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
        
        # 탭 생성
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="파일 바꾸기")
        
        # 고급 탭
        advanced_tab = ttk.Frame(notebook)
        notebook.add(advanced_tab, text="바꾸기 설정")
        
        # 병합 탭 (NEW)
        merger_tab = ttk.Frame(notebook)
        notebook.add(merger_tab, text="파일 합치기")
        
        # 탭 초기화
        self.basic_tab_ui = BasicTab(basic_tab, self)
        self.advanced_tab_ui = AdvancedTab(advanced_tab, self)
        self.merger_tab_ui = MergerTab(merger_tab, self)  # 새로운 병합 탭 초기화
        
        # 공통 하단 영역: 변환/취소 버튼, 진행 바, 로그 출력
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 버튼 영역
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.convert_btn = ttk.Button(button_frame, text="바꾸기 시작", 
                                     style="Primary.TButton", command=self.start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.cancel_btn = ttk.Button(button_frame, text="바꾸기 중단", 
                                   command=self.stop_conversion, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 병합 버튼 추가 (NEW)
        self.merge_btn = ttk.Button(button_frame, text="합치기 시작", 
                                   style="Primary.TButton", command=self.start_merger)
        self.merge_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
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
        log_frame = ttk.LabelFrame(bottom_frame, text="로그")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15, 
                                              wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("info", foreground="blue")
        self.log_text.tag_configure("warning", foreground="orange")
        
        # 초기 로그 메시지
        self.log("✨ Lexi Convert가 준비되었습니다.", "info")
        self.log("문서 변환 또는 파일 병합 기능을 사용할 수 있습니다.")
        
        # 초기 모드에 따라 UI 조정
        self.input_mode_changed()
    
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
            filetypes=[
                # ✅ "문서 파일" 목록에 html, htm 추가
                ("문서 파일", "*.epub *.pdf *.html *.htm"),
                ("HTML 파일", "*.html *.htm"), # ✅ HTML 파일 유형 추가
                ("EPUB 파일", "*.epub"),
                ("PDF 파일", "*.pdf"),
                ("모든 파일", "*.*")
            ]
        )
        
        if files:
            # 선택한 파일 중 지원되는 형식만 필터링
            self.document_files = [f for f in files if f.lower().endswith(('.epub', '.pdf', '.html', '.htm'))]

            
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
                    self.log(f" {idx}. {filename}")
    
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
                    self.log(f" {idx}. {filename}")
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
                if file.lower().endswith((".epub", ".pdf", ".html", ".htm")):
                    self.document_files.append(os.path.join(root, file))
        
        count_added = len(self.document_files) - count_before
        if count_added > 0:
            self.log(f"📚 입력 폴더에서 {count_added}개의 파일이 추가되었습니다.", "info")
    
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
                
                # UI가 이미 생성되었다면 경로 표시 업데이트
                if hasattr(self, 'input_folder_entry'):
                    self.input_folder_entry.delete(0, tk.END)
                    self.input_folder_entry.insert(0, self.input_folder)
                
                if hasattr(self, 'output_folder_entry'):
                    self.output_folder_entry.delete(0, tk.END)
                    self.output_folder_entry.insert(0, self.output_folder)
        except Exception as e:
            print(f"⚠️ 설정 로드 중 오류 발생: {e}")
    
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
                        
                        success, error = save_json_file(data, output_path)
                        if not success:
                            self.log(f"❌ JSON 저장 실패: {error}", "error")
                            continue
                        
                        # 디버그 모드일 경우 파일 크기 체크
                        if self.debug_mode.get():
                            file_size = os.path.getsize(output_path)
                            self.log(f" - 생성된 파일 크기: {file_size / 1024:.2f} KB", "info")
                    
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
                    
                    success, error = save_json_file(merged_data, output_path)
                    if not success:
                        self.log(f"❌ 병합 JSON 저장 실패: {error}", "error")
                
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
                self.open_file_explorer(self.output_folder)
        
        # UI 상태 복원
        self.is_converting = False
        self.stop_flag = False
        self.convert_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
    
    def start_merger(self):
        """병합 작업 시작"""
        # 이미 작업 중이면 취소
        if self.is_converting or self.is_merging:
            messagebox.showwarning("경고", "이미 진행 중인 작업이 있습니다. 완료 후 다시 시도하세요.")
            return
        
        # 병합 모드에 따라 파일 목록 확인
        if self.merge_mode.get() == "directory":
            directory_path = self.merge_dir_entry.get().strip()
            if not directory_path or not os.path.isdir(directory_path):
                messagebox.showwarning("경고", "유효한 폴더 경로를 선택해주세요.")
                return
        else:  # files 모드
            if not hasattr(self, 'merge_files') or not self.merge_files:
                messagebox.showwarning("경고", "병합할 파일을 선택해주세요.")
                return
        
        # 출력 폴더와 파일명 확인
        output_folder = self.merge_output_folder_entry.get().strip()
        if not output_folder:
            messagebox.showwarning("경고", "출력 폴더를 지정해주세요.")
            return
        
        filename = self.merge_output_filename.get().strip()
        if not filename:
            messagebox.showwarning("경고", "출력 파일 이름을 지정해주세요.")
            return
        
        # 확장자가 없으면 추가
        file_ext = "." + self.merge_output_format.get().lower()
        if not filename.lower().endswith(file_ext):
            filename += file_ext
        
        # 출력 경로 구성
        output_path = os.path.join(output_folder, filename)
        
        # 출력 디렉토리 생성 (필요한 경우)
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                messagebox.showerror("오류", f"출력 디렉토리 생성 실패: {str(e)}")
                return
        
        # UI 상태 업데이트
        self.is_merging = True
        self.convert_btn.config(state=tk.DISABLED)
        self.merge_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_bar["value"] = 0
        self.progress_percent.config(text="0%")
        self.progress_status.config(text="병합 준비 중...")
        
        # 로그 초기화 및 시작 메시지
        self.log_text.delete("1.0", tk.END)
        self.log("🔄 파일 병합 작업을 시작합니다...", "info")
        
        # 스레드로 병합 작업 실행
        threading.Thread(target=self.merge_process, daemon=True).start()

    
    def merge_process(self):
        """파일 병합 프로세스를 실행"""
        try:
            # 병합 모드에 따라 처리
            if self.merge_mode.get() == "directory":
                directory_path = self.merge_dir_entry.get().strip()
                # 출력 폴더와 파일 이름 조합
                output_folder = self.merge_output_folder_entry.get().strip()
                filename = self.merge_output_filename.get().strip()
                file_ext = "." + self.merge_output_format.get().lower()
                
                # 확장자가 없으면 추가
                if not filename.lower().endswith(file_ext):
                    filename += file_ext
                
                output_path = os.path.join(output_folder, filename)
                file_pattern = self.file_pattern.get().strip()
                include_filenames = self.include_filenames.get()
                include_folder_structure = self.include_folder_structure.get()
                recursive = self.recursive_search.get()
                
                self.log(f"📁 폴더: {directory_path}")
                self.log(f"🔍 파일 패턴: {file_pattern}")
                if recursive:
                    self.log("🔍 하위 폴더 포함: 예")
                self.progress_status.config(text="파일 검색 중...")
                
                # 수정된 부분: 먼저 파일 패턴에 따라 처리 방법 결정
                if file_pattern.lower().endswith(".json"):
                    self.log("📊 JSON 파일 병합 중...")
                    success, message = merge_json_files(directory_path, output_path, recursive)
                elif file_pattern.lower().endswith((".py", ".c", ".h", ".cpp", ".cs")):
                    self.log(f"📝 코드 파일 병합 중... ({file_pattern})")
                    file_ext = os.path.splitext(file_pattern)[1]  # *.py -> .py
                    success, message = merge_code_files(directory_path, output_path, file_ext, 
                                                    include_filenames, include_folder_structure, 
                                                    recursive)
                else:
                    # 기본 텍스트 파일 병합
                    self.log(f"📄 텍스트 파일 병합 중... ({file_pattern})")
                    success, message = merge_text_files(directory_path, output_path, file_pattern, 
                                                    include_filenames, include_folder_structure, 
                                                    recursive)
            
            else:  # files 모드
                # 출력 폴더와 파일 이름 조합
                output_folder = self.merge_output_folder_entry.get().strip()
                filename = self.merge_output_filename.get().strip()
                file_ext = "." + self.merge_output_format.get().lower()
                
                # 확장자가 없으면 추가
                if not filename.lower().endswith(file_ext):
                    filename += file_ext
                
                output_path = os.path.join(output_folder, filename)
                self.log(f"📄 선택한 {len(self.merge_files)}개 파일 병합 중...")
                
                # 선택한 파일들 병합
                success, message = merge_documents(self.merge_files, output_path, self.merge_output_format.get())
            
            # 결과 처리
            if success:
                self.log(f"✅ {message}", "success")
                self.progress_bar["value"] = 100
                self.progress_percent.config(text="100%")
                
                # 완료 후 파일 탐색기에서 출력 파일 열기 옵션 제공
                if messagebox.askyesno("병합 완료", f"파일 병합이 완료되었습니다.\n결과 파일을 열어보시겠습니까?"):
                    self.open_file(output_path)
            else:
                self.log(f"❌ {message}", "error")
        
        except Exception as e:
            self.log(f"❌ 병합 중 오류 발생: {str(e)}", "error")
            if self.debug_mode.get():
                import traceback
                self.log(f"상세 오류: {traceback.format_exc()}", "error")
        
        finally:
            # UI 상태 복원
            self.is_merging = False
            self.progress_status.config(text="준비됨")
            self.convert_btn.config(state=tk.NORMAL)
            self.merge_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)


    
    def open_file(self, file_path):
        """파일을 시스템 기본 앱으로 엽니다."""
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            self.log(f"⚠️ 파일 열기 실패: {str(e)}", "warning")
    
    def open_file_explorer(self, path):
        """폴더를 파일 탐색기에서 엽니다."""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', path])
            else:  # linux
                subprocess.run(['xdg-open', path])
        except Exception as e:
            self.log(f"⚠️ 폴더 열기 실패: {str(e)}", "warning")
    
    def log(self, message, tag=None):
        """로그 메시지를 로그 창에 추가합니다."""
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
