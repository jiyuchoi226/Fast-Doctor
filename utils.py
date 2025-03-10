import os
from openai import OpenAI
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key="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"
    # This is the default and can be omitted
    # api_key=os.environ.get("OPENAI_API_KEY")
)


def predict_disease(symptom):
    """AI 모델을 통해 증상에 따른 병명을 예측."""
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": f"""
                                            사용자의 증상은 '{symptom}'입니다.   
                                            아래에 따라 대답해.:
                                            1. 증상에 기반한 가능한 병명을 제시하세요.
                                            줄 바꾸세요.
                                            2. 추가로 고려해야 할 건강 문제를 나열하세요.
                                            줄 바꾸세요.
                                             [
                                                내과,
                                                외과,
                                                소아과,
                                                산부인과, 
                                                정신건강과,
                                                정신과,
                                                피부과,
                                                클리닉,
                                                안과,
                                                이비인후과,
                                                치과,
                                                재활의학과,                                                 
                                                영상의학과,
                                                핵의학과,
                                                병리과,
                                                진단검사의학과,-
                                                가정의학과,
                                                응급의학과,
                                                직업환경의학과,
                                                예방의학과,
                                                중환자의학과,
                                                종양내과,
                                                방사선종양학과,
                                                암센터,
                                                마취통증의학과,
                                                노인의학과,
                                                스포츠의학과,
                                                한방진료과
                                                ]
                                            3. 목록에서 진료 받을 수 있는 과를 제시하세요.
                                            """}
            ],
            model="gpt-3.5-turbo",
            temperature=0
        )

        # 응답 내용 추출
        content = response.choices[0].message.content
        if content:
            return content.strip()
        else:
            return "모델이 병명을 예측하지 못했습니다."
    except Exception as e:
        return f"AI 분석 실패: {e}"


def predict_medical(symptom, check, size):
    """AI 모델을 통해 증상에 따른 병명을 예측."""
    try:
        if check == "medicals":
            response = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": f"""
                                                사용자의 증상은 '{symptom}'입니다.   
                                                아래의 목록에서 해당 증상을 진료할 수 있는 **단 하나의 과만 선택하여 답변하세요.

                                                목록:
                                                [내과,
                                                외과,
                                                소아과,
                                                산부인과, 
                                                정신건강과,
                                                정신과,
                                                피부과,
                                                클리닉,
                                                안과,
                                                이비인후과,
                                                치과,
                                                재활의학과,                                                 
                                                영상의학과,
                                                핵의학과,
                                                병리과,
                                                진단검사의학과,
                                                가정의학과,
                                                응급의학과,
                                                직업환경의학과,
                                                예방의학과,
                                                중환자의학과,
                                                종양내과,
                                                방사선종양학과,
                                                암센터,
                                                마취통증의학과,
                                                노인의학과,
                                                스포츠의학과,
                                                한방진료과]

                                                규칙:
                                                1. 증상에 가장 적합한 진료과 1개만 선택하세요.
                                                2. 추가 설명은 하지 않고, 선택한 진료과의 이름만 답변하세요.
                                                """}
                ],
                model="gpt-3.5-turbo",
                temperature=0
            )
        else:
            response = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": f"""
                                                사용자의 증상은 '{symptom}'입니다. 
                                                사용자의 증상과 관련된 진료과를 판단한 뒤, 
                                                해당 진료과에서 현재 위치의 {check}Km 반경 내에서  
                                                **추천 수가 가장 높은 병원 이름** {size}곳을 제시하세요.  
                                                답변은 병원 이름만 나열하세요. 추가적인 설명은 하지 마세요.  
                                                """}
                ],
                model="gpt-3.5-turbo",
                temperature=0
            )
        # 응답 내용 추출
        content = response.choices[0].message.content
        if content:
            return content.strip()
        else:
            return "모델이 병명을 예측하지 못했습니다."
    except Exception as e:
        return f"AI 분석 실패: {e}"