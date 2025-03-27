# ui/advanced_tab.py
import tkinter as tk
from tkinter import ttk

class AdvancedTab:
    """고급 설정 탭 관련 기능을 담당하는 클래스"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_advanced_tab(parent)
    
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
        chunk_combo = ttk.Combobox(chunk_size_frame, textvariable=self.app.chunk_size,
                               values=chunk_values, width=10)
        chunk_combo.pack(side=tk.LEFT, padx=5)
        
        # 2) 추가 옵션들
        options_frame = ttk.LabelFrame(parent, text="추가 옵션")
        options_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Checkbutton(options_frame, text="목차 정보 포함 (EPUB만 해당)",
                      variable=self.app.include_toc).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="확장 메타데이터 추가 (파일 경로, 크기, 변환 일시 등)",
                      variable=self.app.advanced_metadata).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="마지막 사용 경로 저장",
                      variable=self.app.save_last_paths).pack(anchor=tk.W, padx=10, pady=2)
        
        # 3) 병합 옵션
        merge_frame = ttk.LabelFrame(parent, text="병합 옵션")
        merge_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Checkbutton(merge_frame, text="모든 문서 파일을 하나의 출력 파일로 병합",
                      variable=self.app.merge_output).pack(anchor=tk.W, padx=10, pady=2)
        
        merge_name_frame = ttk.Frame(merge_frame)
        merge_name_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Label(merge_name_frame, text="병합 파일 이름:").pack(side=tk.LEFT, padx=(0, 5))
        self.app.merge_name_entry = ttk.Entry(merge_name_frame, textvariable=self.app.merge_filename, width=30)
        self.app.merge_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 4) 디버그 옵션 추가
        debug_frame = ttk.LabelFrame(parent, text="개발자 옵션")
        debug_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Checkbutton(debug_frame, text="디버그 모드 활성화 (상세 로그 출력)",
                      variable=self.app.debug_mode).pack(anchor=tk.W, padx=10, pady=2)
