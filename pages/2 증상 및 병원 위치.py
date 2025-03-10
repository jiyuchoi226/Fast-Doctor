import streamlit as st
import streamlit.components.v1 as components
import requests
from geopy.geocoders import Nominatim
from utils import predict_disease
from utils import predict_medical
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from streamlit.components.v1 import html
from audio_recoder import AudioRecorder
import time
import re

st.set_page_config(page_title="증상 및 병원 추천", page_icon="🚑")

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

# 위치 정보를 가져오는 함수
def get_current_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        lat, lon = map(float, data["loc"].split(","))
        return lat, lon
    except Exception as e:
        st.error(f"위치 정보를 가져오는 중 오류가 발생했습니다: {e}")
        return None, None

# 세션 상태에서 위치 정보 초기화
if "location" not in st.session_state:
    latitude, longitude = get_current_location()
    if latitude and longitude:
        st.session_state["location"] = {"latitude": latitude, "longitude": longitude}
    else:
        st.session_state["location"] = {"latitude": None, "longitude": None}

# 위치 정보 가져오기
latitude = st.session_state["location"]["latitude"]
longitude = st.session_state["location"]["longitude"]

if latitude and longitude:
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.reverse((latitude, longitude))
    print(f"현재 위치: {location.address}")
    print(f"위도: {latitude}, 경도: {longitude}")
else:
    print("위치 정보를 가져올 수 없습니다.")

# 카카오 REST API 키 및 JavaScript API 키 설정

KAKAO_REST_API_KEY = "136b11c4d714e0f91233e93d9a6ad4c2"  # REST API 키
KAKAO_JS_API_KEY = "16d73f2d34ce5160ead147331927edac"  # JavaScript API 키

# 제목
st.title("🚑 증상 분석 및 병원 추천")
st.markdown("""
📌 증상과 주소를 작성하여 검색해주세요.<br>
📌 위치 검색 설정을 통해 세부적으로 확인할 수 있습니다.<br>
📌 최초 입력된 주소는 현재 위치로 조회 됩니다.
""",
            unsafe_allow_html=True)
#t.markdown("---")


#symptom1 = st.chat_input("증상을 입력하세요.")

st.markdown("""
            <style>
                .e1obcldf2 {
                    //border-radius: 10px;
                    background-color: #F0F2F6;
                    border: 1px solid transparent;            
                    border-top-left-radius: 10px; /* 왼쪽 상단 모서리 둥글게 */
                    border-top-right-radius: 10;  /* 오른쪽 상단 모서리는 직각 */
                    border-bottom-left-radius: 10; /* 왼쪽 하단 모서리는 직각 */
                    border-bottom-right-radius: 10px; /* 오른쪽 하단 모서리 둥글게 */   
                }
                .e1obcldf2:hover {                     
                    border: 1px solid #FF4B4B;
                }
                .stHorizontalBlock {
                    max-height: 40px
                    gap: 2px; /* 간격 */
                    // background-color: #F0F2F6;
                    // border-radius: 10px;
                }      
            </style>
""", unsafe_allow_html=True)

# 레이아웃 조정
c1, c2 = st.columns([15, 1])  # 채팅 입력과 음성 녹음을 두 열로 배치

with c2:
    # 오디오 레코더
    recorder = AudioRecorder(silence_timeout=2)
    user_input_audio = recorder.run()
with c1:
    # 사용자 입력 필드
    #user_input_text = st.chat_input("증상을 입력하세요.")
    symptom = st.text_input(
        label="**·** 증상을 입력하세요.",
        label_visibility="collapsed",
        placeholder="증상을 입력하세요.",  # 플레이스홀더로 대체
        value= user_input_audio if user_input_audio else "")

# 주소 입력 및 좌표 변환
parse_location = location.address.split(",")[-3] + " " + location.address.split(",")[-4]  # + " "+ location.address.split(",")[0]

# 레이아웃 조정
c3, c4 = st.columns([15, 1])  # 채팅 입력과 음성 녹음을 두 열로 배치

with c3:
    # address = st.text_input("**·** 주소를 입력하세요.", parse_location)
    address = st.text_input(
        label="**·** 주소를 입력하세요.",
        label_visibility="collapsed",
        placeholder="주소를 입력하세요.",  # 플레이스홀더로 대체
        value=parse_location if parse_location else "")
    latitude, longitude = None, None
with c4:
    button_clicked = st.button("🔍")



# 설정 박스 생성
with st.expander("위치 검색 설정", expanded=True):
    # 라디오 버튼
    search_type = st.radio(label="**·** 검색 기준을 선택하세요.",
                           options=['가까운 병원 위치', '추천 병원', '응급실'])

    # Streamlit columns로 수평 배치
    col1, spacer, col2 = st.columns([1, 0.1, 2])  # 각 열의 비율 설정

    # Item 1: Number Input
    with col1:
        size = st.number_input('**·** 병원 수를 입력 하세요. (최대 5곳)', 1, 5, 3)

    with spacer:
        st.write("")  # 빈 열(공백)

    # Item 3: Slider
    with col2:
        radius_m = st.slider('**·** 위치 반경(Km)을 입력 하세요.', 1, 10, 3)  # 반경(Km)
        radius = radius_m * 1000
        # st.text('현재 반경 ' + str(radius) + 'Km 입니다')

st.markdown(
    """
    <style>
    div[data-testid="stRadio"] > div{ display: flex; flex-direction:row;}
    div[data-testid="stRadio"] label {margin-right: 10px}
    </style>
    """,
    unsafe_allow_html=True,
)

# 주소 검색 함수
def get_coordinates(address):
    """주소를 위도와 경도로 변환"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and response.json()["documents"]:
        location = response.json()["documents"][0]
        return float(location["y"]), float(location["x"])  # 위도, 경도 반환
    else:
        st.error("주소를 찾을 수 없습니다.")
        return None, None

# 추천 병원 정보 가져오기
def get_recommended_hospital(lat, lng, radius, size, medical):
    text = medical
    fruit_list = text.split("\n")
    cleaned_list = [item[3:] for item in fruit_list]
    #st.success(f"{cleaned_list}")

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": cleaned_list,  # 키워드(증상) 검색
        #"place_name": "서울성모병원", # 병원 이름 > 안됨
        "category_group_code": "HP8",  # 카테고리 코드 (예: 병원)
        "x": lng,
        "y": lat,
        #"radius": radius,  # 반경(m)
        "sort": "distance",  # 거리순 정렬
        "size": size,  # 상위 가져오기
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and response.json()["documents"]:
        return response.json()["documents"]  # 가장 유명한 병원 반환
    else:
        st.error(f"{fruit_list}")
        return []

###########################
# 사용자 증상에 따라 병원 검색
def search_hospitals_by_symptom(Bast_medical, lng, lat, radius, size):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": Bast_medical,  # 검색 키워드 (증상)
        "x": lng,  # 사용자 경도
        "y": lat,  # 사용자 위도
        "radius": radius,  # 검색 반경
        "size": size #임의로 10개 가져오기   # 결과 제한 개수
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        #documents = response.json()["documents"]  # "documents" 값 조회
        # for doc in documents:
        #     st.success(f"{doc}")
        return response.json()["documents"]
    else:
        print("API 요청 실패:", response.status_code)
        return []

##---------------------------------------------------------------------------------------------
# 병원 상세 페이지에서 리뷰와 평점 크롤링
def scrape_hospital_reviews(place_url):
    try:
        # 평점만 가져오자.
        # ChromeDriver 설정
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # 브라우저를 보이지 않게 실행
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=service, options=options)

        # 카카오맵 상세 페이지 로드
        driver.get(place_url)
        time.sleep(1)  # 페이지 로딩 대기 (필요 시 조정)

        # 1. 평점 추출 (color_b 클래스)
        rating_element = driver.find_element(By.CLASS_NAME, "color_b")
        rating = rating_element.text.strip()
        #st.success(f"평균 평점: {ratings}")  # 결과 출력

        # 2. 전체 추천 수 추출 (color_g 클래스)
        rating_element2 = driver.find_element(By.CLASS_NAME, "color_g")
        ratings_all = rating_element2.text.strip()
        match = re.search(r"\((\d+)\)", ratings_all)  # 괄호 안 숫자 추출
        rating_all = int(match.group(1))
        #st.success(f"전체 추천 수: {rating_all}")

        # 3. 추천 포인트 데이터 추출 (chip_likepoint 클래스)
        points = driver.find_elements(By.CLASS_NAME, "chip_likepoint")

        # 결과 출력
        recommendation_points = {}
        for point in points:
            try:
                category = point.find_element(By.CLASS_NAME, "txt_likepoint").text.strip()
                score = point.find_element(By.CLASS_NAME, "num_likepoint").text.strip()
                recommendation_points[category] = score
            except:
            # 요소를 찾지 못했을 때 실행되는 로직
                print("크롤링 실패: 요소를 찾을 수 없습니다.")
        #st.success(f"{recommendation_points}")

        reviews = {"rating": rating, "rating_all": rating_all, "recommendation_points": recommendation_points}

        return reviews

        # # 병원 상세 페이지 HTML 가져오기
        # response = requests.get(place_url)
        # soup = BeautifulSoup(response.text, "html.parser")
        # #driver.find_element(By.CLASS_NAME, "color_b")
        #
        # # 리뷰 및 평점 추출 (HTML 구조 분석 필요)
        # reviews = soup.select(".color_b")  # 리뷰가 담긴 요소 선택자
        # ratings = soup.select(".color_g")  # 평점이 담긴 요소 선택자
        #
        # st.success(f"reviews : {reviews}")
        # st.success(f"ratings : {ratings}")
        #
        # # 리뷰 및 평점 데이터 수집
        # review_list = []
        # for review, rating in zip(reviews, ratings):
        #     review_text = review.text.strip()
        #     rating_value = rating.text.strip()
        #     review_list.append({"review": review_text, "rating": rating_value})
        #
        #     for doc in review_list:
        #         st.success(f"{doc}")
        #
        # return review_list
    except Exception as e:
        print("크롤링 실패:", e)
        return []

# 병원 추천 시스템
def recommend_hospitals(Bast_medical, x, y, radius, size):
    # 증상 기반으로 병원 검색
    hospitals = search_hospitals_by_symptom(Bast_medical, x, y, radius, size)

    recommendations = []

    for hospital in hospitals:
        name = hospital["place_name"]
        place_url = hospital["place_url"]
        phone = hospital["phone"]

        # 병원 리뷰 및 평점 가져오기
        reviews = scrape_hospital_reviews(place_url)
        rating = reviews["rating"]
        rating_all = reviews["rating_all"]
        recommendation_points = reviews["recommendation_points"]

        # 딕셔너리에 데이터 추가
        hospital["rating"] = rating
        hospital["rating_all"] = rating_all
        hospital["recommendation_points"] = recommendation_points

        # 추천 병원 목록에 추가
        #recommendations.append({"name": name, "rating": rating, "rating_all":rating_all, "url": place_url, "phone": phone, "hospital": hospitals})

    return hospitals#recommendations



###

# 가장 가까운 병원 정보 가져오기
def get_nearest_hospital(lat, lng, radius, size, medical):
    #st.success(f"{medical}")
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": medical,  # 키워드 검색
        "category_group_code": "HP8",  # 카테고리 코드 (예: 병원)
        "x": lng,
        "y": lat,
        "radius": radius,  # 반경(m)
        "sort": "distance",  # 거리순 정렬
        "size": size,  # 상위 가져오기

    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and response.json()["documents"]:
        return response.json()["documents"]  # 가장 가까운 3곳 반환
    else:
        st.error("가까운 병원을 찾을 수 없습니다.")
        return []

# 가장 가까운 응급실 정보 가져오기
def get_nearest_hospital2(lat, lng, radius, size, medical):
    #st.success(f"{medical}")
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": medical,  # 키워드 검색
        "x": lng,
        "y": lat,
        "radius": radius,  # 반경(m)
        "sort": "distance",  # 거리순 정렬
        "size": size,  # 상위 가져오기
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and response.json()["documents"]:
        return response.json()["documents"]  # 가장 가까운 3곳 반환
    else:
        st.error("가까운 응급실을 찾을 수 없습니다.")
        return []

if address:
    latitude, longitude = get_coordinates(address)

if button_clicked:
    try:
        if not symptom:
            # 경고 메시지를 일시적으로 표시
            placeholder = st.empty()
            placeholder.error("⚠️ 증상을 입력해주세요.")
            time.sleep(3)
            placeholder.empty()
        elif not address:
            placeholder = st.empty()
            placeholder.error("⚠️ 주소를 입력해주세요.")
            time.sleep(3)
            placeholder.empty()
        else:
            # AI 분석
            disease = predict_disease(symptom)
            st.success(f"{disease}" )

            medical = predict_medical(symptom, "medicals", size)

            def hospital_location():  # nearest
                if search_type == "가까운 병원 위치":
                    return get_nearest_hospital(latitude, longitude, radius, size, medical)
                elif search_type == "추천 병원":
                    return recommend_hospitals(medical, latitude, longitude, radius, size)
                elif search_type == "응급실":
                    return get_nearest_hospital2(latitude, longitude, radius, size, "응급")
                else:
                    st.error("검색 기준 오류 발생")

            # 병원 데이터 가져오기
            if latitude and longitude:
                nearest_hospital = hospital_location()

                # HTML 코드 생성
                clinic_markers = ""
                if nearest_hospital:
                    for clinic in nearest_hospital:
                        clinic_name = clinic["place_name"]
                        clinic_lat = clinic["y"]
                        clinic_lng = clinic["x"]
                        clinic_address = clinic.get("road_address_name", "주소 정보 없음")
                        clinic_phone = clinic.get("phone", "전화번호 없음")
                        clinic_rating = clinic.get("rating")
                        clinic_rating_all = clinic.get("rating_all")
                        clinic_points = clinic.get("recommendation_points")
                        clinic_markers += f"""
                        var marker = new kakao.maps.Marker({{
                            position: new kakao.maps.LatLng({clinic_lat}, {clinic_lng}),
                            map: map
                        }});
                        var infowindow = new kakao.maps.InfoWindow({{
                            content: '<div style="padding:5px;">{clinic_name}<br>{clinic_address}<br>전화: {clinic_phone}</div>'
                        }});
                        kakao.maps.event.addListener(marker, 'mouseover', function() {{
                            infowindow.open(map, marker);
                        }});
                        kakao.maps.event.addListener(marker, 'mouseout', function() {{
                            infowindow.close();
                        }});
                        """

                html_code = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>카카오 지도</title>
                    <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_API_KEY}"></script>
                </head>
                <body>
                    <div id="map" style="width: 100%; height: 500px;"></div>
                    <script>
                        var mapContainer = document.getElementById('map'), 
                            mapOption = {{
                                center: new kakao.maps.LatLng({latitude}, {longitude}),
                                level: 3
                            }};
                        var map = new kakao.maps.Map(mapContainer, mapOption);
    
                        {clinic_markers}
                    </script>
                </body>
                </html>
                """

                # 지도 표시
                components.html(html_code, height=500)

                # 가장 가까운 3곳의 안과 정보 출력
                if nearest_hospital:
                    # st.markdown("## 가장 가까운 병원 3곳 정보")
                    st.markdown(f"#### {search_type} {size}곳 정보")

                    # CSS 스타일 정의
                    st.markdown(
                        """
                        <style>
                        .card-container {
                            display: flex;
                            flex-direction: row;
                            gap: 20px; /* 카드 사이의 간격 */
                            justify-content: center; /* 카드 정렬 */
                            margin-top: 20px;
                        }
                        .card {
                            border: 1px solid #ccc; /* 회색 테두리 */
                            border-radius: 10px;
                            padding: 15px;
                            width: 300px; /* 카드의 고정 너비 */
                            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* 약간의 그림자 */
                            background-color: #fff; /* 카드 배경색 */
                        }
                        .card h4 {
                            margin: 0;
                            font-size: 18px;
                            color: #333;
                        }
                        .card p {
                            margin: 5px 0;
                            color: #555;
                            font-size: 14px;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    for i, clinic in enumerate(nearest_hospital, 1):
                        clinic_name = clinic["place_name"]
                        clinic_address = clinic.get("road_address_name")
                        clinic_phone = clinic.get("phone")
                        clinic_place_url = clinic.get("place_url")
                        clinic_lat = clinic["y"]
                        clinic_lng = clinic["x"]
                        clinic_rating = clinic.get("rating")
                        clinic_rating_all = clinic.get("rating_all")

                        points = str(clinic.get("recommendation_points"))
                        result = points.replace("{", "").replace("}", "").replace("'", "")
                        clinic_points = result

                        if clinic_rating and clinic_rating_all:
                            st.write(f"**{i}. {clinic_name}** ⭐ {clinic_rating}({clinic_rating_all}) 👍 [{clinic_points}]")
                        elif clinic_rating:
                            st.write(f"**{i}. {clinic_name}** ⭐ {clinic_rating}  [{clinic_points}]")
                        elif search_type == "응급실":
                            st.write(f"**{i}. 🚨{clinic_name}**")
                        else:
                            st.write(f"**{i}. {clinic_name}**")

                        if clinic_address:
                            st.write(f"📍 {clinic_address}")

                        if clinic_phone:
                            st.write(f"📞 {clinic_phone}")

                        if clinic_place_url:
                            st.write(f"🌐 {clinic_place_url}")

                        # st.write(f"**위치**: 위도 {clinic_lat}, 경도 {clinic_lng}")
                        st.write("---")
                else:
                    st.info("가까운 병원이 없습니다. 조건을 다시 설정해주세요.")
            


    except Exception as e:
        st.error(f"오류 발생: {e}")

