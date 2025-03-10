import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_upstage import UpstageEmbeddings
from langchain.vectorstores import FAISS
from tqdm import tqdm
import time

# 폴더 경로 및 카테고리 설정
questions_folder = r'C:\Users\uone\Desktop\health\Q\과호흡 증후군'
answers_folder = r'C:\Users\uone\Desktop\health\A\과호흡 증후군'
category = os.path.basename(os.path.dirname(questions_folder))
print(f"카테고리: {category}")

# JSON 파일 읽기 함수
def get_all_json_files(folder_path):
    json_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


def load_json_files(json_files, key):
    texts = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if key == 'question':
                    texts.append(data.get('question', '').strip())
                elif key == 'answer':
                    answer_text = ''
                    for section in ['intro', 'body', 'conclusion']:
                        answer_text += data.get('answer', {}).get(section, '') + ' '
                    texts.append(answer_text.strip())
        except (json.JSONDecodeError, KeyError) as e:
            print(f"파일 로드 오류: {file_path} - {str(e)}")
    return [t for t in texts if t]



# 질문과 답변 텍스트 읽기
question_files = get_all_json_files(questions_folder)
answer_files = get_all_json_files(answers_folder)
question_texts = load_json_files(question_files, 'question')
answer_texts = load_json_files(answer_files, 'answer')
print(f"질문 개수: {len(question_texts)}, 답변 개수: {len(answer_texts)}")

# 문서 분할
print("split 시작 : " + time.strftime('%x %X'))
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
question_docs = [Document(page_content=q) for q in question_texts]
answer_docs = [Document(page_content=a) for a in answer_texts]

print("split 시작 - question_splits")
question_splits = text_splitter.split_documents(question_docs)
print("split 시작 - answer_splits")
answer_splits = text_splitter.split_documents(answer_docs)

print("임베딩 및 FAISS 벡터스토어 생성 - embeddings")
# 임베딩 및 FAISS 벡터스토어 생성
embeddings = UpstageEmbeddings(model='embedding-query')
print("임베딩 및 FAISS 벡터스토어 생성 - vectorstore")
vectorstore = FAISS.from_documents(question_splits + answer_splits, embeddings)
print("저장중")



def add_to_faiss(vectorstore, splits, category, data_type):
    metadata = [{'category': category, 'type': data_type} for _ in splits]
    texts = [split.page_content for split in splits]
    # tqdm을 활용한 진행률 표시
    for text, meta in tqdm(zip(texts, metadata), total=len(texts), desc=f"Adding {data_type} data"):
        vectorstore.add_texts(texts=[text], metadatas=[meta])

    #vectorstore.add_texts(texts=texts, metadatas=metadata)
    print(f"{data_type} 데이터 {len(splits)}개가 저장되었습니다.")

print("faiss저장 - question")
add_to_faiss(vectorstore, question_splits, category, 'question')
print("faiss저장 - answer")
add_to_faiss(vectorstore, answer_splits, category, 'answer')


print("local저장")
vectorstore.save_local("health_care")
print(f"FAISS 인덱스가 'health_care'로 저장되었습니다.")
print("완료 : " + time.strftime('%x %X'))
