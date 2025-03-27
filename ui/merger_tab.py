# ui/merger_tab.py

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class MergerTab:
    """병합 기능 전용 탭 관련 기능을 담당하는 클래스"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_merger_tab(parent)
    
    def setup_merger_tab(self, parent):
        """병합 탭 위젯 구성"""
        # 1) 입력 설정 프레임
        input_frame = ttk.LabelFrame(parent, text="입력 설정")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # 병합 모드 선택
        mode_frame = ttk.Frame(input_frame)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(mode_frame, text="병합 모드:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.app.merge_mode = tk.StringVar(value="directory")
        ttk.Radiobutton(mode_frame, text="폴더 내 파일 병합", 
                    variable=self.app.merge_mode, value="directory",
                    command=self.merge_mode_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="선택한 파일들 병합", 
                    variable=self.app.merge_mode, value="files",
                    command=self.merge_mode_changed).pack(side=tk.LEFT, padx=5)
        
        # 폴더 선택 프레임 (폴더 모드용)
        self.app.merge_dir_frame = ttk.Frame(input_frame)
        self.app.merge_dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 폴더 경로 입력 행
        folder_path_frame = ttk.Frame(self.app.merge_dir_frame)
        folder_path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_path_frame, text="병합할 파일이 있는 폴더:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.merge_dir_entry = ttk.Entry(folder_path_frame, width=50)
        self.app.merge_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(folder_path_frame, text="찾아보기", 
                command=self.select_merge_directory).pack(side=tk.LEFT)
        
        # 파일 패턴 선택 (폴더 모드용) - 수정된 부분: 콤보박스에서 라디오 버튼으로 변경
        pattern_frame = ttk.LabelFrame(self.app.merge_dir_frame, text="파일 유형 선택")
        pattern_frame.pack(fill=tk.X, pady=5)
        
        self.app.file_pattern = tk.StringVar(value="*.txt")
        ttk.Radiobutton(pattern_frame, text="텍스트 파일 (*.txt)", 
                    variable=self.app.file_pattern, value="*.txt").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(pattern_frame, text="Python 파일 (*.py)", 
                    variable=self.app.file_pattern, value="*.py").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(pattern_frame, text="C/C++ 파일 (*.c/*.cpp)", 
                    variable=self.app.file_pattern, value="*.c").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(pattern_frame, text="헤더 파일 (*.h)", 
                    variable=self.app.file_pattern, value="*.h").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(pattern_frame, text="JSON 파일 (*.json)", 
                    variable=self.app.file_pattern, value="*.json").pack(anchor=tk.W, padx=20, pady=2)
        
        # 폴더 구조 포함 옵션 (폴더 모드용)
        folder_struct_frame = ttk.Frame(self.app.merge_dir_frame)
        folder_struct_frame.pack(fill=tk.X, pady=5)
        
        self.app.include_folder_structure = tk.BooleanVar(value=True)
        ttk.Checkbutton(folder_struct_frame, text="병합 시 폴더 구조 정보 포함", 
                    variable=self.app.include_folder_structure).pack(anchor=tk.W, padx=(20, 0))
        
        # 하위 폴더 포함 옵션 (폴더 모드용)
        recursive_frame = ttk.Frame(self.app.merge_dir_frame)
        recursive_frame.pack(fill=tk.X, pady=5)
        
        self.app.recursive_search = tk.BooleanVar(value=True)
        ttk.Checkbutton(recursive_frame, text="하위 폴더의 파일도 모두 포함", 
                    variable=self.app.recursive_search).pack(anchor=tk.W, padx=(20, 0))
        
        # 파일 선택 프레임 (파일 모드용)
        self.app.merge_files_frame = ttk.Frame(input_frame)
        # 초기에는 숨김 상태
        
        file_buttons_frame = ttk.Frame(self.app.merge_files_frame)
        file_buttons_frame.pack(fill=tk.X, pady=5)
        ttk.Button(file_buttons_frame, text="파일 선택", 
                command=self.select_merge_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="목록 초기화", 
                command=self.clear_merge_files).pack(side=tk.LEFT)
        
        # 선택된 파일 목록
        file_list_frame = ttk.Frame(self.app.merge_files_frame)
        file_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(file_list_frame, text="병합할 파일 목록:").pack(anchor=tk.W)
        
        file_list_scroll = ttk.Scrollbar(file_list_frame)
        file_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.app.merge_file_listbox = tk.Listbox(file_list_frame, height=6, 
                                        yscrollcommand=file_list_scroll.set)
        self.app.merge_file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_list_scroll.config(command=self.app.merge_file_listbox.yview)
        
        # 2) 출력 설정 프레임
        output_frame = ttk.LabelFrame(parent, text="출력 설정")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # 출력 폴더 설정
        out_folder_frame = ttk.Frame(output_frame)
        out_folder_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(out_folder_frame, text="출력 폴더:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.merge_output_folder_entry = ttk.Entry(out_folder_frame, width=50)
        self.app.merge_output_folder_entry.insert(0, os.path.expanduser("~"))
        self.app.merge_output_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(out_folder_frame, text="찾아보기", 
                command=self.select_merge_output_folder).pack(side=tk.LEFT)
        
        # 출력 파일명 설정
        out_file_frame = ttk.Frame(output_frame)
        out_file_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(out_file_frame, text="출력 파일 이름:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.merge_output_filename = tk.StringVar(value="merged_output")
        self.app.merge_output_filename_entry = ttk.Entry(out_file_frame, textvariable=self.app.merge_output_filename, width=30)
        self.app.merge_output_filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 출력 형식 선택
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(format_frame, text="출력 형식:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.merge_output_format = tk.StringVar(value="txt")
        ttk.Radiobutton(format_frame, text="텍스트 (.txt)", 
                    variable=self.app.merge_output_format, value="txt").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="JSON (.json)", 
                    variable=self.app.merge_output_format, value="json").pack(side=tk.LEFT, padx=5)
        
        # 파일명 포함 옵션
        include_frame = ttk.Frame(output_frame)
        include_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.app.include_filenames = tk.BooleanVar(value=True)
        ttk.Checkbutton(include_frame, text="병합된 파일에 원본 파일명 포함", 
                    variable=self.app.include_filenames).pack(anchor=tk.W)
        
        # 탭 초기화 후 모드에 따른 UI 조정
        self.merge_mode_changed()

    
    def merge_mode_changed(self):
        """병합 모드(폴더/파일) 변경 시 UI 업데이트"""
        mode = self.app.merge_mode.get()
        if mode == "directory":
            # 폴더 모드 활성화
            self.app.merge_files_frame.pack_forget()
            self.app.merge_dir_frame.pack(fill=tk.X, padx=10, pady=5)
        else:  # files mode
            # 파일 모드 활성화
            self.app.merge_dir_frame.pack_forget()
            self.app.merge_files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def select_merge_directory(self):
        """병합할 파일이 있는 폴더 선택"""
        folder_path = filedialog.askdirectory(title="병합할 파일이 있는 폴더 선택")
        if folder_path:
            self.app.merge_dir_entry.delete(0, tk.END)
            self.app.merge_dir_entry.insert(0, folder_path)
    
    def select_merge_files(self):
        """병합할 파일들 선택"""
        files = filedialog.askopenfilenames(
            title="병합할 파일 선택",
            filetypes=[
                ("모든 파일", "*.*"),
                ("텍스트 파일", "*.txt"),
                ("JSON 파일", "*.json"),
                ("Python 파일", "*.py"),
                ("C 파일", "*.c *.h"),
                ("마크다운 파일", "*.md")
            ]
        )
        
        if files:
            self.app.merge_files = list(files)
            self.update_merge_file_listbox()
    
    def clear_merge_files(self):
        """병합 파일 목록 초기화"""
        self.app.merge_files = []
        self.update_merge_file_listbox()
    
    def update_merge_file_listbox(self):
        """병합 파일 목록 리스트박스 업데이트"""
        self.app.merge_file_listbox.delete(0, tk.END)
        for file in getattr(self.app, 'merge_files', []):
            self.app.merge_file_listbox.insert(tk.END, os.path.basename(file))
    
    def select_merge_output_folder(self):
        """병합 결과 출력 폴더 선택"""
        folder_path = filedialog.askdirectory(title="출력 폴더 선택")
        if folder_path:
            self.app.merge_output_folder_entry.delete(0, tk.END)
            self.app.merge_output_folder_entry.insert(0, folder_path)
