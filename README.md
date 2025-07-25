# Lexi Convert

텍스트 문서 파일을 다양한 포맷으로 변환하는 Python 기반 도구입니다.
EPUB, PDF, HTML 등의 문서를 입력받아 **JSON**, **Markdown**, **Plain Text** 형식으로 변환할 수 있습니다.

---

## 📁 프로젝트 구조

```
Python_Lexi_Convert/
├── main.py                # 메인 진입점
├── assets/                # 이미지와 리소스 파일
│   └── images/
│       └── Lexi_Convert.png   # 애플리케이션 아이콘
├── utils/                 # 공통 유틸리티 함수 모음
│   ├── init.py
│   ├── json_encoder.py    # CustomJSONEncoder 클래스
│   ├── module_checker.py  # 필요한 모듈 체크 및 설치
│   └── text_utils.py      # 텍스트 전처리 및 유틸 함수
├── converters/            # 문서 포맷 변환 관련 모듈
│   ├── init.py
│   ├── epub_converter.py  # EPUB 포맷 변환 처리
│   ├── pdf_converter.py   # PDF 포맷 변환 처리
│   ├── html_converter.py  # HTML 포맷 변환 처리
│   ├── common.py          # 변환 공통 함수들
│   ├── file_merger.py     # 파일 병합 관련 기능
│   └── exporters.py       # JSON, 마크다운, 텍스트 등 출력 포맷 처리
├── ui/                    # 사용자 인터페이스 관련 코드
│   ├── init.py
│   ├── main_app.py        # 전체 UI 메인 앱 구성
│   ├── basic_tab.py       # 기본 설정 탭 UI
│   ├── advanced_tab.py    # 고급 설정 탭 UI
│   └── merger_tab.py      # 파일 병합 탭 UI
└── scripts/               # 빌드 및 배포용 스크립트
├── build_portable.bat # 폴더형 실행 파일 빌드 스크립트
└── build_onefile.bat  # 단일 EXE 실행 파일 빌드 스크립트
```

---

## 🛠️ 주요 기능

- **EPUB, PDF, HTML → JSON / Markdown / Plain Text 변환**
- **문서 구조(제목, 표 등) 분석 및 계층적 데이터 추출**
- **텍스트 청크 분할 & 메타데이터 추출**
- **다중 파일 일괄 처리 및 병합**
- **독립적인 파일 병합 기능**
  - 폴더 내 특정 확장자 파일(.py, .c, .h 등) 병합
  - 하위 폴더 파일 포함 병합 기능
  - 폴더 구조 정보 유지 옵션
- **모듈 자동 설치 / 마지막 경로 저장 / 디버그 모드**

---

## 🔧 필요 요구사항

- Python 3.8 이상
- `ebooklib`, `beautifulsoup4`, `pymupdf`, `pillow`, `pandas`, `lxml`

```
pip install ebooklib beautifulsoup4 pymupdf pillow pandas lxml

```

---

## 🚀 실행 방법

```
python main.py

```
- 처음 실행 시 필요한 패키지가 없으면 자동 설치 여부를 물어봅니다.
- 설치 후 프로그램을 재시작하면 적용됩니다.

---

## 📑 사용자 인터페이스

프로그램은 세 개의 주요 탭으로 구성되어 있습니다:

1.  **파일 바꾸기**: 기본 변환 기능 설정
    - 문서 선택 (개별 파일 또는 폴더)
    - 출력 폴더 지정
    - 출력 포맷 선택 (JSON, 마크다운, 텍스트)

2.  **바꾸기 설정**: 고급 변환 옵션
    - 텍스트 청크 크기 설정
    - 메타데이터 및 목차 포함 옵션
    - 병합 출력 설정

3.  **파일 합치기**: 독립적인 파일 병합 기능
    - 폴더 내 특정 확장자 파일 병합
    - 개별 선택 파일 병합
    - 다양한 형식 지원 (.py, .c, .h, .txt, .json 등)
    - 하위 폴더 포함 및 폴더 구조 정보 유지 옵션

---

## 📦 실행 파일 만들기 (PyInstaller)

### 👜 포터블 폴더 형태

```
cd scripts
build_portable.bat
```

- `dist` 폴더 안에 폴더형 실행 파일 생성

### 📁 단일 EXE 파일

```
cd scripts
build_onefile.bat

```

- `dist` 폴더 안에 단일 EXE 파일 생성

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
