import os
import streamlit as st
import time
import base64
import tempfile
from langchain_upstage import UpstageEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_upstage import ChatUpstage
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import chromadb

chromadb.api.client.SharedSystemClient.clear_system_cache()

os.environ["UPSTAGE_API_KEY"] = "up_CAb1wgEBbFqTiFuGvb1EhXakso2jr"
if not os.getenv("UPSTAGE_API_KEY"):
    os.environ["UPSTAGE_API_KEY"] = st.text_input("Enter your UPSTAGE API KEY:", type="password")
    if not os.environ["UPSTAGE_API_KEY"]:
        st.stop()

if "id" not in st.session_state:
    st.session_state.id = "CHAT2"
    st.session_state.file_cache = {}

session_id = st.session_state.id


def reset_chat():
    st.session_state[f"{session_id}_messages"] = []
    st.session_state.context = None
    st.session_state["summary_done"] = False


def display_pdf(file):
    st.markdown("### PDF Preview")
    base64_pdf = base64.b64encode(file.read()).decode("utf-8")
    pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="400" height="100%" type="application/pdf"
                        style="height:50vh; width:100%"
                    >
                    </iframe>"""
    st.markdown(pdf_display, unsafe_allow_html=True)


def process_pdf(uploaded_file, max_pages=20):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, uploaded_file.name)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            if len(pages) > max_pages:
                pages = pages[:max_pages]

            vectorstore = Chroma.from_documents(pages, UpstageEmbeddings(model="solar-embedding-1-large"))
            retriever = vectorstore.as_retriever(k=2)
            return retriever
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

# CSS로 사이드바 네비게이션 클릭 막기
st.markdown(
    """
    <style>
    //[data-testid="stSidebarNav"] {
        //display: none;
        //pointer-events: none;  /* 클릭 이벤트 비활성화 */
        //opacity: 0.5;          /* 메뉴 흐리게 (선택 사항) */
    //}
        /* Home 링크 비활성화 */
    [data-testid="stSidebarNav"] a[href*="home"] {
        pointer-events: none; /* 클릭 방지 */
        //color: gray;          /* 텍스트 색상 변경 (선택 사항) */
        opacity: 0.8; 
        text-decoration: none; 
        background-color: transparent;
    }
    </style> 
    """,
    unsafe_allow_html=True,
)

st.title("📑 PDF 요약 Chatbot")
st.markdown("### 📌 **사용 방법**")
st.markdown("""
1. **PDF 업로드**: 하단의 업로드 창을 통해 PDF 파일을 선택하세요.
2. **문서 요약**: 업로드된 문서의 주요 내용을 요약해서 보여줍니다.
3. **질문하기**: 문서 내용에 대해 질문을 입력하면 실시간으로 답변을 제공합니다.
""")
st.markdown("---")
uploaded_file = st.file_uploader("Choose your `.pdf` file", type="pdf")

if uploaded_file:
    if uploaded_file.name not in st.session_state.file_cache:
        reset_chat()
    st.session_state.file_cache[uploaded_file.name] = uploaded_file
    retriever = process_pdf(uploaded_file)
    if retriever:
        chat = ChatUpstage(upstage_api_key=os.getenv("UPSTAGE_API_KEY"), model="solar-pro")

        contextualize_q_system_prompt = """이전 대화 내용과 최신 사용자 질문이 있을 때, 이 질문이 이전 대화 내용과 관련이 있을 수 있습니다.
        이런 경우, 대화 내용을 알 필요 없이 독립적으로 이해할 수 있는 질문으로 바꾸세요.
        질문에 답할 필요는 없고, 필요하다면 그저 다시 구성하거나 그대로 두세요."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(
            chat, retriever, contextualize_q_prompt
        )

        qa_system_prompt = """질문-답변 업무를 돕는 보조원입니다.
        질문에 답하기 위해 검색된 내용을 사용하세요.
        답을 모르면 모른다고 말하세요.
        답변은 세 문장 이내로 간결하게 유지하세요.

        ## 답변 예시
        📍답변 내용:
        {context}"""

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(chat, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        st.success("Ready to Chat!")
        display_pdf(uploaded_file)

        if "summary_done" not in st.session_state or not st.session_state["summary_done"]:
            with st.spinner("문서 내용을 요약하고 있습니다..."):
                summary_prompt = f"이 문서에 대한 요약을 3줄로 작성해주세요: {uploaded_file.name}"
                result_summary = rag_chain.invoke(
                    {"input": summary_prompt, "chat_history": st.session_state.get(f"{session_id}_messages", [])}
                )

            st.session_state[f"{session_id}_messages"] = [{"role": "assistant", "content": result_summary["answer"]}]
            st.session_state["summary_done"] = True

if f"{session_id}_messages" not in st.session_state:
    st.session_state[f"{session_id}_messages"] = []

for message in st.session_state.get(f"{session_id}_messages", []):
    if isinstance(message, dict):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

MAX_MESSAGES_BEFORE_DELETION = 4

if prompt := st.chat_input("Ask a question!"):
    if len(st.session_state.get(f"{session_id}_messages", [])) >= MAX_MESSAGES_BEFORE_DELETION:
        del st.session_state[f"{session_id}_messages"][:2]

    st.session_state[f"{session_id}_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        result = rag_chain.invoke({"input": prompt, "chat_history": st.session_state.get(f"{session_id}_messages", [])})

        for chunk in result["answer"].split(" "):
            full_response += chunk + " "
            time.sleep(0.2)
            message_placeholder.markdown(full_response + "\u2588")
            message_placeholder.markdown(full_response)

    st.session_state[f"{session_id}_messages"].append({"role": "assistant", "content": full_response})

print("_______________________")
print(st.session_state.get(f"{session_id}_messages", []))
