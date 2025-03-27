# Lexi Convert

텍스트 문서 파일을 다양한 포맷으로 변환하는 Python 기반 도구입니다.  
EPUB, PDF 등의 문서를 입력받아 JSON, Markdown, Plain Text 형식으로 변환할 수 있습니다.

---

## 📁 프로젝트 구조

```
Python_Lexi_Convert/
├── main.py                # 메인 진입점
├── assets/                # 이미지와 리소스 파일
│   └── images/
│       └── Lexi_Convert.png   # 애플리케이션 아이콘
├── utils/                 # 공통 유틸리티 함수 모음
│   ├── __init__.py
│   ├── json_encoder.py    # CustomJSONEncoder 클래스
│   ├── module_checker.py  # 필요한 모듈 체크 및 설치
│   └── text_utils.py      # 텍스트 전처리 및 유틸 함수
├── converters/            # 문서 포맷 변환 관련 모듈
│   ├── __init__.py
│   ├── epub_converter.py  # EPUB 포맷 변환 처리
│   ├── pdf_converter.py   # PDF 포맷 변환 처리
│   ├── common.py          # 변환 공통 함수들
│   └── exporters.py       # JSON, 마크다운, 텍스트 등 출력 포맷 처리
├── ui/                    # 사용자 인터페이스 관련 코드
│   ├── __init__.py
│   ├── main_app.py        # 전체 UI 메인 앱 구성
│   ├── basic_tab.py       # 기본 설정 탭 UI
│   └── advanced_tab.py    # 고급 설정 탭 UI
└── scripts/               # 빌드 및 배포용 스크립트
    ├── build_portable.bat # 폴더형 실행 파일 빌드 스크립트
    └── build_onefile.bat  # 단일 EXE 실행 파일 빌드 스크립트
```

---

## 🛠️ 주요 기능

- **EPUB, PDF → JSON / Markdown / Plain Text 변환**  
- **텍스트 청크 분할 & 메타데이터 추출**  
- **GPT 컨텍스트 최적화 옵션**  
- **다중 파일 일괄 처리 및 병합**  
- **모듈 자동 설치 / 마지막 경로 저장 / 디버그 모드**

---

## 🔧 필요 요구사항

- Python 3.8 이상  
- ebooklib, beautifulsoup4, pymupdf, pillow

```bash
pip install ebooklib beautifulsoup4 pymupdf pillow
```

---

## 🚀 실행 방법

```bash
python main.py
```

- 처음 실행 시 필요한 패키지가 없으면 자동 설치 여부를 물어봅니다.
- 설치 후 프로그램을 재시작하면 적용됩니다.

---

## 📦 실행 파일 만들기 (PyInstaller)

### 👜 포터블 폴더 형태

```bash
cd scripts
build_portable.bat
```

- dist 폴더 안에 폴더형 실행 파일 생성

### 📁 단일 EXE 파일

```bash
cd scripts
build_onefile.bat
```

- dist 폴더 안에 단일 EXE 파일 생성

---

## 🤝 기여하기

1. Fork → 새 브랜치 생성 → 커밋 → Pull Request 제출  
2. 이슈 등록 후 의견 교환 환영

---

## 📝 라이선스

- 개인·비상업적 용도는 자유롭게 사용  
- 상업적 용도 시 저작자에게 문의 바랍니다

---

## 👨‍💻 제작자

El Fenomeno — Lexi Convert
