import streamlit as st
import re

# ------------------- 감정 키워드 사전 -------------------
EMOTION_KEYWORDS = {
    "joy": [
        "great", "good", "love", "nice", "really", "price", "recommend", "buy",
        "looks", "perfect", "happy", "best", "looking", "feel", "fine", "lot", "purchased",
        "makes", "worth", "day", "easy", "fits", "quality", "protection", "satisfied"
    ],
    "anger": [
        "problem", "doesnt", "did", "didnt", "broken", "bad", "waste", "hard",
        "worst", "poor", "hate", "issue"
    ],
    "sad": [
        "sad", "broken", "waste", "poor", "didnt", "unhappy",
        "disappointed", "regret"
    ],
    "surprise": [
        "surprise", "wow", "unexpected", "amazed", "astonishing", "shocked", "unbelievable"
    ]
}
EMOTIONS = list(EMOTION_KEYWORDS.keys())

# ------------------- 전각/반각 변환 함수 -------------------
def to_halfwidth(s):
    result = ""
    for c in s:
        code = ord(c)
        if code == 12288:  # 전각 스페이스
            result += chr(32)
        elif 65281 <= code <= 65374:
            result += chr(code - 65248)
        else:
            result += c
    return result

# ------------------- 감정 분석 함수 -------------------
def rule_based_emotion(text):
    # 1. 전각 → 반각 변환, 2. 소문자, 3. 토큰 분리
    text = to_halfwidth(str(text)).lower()
    tokens = re.findall(r'\b\w+\b', text)
    found = []
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in tokens:
                found.append(emotion)
    # 여러 감정 발견 시 우선순위 적용
    for emo in ['anger', 'sad', 'joy', 'surprise']:
        if emo in found:
            return emo
    return "neutral"

# ------------------- 샘플 상품 리스트 -------------------
PRODUCTS = [
    {"asin": "A1", "name": "Phone Case", "desc": "Protect your phone with style."},
    {"asin": "A2", "name": "Wireless Charger", "desc": "Charge without cables."},
    {"asin": "A3", "name": "Earphones", "desc": "Enjoy quality sound on the go."},
    {"asin": "A4", "name": "Screen Protector", "desc": "Keep your screen scratch-free."}
]

# ------------------- 리뷰 데이터 저장용 (세션) -------------------
if "reviews" not in st.session_state:
    st.session_state.reviews = []  # [{"user":..., "asin":..., "review":..., "emotion":...}]
if "user_blacklist" not in st.session_state:
    st.session_state.user_blacklist = {}  # {username: [asin1, asin2, ...]}

# ------------------- 메인 UI -------------------
st.title("🛒 Mini Emotion-Aware Shopping Mall Demo")
st.header("Products")

for idx, prod in enumerate(PRODUCTS):
    st.subheader(prod["name"])
    st.caption(prod["desc"])
    if st.button(f"View Details {prod['name']}", key=f"btn_{prod['asin']}"):
        st.session_state["selected_product"] = prod["asin"]

# ------------------- 상품 상세/리뷰 입력 -------------------
if "selected_product" in st.session_state:
    asin = st.session_state["selected_product"]
    prod = next(p for p in PRODUCTS if p["asin"] == asin)
    st.markdown("---")
    st.header(f"Product Detail: {prod['name']}")
    st.write(prod["desc"])

    # 리뷰 남기기
    st.markdown("**Your Name**")
    username = st.text_input("User Name", value="김민지", key="review_username")
    st.markdown("**Leave a Review**")
    review_text = st.text_area("Type your review here", value="", key="review_text")

    if st.button("Submit Review", key="submit_review"):
        emotion = rule_based_emotion(review_text)
        st.session_state.reviews.append({
            "user": username, "asin": asin, "review": review_text, "emotion": emotion
        })
        # 부정 감정(anger, sad) 남기면 블랙리스트에 추가
        if emotion in ["anger", "sad"]:
            st.session_state.user_blacklist.setdefault(username, []).append(asin)
        st.success(f"Review submitted! 감정 분석 결과: **{emotion.upper()}**")

    # 기존 리뷰 보기
    st.markdown("---")
    st.markdown("**Reviews**")
    reviews = [r for r in st.session_state.reviews if r["asin"] == asin]
    if reviews:
        for r in reviews:
            st.write(f"- {r['user']} ({r['emotion']}) : {r['review']}")
    else:
        st.write("No reviews yet.")

# ------------------- 맞춤형 추천 + Diversity(필터버블 완화) -------------------
st.markdown("---")
st.header("🔎 Personalized Recommendations")
username = st.text_input("Enter your name for recommendations", value="김민지", key="recommend_name")
diversity = st.slider("Diversity Ratio (필터버블 완화)", 0.0, 1.0, 0.0, 0.05, key="diversity_slider")

if st.button("Show My Recommendations", key="show_recs"):
    # 1. 블랙리스트 상품 제외(부정 감정 남긴 상품)
    blacklist = st.session_state.user_blacklist.get(username, [])
    non_black_products = [p for p in PRODUCTS if p["asin"] not in blacklist]
    # 2. Diversity 비율에 따라 랜덤 추천도 일부 추가
    import random
    n_diverse = int(len(PRODUCTS) * diversity)
    diverse_items = random.sample([p for p in PRODUCTS if p["asin"] not in [prod["asin"] for prod in non_black_products]], k=min(n_diverse, len(PRODUCTS)-len(non_black_products)))
    recs = non_black_products + diverse_items
    # 중복 방지
    recs = {p["asin"]: p for p in recs}.values()
    st.subheader(f"Recommended Products for {username}")
    for prod in recs:
        st.write(f"- {prod['name']}: {prod['desc']}")
    if not recs:
        st.info("모든 상품이 블랙리스트 처리되어 추천이 없습니다.")

# ------------------- 끝 -------------------
st.markdown("""
---
*전각문자, 감정 키워드, Diversity 슬라이더, 블랙리스트(회피 추천) 등 실제 서비스 수준의 주요 기능 샘플 구현입니다!*
""")
