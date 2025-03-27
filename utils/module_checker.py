# utils/module_checker.py
import sys
import subprocess
import tkinter.messagebox as messagebox

def check_required_modules():
    """필요한 모듈 체크 및 설치"""
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
