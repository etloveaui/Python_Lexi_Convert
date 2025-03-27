# converters/file_merger.py
import os
import glob
import json
from datetime import datetime
from utils.json_encoder import CustomJSONEncoder

def merge_text_files(directory_path, output_path, file_pattern="*.txt", include_filename=True, include_folder_structure=True, recursive=True):
    """텍스트 파일들을 병합합니다. recursive=True이면 하위 폴더까지 탐색합니다."""
    try:
        # 해당 패턴의 모든 파일 찾기 (recursive=True면 하위 폴더까지)
        files = []
        if recursive:
            for root, _, _ in os.walk(directory_path):
                for file in glob.glob(os.path.join(root, file_pattern)):
                    files.append(file)
        else:
            files = glob.glob(os.path.join(directory_path, file_pattern))
        
        if not files:
            return False, f"지정된 경로({directory_path})에서 {file_pattern} 패턴의 파일을 찾을 수 없습니다."
        
        # 출력 파일 열기
        with open(output_path, 'w', encoding='utf-8') as outfile:
            # 헤더 추가
            outfile.write(f"# 병합된 파일 ({len(files)}개)\n")
            outfile.write(f"# 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 각 파일의 내용 병합
            for file_path in files:
                rel_path = os.path.relpath(file_path, directory_path)
                file_name = os.path.basename(file_path)
                folder_path = os.path.dirname(rel_path)
                
                if include_filename:
                    outfile.write(f"\n{'=' * 80}\n")
                    if include_folder_structure and folder_path:
                        outfile.write(f"폴더: {folder_path}\n")
                    outfile.write(f"파일: {file_name}\n")
                    outfile.write(f"{'=' * 80}\n\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(content)
                        
                        # 파일 간 구분을 위한 빈 줄 추가
                        if not content.endswith('\n'):
                            outfile.write('\n')
                        outfile.write('\n')
                except Exception as e:
                    outfile.write(f"[파일 읽기 오류: {str(e)}]\n\n")
        
        return True, f"{len(files)}개의 파일이 성공적으로 병합되었습니다: {output_path}"
    
    except Exception as e:
        return False, f"파일 병합 중 오류 발생: {str(e)}"

def merge_code_files(directory_path, output_path, file_extension, include_filename=True, include_folder_structure=True, recursive=True):
    """코드 파일들(.py, .c, .h 등)을 병합합니다. recursive=True이면 하위 폴더까지 탐색합니다."""
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    
    # 파일 목록 수집
    files = []
    if recursive:
        for root, dirs, filenames in os.walk(directory_path):
            # .git과 같은 숨김 폴더 제외
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                # 정확히 해당 확장자로 끝나는 파일만 추가
                if filename.endswith(file_extension):
                    full_path = os.path.join(root, filename)
                    files.append(full_path)
    else:
        # 비재귀적 검색일 경우 현재 폴더만 검색
        for filename in os.listdir(directory_path):
            if filename.endswith(file_extension):
                full_path = os.path.join(directory_path, filename)
                if os.path.isfile(full_path):
                    files.append(full_path)
    
    if not files:
        return False, f"지정된 경로({directory_path})에서 {file_extension} 확장자를 가진 파일을 찾을 수 없습니다."
    
    # 파일 이름 순으로 정렬
    files.sort()
    
    # 출력 파일 열기
    with open(output_path, 'w', encoding='utf-8') as outfile:
        # 헤더 추가
        outfile.write(f"# 병합된 파일 ({len(files)}개)\n")
        outfile.write(f"# 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write(f"# 파일 확장자: {file_extension}\n\n")
        
        # 각 파일의 내용 병합
        for file_path in files:
            rel_path = os.path.relpath(file_path, directory_path)
            file_name = os.path.basename(file_path)
            folder_path = os.path.dirname(rel_path)
            
            if include_filename:
                outfile.write(f"\n{'=' * 80}\n")
                if include_folder_structure and folder_path:
                    outfile.write(f"폴더: {folder_path}\n")
                outfile.write(f"파일: {file_name}\n")
                outfile.write(f"{'=' * 80}\n\n")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    
                    # 파일 간 구분을 위한 빈 줄 추가
                    if not content.endswith('\n'):
                        outfile.write('\n')
                    outfile.write('\n')
            except Exception as e:
                outfile.write(f"[파일 읽기 오류: {str(e)}]\n\n")
    
    return True, f"{len(files)}개의 {file_extension} 확장자 파일이 성공적으로 병합되었습니다: {output_path}"



def merge_json_files(directory_path, output_path, recursive=True):
    """JSON 파일들을 하나의 JSON 배열로 병합합니다. recursive=True이면 하위 폴더까지 탐색합니다."""
    try:
        # JSON 파일들 찾기
        files = []
        if recursive:
            for root, _, _ in os.walk(directory_path):
                for file in glob.glob(os.path.join(root, "*.json")):
                    files.append(file)
        else:
            files = glob.glob(os.path.join(directory_path, "*.json"))
        
        if not files:
            return False, f"지정된 경로({directory_path})에서 JSON 파일을 찾을 수 없습니다."
        
        merged_data = []
        
        # 각 JSON 파일 처리
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    data = json.load(infile)
                    
                    # 객체 또는 배열 처리
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        # 파일 출처 정보 추가
                        rel_path = os.path.relpath(file_path, directory_path)
                        data['_source_file'] = rel_path
                        merged_data.append(data)
            except Exception as e:
                # 오류 발생 시 해당 파일 건너뛰기
                continue
        
        # 병합된 데이터 저장
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(merged_data, outfile, cls=CustomJSONEncoder, ensure_ascii=False, indent=2)
        
        return True, f"{len(files)}개의 JSON 파일이 성공적으로 병합되었습니다: {output_path}"
    
    except Exception as e:
        return False, f"JSON 파일 병합 중 오류 발생: {str(e)}"

def merge_documents(input_files, output_path, file_type="txt"):
    """여러 문서 파일들을 병합합니다."""
    if file_type.lower() == "txt":
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                # 헤더 추가
                outfile.write(f"# 병합된 문서 ({len(input_files)}개)\n")
                outfile.write(f"# 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 각 파일의 내용 병합
                for file_path in input_files:
                    file_name = os.path.basename(file_path)
                    
                    outfile.write(f"\n{'=' * 80}\n")
                    outfile.write(f"문서: {file_name}\n")
                    outfile.write(f"{'=' * 80}\n\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(content)
                            
                            # 파일 간 구분을 위한 빈 줄 추가
                            if not content.endswith('\n'):
                                outfile.write('\n')
                            outfile.write('\n')
                    except Exception as e:
                        outfile.write(f"[파일 읽기 오류: {str(e)}]\n\n")
            
            return True, f"{len(input_files)}개의 문서가 성공적으로 병합되었습니다: {output_path}"
        
        except Exception as e:
            return False, f"문서 병합 중 오류 발생: {str(e)}"
    else:
        return False, f"지원하지 않는 출력 파일 형식입니다: {file_type}"
