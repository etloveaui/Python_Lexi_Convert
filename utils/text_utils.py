# utils/text_utils.py
import re

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
