# ui/basic_tab.py
import os
import tkinter as tk
from tkinter import ttk, filedialog

class BasicTab:
    """기본 설정 탭 관련 기능을 담당하는 클래스"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_basic_tab(parent)
    
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
                     variable=self.app.input_mode, value="files",
                     command=self.app.input_mode_changed).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Radiobutton(input_mode_frame, text="폴더 선택",
                     variable=self.app.input_mode, value="folder",
                     command=self.app.input_mode_changed).pack(side=tk.LEFT, padx=5)
        
        # 파일 선택 영역 (개별 파일 선택 모드)
        self.app.files_frame = ttk.Frame(input_frame)
        self.app.files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        file_buttons_frame = ttk.Frame(self.app.files_frame)
        file_buttons_frame.pack(fill=tk.X, pady=5)
        ttk.Button(file_buttons_frame, text="파일 선택",
                 command=self.app.select_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="파일 목록 초기화",
                 command=self.app.clear_files).pack(side=tk.LEFT)
        
        # 선택된 파일 목록
        file_list_frame = ttk.Frame(self.app.files_frame)
        file_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(file_list_frame, text="선택된 파일:").pack(anchor=tk.W)
        file_list_scroll = ttk.Scrollbar(file_list_frame)
        file_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.app.file_listbox = tk.Listbox(file_list_frame, height=6,
                                      yscrollcommand=file_list_scroll.set)
        self.app.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_list_scroll.config(command=self.app.file_listbox.yview)
        
        # 폴더 선택 영역 (폴더 선택 모드)
        self.app.folder_frame = ttk.Frame(input_frame)
        # 처음에는 숨김 상태
        
        folder_select_frame = ttk.Frame(self.app.folder_frame)
        folder_select_frame.pack(fill=tk.X, pady=5)
        ttk.Label(folder_select_frame, text="문서 폴더:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.input_folder_entry = ttk.Entry(folder_select_frame, width=50)
        self.app.input_folder_entry.insert(0, self.app.input_folder)
        self.app.input_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(folder_select_frame, text="찾아보기",
                 command=self.app.select_input_folder).pack(side=tk.LEFT)
        
        # 폴더 내 파일 탐색 버튼
        ttk.Button(self.app.folder_frame, text="폴더 내 모든 EPUB/PDF 파일 찾기",
                 command=self.app.find_files_in_folder).pack(fill=tk.X, pady=5)
        
        # 찾은 파일 정보 표시
        self.app.folder_files_label = ttk.Label(self.app.folder_frame, text="발견된 파일: 0개")
        self.app.folder_files_label.pack(anchor=tk.W, pady=5)
        
        # 2) 출력 부분
        output_frame = ttk.LabelFrame(parent, text="출력 설정")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # 출력 폴더 선택
        out_folder_frame = ttk.Frame(output_frame)
        out_folder_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Label(out_folder_frame, text="출력 폴더:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.output_folder_entry = ttk.Entry(out_folder_frame, width=50)
        self.app.output_folder_entry.insert(0, self.app.output_folder)
        self.app.output_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(out_folder_frame, text="찾아보기",
                 command=self.app.select_output_folder).pack(side=tk.LEFT)
        
        # 출력 포맷 선택
        format_frame = ttk.LabelFrame(output_frame, text="출력 포맷")
        format_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Radiobutton(format_frame, text="JSON (기본)",
                      variable=self.app.output_format, value="json").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(format_frame, text="마크다운 (.md)",
                      variable=self.app.output_format, value="markdown").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(format_frame, text="텍스트 (.txt)",
                      variable=self.app.output_format, value="text").pack(anchor=tk.W, padx=10, pady=2)
        
        # GPT 최적화 옵션
        gpt_frame = ttk.Frame(output_frame)
        gpt_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Checkbutton(gpt_frame, text="GPT 분석에 최적화된 형식으로 변환 (청크 분할, 인덱싱 적용)",
                      variable=self.app.gpt_optimized).pack(anchor=tk.W)
