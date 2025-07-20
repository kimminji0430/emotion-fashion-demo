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

# ------------------- 감정 분석 함수 -------------------

import unicodedata

def rule_based_emotion(text):
    text = unicodedata.normalize("NFKC", str(text).lower())  # ← 여기!
    tokens = re.findall(r'\b\w+\b', text)
    found = []
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in tokens:
                found.append(emotion)
    for emo in ['anger', 'sad', 'joy', 'surprise']:
        if emo in found:
            return emo
    return "neutral"

# ------------------- 샘플 상품 -------------------
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

# ------------------- UI -------------------
st.title("🛒 Mini Emotion-Aware Shopping Mall Demo")
st.header("Products")

for idx, prod in enumerate(PRODUCTS):
    st.subheader(prod["name"])
    st.caption(prod["desc"])
    if st.button(f"View Details {prod['name']}", key=f"btn_{prod['asin']}"):
        st.session_state["selected_product"] = prod["asin"]

if "selected_product" in st.session_state:
    asin = st.session_state["selected_product"]
    prod = next(p for p in PRODUCTS if p["asin"] == asin)
    st.markdown("---")
    st.header(f"Product Detail: {prod['name']}")
    st.write(prod["desc"])

    # 리뷰 남기기
    st.markdown("**Your Name**")
    username = st.text_input("User Name", value="김민지")
    st.markdown("**Leave a Review**")
    review_text = st.text_area("Type your review here", value="")

    if st.button("Submit Review"):
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

# ------------------- 맞춤형 추천 -------------------
st.markdown("---")
st.header("🔎 Personalized Recommendations")
username = st.text_input("Enter your name for recommendations", value="김민지", key="recommend_name")

if st.button("Show My Recommendations"):
    # 사용자가 부정 감정(anger/sad) 남긴 상품 제외
    blacklist = st.session_state.user_blacklist.get(username, [])
    recs = [p for p in PRODUCTS if p["asin"] not in blacklist]
    st.subheader(f"Recommended Products for {username}")
    for prod in recs:
        st.write(f"- {prod['name']}: {prod['desc']}")
    if not recs:
        st.info("모든 상품이 블랙리스트 처리되어 추천이 없습니다.")
diversity = st.slider("Diversity Ratio (필터버블 완화)", 0.0, 1.0, 0.2, 0.05)

if st.button("Show My Recommendations"):
    blacklist = st.session_state.user_blacklist.get(username, [])
    n_total = 5
    n_main = int(n_total * (1 - diversity))
    n_diverse = n_total - n_main

    # 감정 기반 추천
    recs_main = [p for p in PRODUCTS if p["asin"] not in blacklist][:n_main]

    # 남은 상품 중 랜덤 추천
    rest = [p for p in PRODUCTS if p["asin"] not in blacklist and p not in recs_main]
    import random
    random.shuffle(rest)
    recs_diverse = rest[:n_diverse]

    recs = recs_main + recs_diverse
    st.subheader(f"Recommended Products for {username}")
    for prod in recs:
        st.write(f"- {prod['name']}: {prod['desc']}")


# (추가 확장: 감정/키워드별 추천, diversity 등 원하면 안내!)
