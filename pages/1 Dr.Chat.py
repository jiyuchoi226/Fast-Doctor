import os
import getpass
import warnings
from langchain.vectorstores import FAISS
from langchain_upstage import UpstageEmbeddings, ChatUpstage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.document_loaders import WebBaseLoader
from datetime import datetime
import uuid
import re
import streamlit as st
import tkinter as tk
from audio_recoder import AudioRecorder
import requests
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from streamlit.components.v1 import html
warnings.filterwarnings("ignore")

os.environ["UPSTAGE_API_KEY"] = "Your_Upstage_KEY"
if "UPSTAGE_API_KEY" not in os.environ or not os.environ["UPSTAGE_API_KEY"]:
    os.environ["UPSTAGE_API_KEY"] = getpass.getpass("Enter your UPSTAGE API KEY: ")
    print("API key has been set successfully.")
else:
    print("API key is already set.")


def call_upstage_solar_api(prompt):
    api_url = "https://api.upstage.ai/v1/solar/chat/completions"
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise ValueError("업스테이지 API 키가 설정되지 않았습니다.")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "solar-1-mini-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "top_p": 0.85,
        "max_tokens": 500
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            print("업스테이지 Solar API 연결 성공!")
            response_data = response.json()
            answer = response_data["choices"][0]["message"]["content"]
            return answer
        else:
            raise Exception(f"업스테이지 Solar API 호출 실패: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"예외 발생: {e}")
        return None

# 데이터로드
embeddings = UpstageEmbeddings(model='embedding-query')
vectorstore = FAISS.load_local("C:\Python\Fast-Doctor\health_care", embeddings, allow_dangerous_deserialization=True)
class ConversationHistory:
    def __init__(self, embeddings, index_path="history_vectorstore.index"):
        self.history = {}
        self.embeddings = embeddings
        self.history_vectorstore = None
        self.index_path = index_path
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

    def add_to_history(self, session_id, user_input, bot_response):
        if session_id not in self.history:
            self.history[session_id] = []

        self.history[session_id].append({'user_input': user_input, 'bot_response': bot_response})
        self.save_to_faiss(user_input, bot_response, session_id)

    def get_history(self, session_id):
        history_entries = self.history.get(session_id, [])
        return " ".join([f"User: {entry['user_input']} Bot: {entry['bot_response']}" for entry in history_entries])

    def reset_history(self, session_id):
        if session_id in self.history:
            del self.history[session_id]

        if self.history_vectorstore is not None:
            self.history_vectorstore.reset()
            self.history_vectorstore = FAISS.from_documents([], self.embeddings)
        print("대화 기록이 초기화되었습니다.")

    def save_to_faiss(self, user_input, bot_response, session_id):
        combined_text = f"User: {user_input} Bot: {bot_response}"
        history_docs = [Document(page_content=combined_text)]
        history_splits = self.text_splitter.split_documents(history_docs)

        if self.history_vectorstore is None:
            self.history_vectorstore = FAISS.from_documents(history_splits, self.embeddings)

        metadata = [{'type': 'conversation', 'session_id': session_id} for _ in history_splits]
        texts = [split.page_content for split in history_splits]
        self.history_vectorstore.add_texts(texts=texts, metadatas=metadata)
        self.history_vectorstore.save_local(self.index_path)
        print("대화 기록이 FAISS에 저장되었습니다.")

    def list_sessions(self):
        return list(self.history.keys())

    def _generate_session_id(self):
        return f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

class SessionManager:
    def __init__(self, conversation_history):
        self.conversation_history = conversation_history
        self.sessions = {}

    def create_session(self):
        session_id = self.conversation_history._generate_session_id()
        self.sessions[session_id] = {'conversation': []}
        return session_id

    def get_session(self, session_id):
        return self.sessions.get(session_id, None)

    def save_message(self, session_id, user_input, bot_response=None):
        self.conversation_history.add_to_history(session_id, user_input, bot_response)

    def get_conversation(self, session_id):
        return self.conversation_history.get_history(session_id)

    def get_all_sessions(self):
        return list(self.sessions.keys())


class ChatUI:
    def __init__(self, root, session_manager):
        self.root = root
        self.session_manager = session_manager
        self.current_session_id = None
        self.create_ui()

    def create_ui(self):
        self.text_box = tk.Text(self.root, height=15, width=50)
        self.text_box.pack(padx=10, pady=10)
        self.input_box = tk.Entry(self.root, width=40)
        self.input_box.pack(pady=10)
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(pady=10)
        self.new_session_button = tk.Button(self.root, text="New Session", command=self.new_session)
        self.new_session_button.pack(pady=10)
        self.session_list_box = tk.Listbox(self.root, height=5, width=50)
        self.session_list_box.pack(pady=10)
        self.session_list_box.bind("<ButtonRelease-1>", self.select_session)

    def send_message(self):
        message = self.input_box.get()
        if message:
            bot_response = "This is a bot response."
            if self.current_session_id:
                self.session_manager.save_message(self.current_session_id, message, None)
                self.update_conversation()
                self.session_manager.save_message(self.current_session_id, message, bot_response)
                self.update_conversation()

    def new_session(self):
        session_id = self.session_manager.create_session()
        self.current_session_id = session_id
        self.session_list_box.insert(tk.END, session_id)
        self.text_box.delete(1.0, tk.END)

    def select_session(self, event):
        selected_session = self.session_list_box.curselection()
        if selected_session:
            session_id = self.session_list_box.get(selected_session)
            self.current_session_id = session_id
            conversation = self.session_manager.get_conversation(session_id)
            self.text_box.delete(1.0, tk.END)
            if conversation:
                self.text_box.insert(tk.END, "\n".join(conversation))

    def update_conversation(self):
        if self.current_session_id:
            conversation = self.session_manager.get_conversation(self.current_session_id)
            if conversation:
                self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, "\n".join(conversation))


os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
class ExternalDocumentManager:
    def __init__(self):
        self.external_docs = []
        self.external_vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

    def fetch_documents_from_url(self, url):
        url_pattern = re.compile(r'https?://[^\s]+')
        if not url_pattern.fullmatch(url):
            print("유효하지 않은 URL입니다.")
            return

        try:
            headers = {'User-Agent': os.environ["USER_AGENT"]}
            web_loader = WebBaseLoader(url, headers=headers)
            web_docs = web_loader.load()

            if web_docs:
                self.add_external_documents(web_docs)
                print("웹사이트에서 문서를 가져왔습니다.")
            else:
                print("웹사이트에서 문서를 찾을 수 없습니다.")
        except requests.exceptions.RequestException as e:
            print(f"웹사이트에서 문서를 가져오는 데 실패했습니다: {e}")
        except Exception as e:
            print(f"알 수 없는 오류가 발생했습니다: {e}")

    def add_external_documents(self, documents):
        doc_splits = self.text_splitter.split_documents(documents)
        self.external_docs.extend(doc_splits)
        self.external_vectorstore = FAISS.from_documents(doc_splits, embeddings)
        print(f"{len(doc_splits)}개의 문서가 외부 문서로 추가되었습니다.")



nlp = spacy.load("en_core_web_sm")

def retrieve_documents_with_similarity(query, top_k=1):
    query_vector = embeddings.embed_query(query)
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': top_k})
    result_docs = retriever.invoke(query)
    results_with_similarity = []

    for doc in result_docs:
        doc_vector = embeddings.embed_query(doc.page_content)
        similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
        results_with_similarity.append((doc, similarity))
        print(f"문서: {doc.page_content[:150]}... 유사도: {similarity:.4f}")

    results_with_similarity = sorted(results_with_similarity, key=lambda x: x[1], reverse=True)
    return results_with_similarity


def contextualized_retrieval_with_similarity(user_question, conversation_history, session_id, external_manager=None,
                                             top_k=1):
    context = conversation_history.get_history(session_id)
    if conversation_history.history_vectorstore:
        relevant_docs = conversation_history.history_vectorstore.similarity_search(user_question, k=top_k)
        if relevant_docs:
            context += "\n\n" + "\n".join([highlight_text(doc.page_content, user_question) for doc in relevant_docs])

    enhanced_question = f"{context} {user_question}"

    if external_manager and external_manager.external_docs:
        external_docs_content = "\n\n".join(
            [highlight_text(doc.page_content, user_question) for doc in external_manager.external_docs])
        enhanced_question = f"{enhanced_question}\n\n{external_docs_content}"
    main_results_with_similarity = retrieve_documents_with_similarity(enhanced_question, top_k)
    return main_results_with_similarity


def generate_prompt_with_similarity(user_input, conversation_history, session_id, external_manager):
    results_with_similarity = contextualized_retrieval_with_similarity(
        user_input, conversation_history, session_id, external_manager, top_k=3
    )
    print("\n--- 유사도---")
    for doc, similarity in results_with_similarity:
        print(f"유사도: {similarity:.4f}")
    print("-------------------")

    context = "\n\n".join(
        [f"{doc.page_content} (유사도: {similarity:.4f})" for doc, similarity in results_with_similarity])
    prompts = ChatPromptTemplate.from_messages(
        [
            ("system", """
                당신은 의학 전문 지식을 갖춘 AI 도우미입니다.
                사용자가 묻는 질문에 대해 관련 정보를 바탕으로 답변을 제공합니다.
                만약 답을 모른다면 모른다고 정확히 말해주시고 가능하다면 여러 시나리오나 해결책을 고려해 답변을 다양하게 제공해주세요.
                대화가 진행되는 동안 동일한 답변은 피해주시고 답변은 3문장 내외로 간추려 주시길 바랍니다.
                또한 강조할 부분이 있다면 굵은 글자로 강조해주세요.
                ---
                CONTEXT:
                {context}
            """),
            ("human", "{input}")
        ]
    )
    return prompts, context


def generate_answer_with_similarity(user_input, conversation_history, session_id, external_manager=None):
    try:
        prompts, context = generate_prompt_with_similarity(user_input, conversation_history, session_id,
                                                           external_manager)
        llm = ChatUpstage(model='solar-pro')
        chain = prompts | llm | StrOutputParser()
        response = chain.invoke({"input": user_input, "context": context})
        highlighted_answer = highlight_text(response, user_input)
        return highlighted_answer
    except Exception as e:
        return f"죄송합니다. 답변을 생성하는 데 문제가 발생했습니다: {str(e)}"


def extract_important_terms_from_query(query):
    doc = nlp(query)
    important_terms = [token.text for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ", "NUM"]]
    return important_terms

def highlight_text(text, query):
    important_terms = extract_important_terms_from_query(query)
    if not important_terms:
        return text

    highlighted_text = text
    for term in important_terms:
        highlighted_text = re.sub(rf"({re.escape(term)})", r'**\1**', highlighted_text, flags=re.IGNORECASE)
    return highlighted_text

def chat_interface():
    st.set_page_config(page_title="AI 챗봇", page_icon=":robot_face:")
    st.title("🤖 Dr.Fast")
    st.markdown("""
            🔹 안녕하세요. Dr.Fast입니다. 궁금한 내용을 물어보세요.<br>
            🔹 저를 통해 빠른 의료 도움을 받으실 수 있습니다.
    """,
            unsafe_allow_html=True)
    st.markdown("""
        <style>
            .e1obcldf2 {
                border-radius: 10px;
                background-color: #F0F2F6;
                border: 1px solid transparent;
            }
            .e1obcldf2:hover {      
                border: 1px solid #FF4B4B;         
            }
            .stHorizontalBlock {
                position: fixed;
                bottom: 0;
                padding-bottom: 30px; /* 하단 */
                padding-top: 20px; /* 하단 */
                z-index: 1000; /* 우선 순위 */
                width: 100%;
                max-width: 704px;
                background-color: white;
            }
            .stMainBlockContainer {
                overflow-y: auto
            }
            
            [data-testid="stSidebarNav"] a[href*="home"] {
            pointer-events: none; /* 클릭 방지 */
            opacity: 0.8; 
            text-decoration: none; 
            background-color: transparent;
            }        
        </style> 
    """, unsafe_allow_html=True)
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = ConversationHistory(embeddings)
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager(st.session_state.conversation_history)
    if "external_manager" not in st.session_state:
        st.session_state.external_manager = ExternalDocumentManager()

    conversation_history = st.session_state.conversation_history
    session_manager = st.session_state.session_manager
    external_manager = st.session_state.external_manager
    session_id = "Chatbot1"

    if f"{session_id}_messages" not in st.session_state:
        st.session_state[f"{session_id}_messages"] = []

    conversation = st.session_state[f"{session_id}_messages"]

    for message in conversation:
        if isinstance(message, dict):
            st.chat_message(message["role"]).markdown(message["content"])
        else:
            st.chat_message("assistant").markdown(message)

    # 레이아웃 조정
    col1, col2 = st.columns([1, 15])  # 채팅 입력과 음성 녹음을 두 열로 배치

    with col1:
        # 오디오 레코더
        recorder = AudioRecorder(silence_timeout=2)
        user_input_audio = recorder.run()

    with col2:
        # 사용자 입력 필드
        user_input_text = st.chat_input("질문을 입력하세요.")

    #user_input_text = st.chat_input("질문을 입력하세요!")
    # recorder = AudioRecorder(silence_timeout=2)
    # user_input_audio = recorder.run()

    if user_input_text:
        user_input = user_input_text
    elif user_input_audio:
        user_input = user_input_audio
        print(user_input_audio)
    else:
        user_input = None

    if user_input:
        user_message = {"role": "user", "content": user_input}
        st.session_state[f"{session_id}_messages"].append(user_message)
        st.chat_message(user_message["role"]).markdown(user_message["content"])

        response = generate_answer_with_similarity(
            user_input,
            conversation_history,
            session_id,
            external_manager if external_manager.external_docs else None
        )

        assistant_message = {"role": "assistant", "content": response}
        st.session_state[f"{session_id}_messages"].append(assistant_message)
        st.chat_message(assistant_message["role"]).markdown(assistant_message["content"])
        conversation_history.add_to_history(session_id, user_input, response)
        session_manager.save_message(session_id, assistant_message)

if __name__ == "__main__":
    chat_interface()
