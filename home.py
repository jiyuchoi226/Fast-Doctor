import streamlit as st
import os

def get_local_url():
    """Streamlit Local URL 가져오기."""
    server_address = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    server_port = os.getenv("STREAMLIT_SERVER_PORT", "8501")
    return f"http://{server_address}:{server_port}"


# Local URL 가져오기
local_url = get_local_url()
# 디지털 의료 플랫폼
st.set_page_config(
    page_title="디지털 의료 플랫폼",
    page_icon="💊",
)

st.title("패스트닥터(Fast Doctor)")

with st.expander("", expanded=True):
    st.header("🤖 Dr.Fast")
    st.markdown("🔹 **안녕하세요. Dr.Chat입니다. 궁금한 내용을 물어보세요.**")

# st.markdown("---")
with st.expander("", expanded=True):
    st.header("🚑 증상 분석 및 병원 추천")
    st.markdown("""
    📌 증상과 주소를 작성하여 검색해주세요.<br>
    📌 위치 검색 설정을 통해 세부적으로 확인할 수 있습니다.<br>
    📌 최초 입력된 주소는 현재 위치로 조회 됩니다.
    """,
                unsafe_allow_html=True)

# st.markdown("---")
with st.expander("", expanded=True):
    st.header("📑 PDF 요약 Chatbot")  # page_link = f"{local_url}/참고_파일_요약"
    st.markdown("### 📌 **사용 방법**")
    st.markdown("""
    1. **PDF 업로드**: 하단의 업로드 창을 통해 PDF 파일을 선택하세요.
    2. **문서 요약**: 업로드된 문서의 주요 내용을 요약해서 보여줍니다.
    3. **질문하기**: 문서 내용에 대해 질문을 입력하면 실시간으로 답변을 제공합니다.
    """)

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

# JavaScript로 특정 href 속성 변경
new_link = f"{local_url}/참고_파일_요약"  # 변경할 링크 주소

st.markdown(
    f"""
    <script>
    var linkElement = document.querySelector('[data-testid="stHeaderActionElements"] a');
    if (linkElement) {{
        linkElement.href = "{new_link}";  // 링크 URL 변경
        linkElement.target = "_self";    // 현재 탭에서 열기
    }}
    </script>
    """,
    unsafe_allow_html=True,
)

# st.title("헤더 링크 수정")
# st.write(f"헤더 링크가 {new_link} 로 변경되었습니다.")

# st.sidebar.header("home")
# st.sidebar.write(f"🔗 [홈페이지]({local_url}/참고_파일_요약)")
# st.sidebar.write(f'<a href="{local_url}/참고_파일_요약" target="_self">📄 참고 파일 요약</a>', unsafe_allow_html=True)