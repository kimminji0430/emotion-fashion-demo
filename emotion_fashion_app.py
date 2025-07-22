import streamlit as st
import re
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

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
def rule_based_emotion(text):
    text = str(text).lower()
    # 전각문자(全角)을 반각(ASCII)으로 치환
    text = ''.join(chr(ord(c) - 0xfee0) if 0xff01 <= ord(c) <= 0xff5e else c for c in text)
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
    {"asin": "A4", "name": "Screen Protector", "desc": "Keep your screen scratch-free."},
    {"asin": "A5", "name": "Power Bank", "desc": "Portable power for your devices."}
]

# ------------------- 리뷰 데이터 저장 (세션) -------------------
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
    username = st.text_input("User Name", value="김민지", key="review_name")
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

# ------------------- 맞춤형 추천 -------------------
st.markdown("---")
st.header("🔎 Personalized Recommendations")
username_rec = st.text_input("Enter your name for recommendations", value="김민지", key="recommend_name")
diversity = st.slider("Diversity Ratio (필터버블 완화)", 0.0, 1.0, 0.2, 0.05)

if st.button("Show My Recommendations", key="show_recs"):
    # 감정 기반 추천
    blacklist = st.session_state.user_blacklist.get(username_rec, [])
    candidate = [p for p in PRODUCTS if p["asin"] not in blacklist]
    n_diverse = int(len(PRODUCTS) * diversity)
    n_rec = max(1, len(candidate) - n_diverse)
    # 감정 기반(블랙리스트 제외) + 무작위(다양성)
    recommend_items = candidate[:n_rec] + list(np.random.choice(PRODUCTS, n_diverse, replace=False))
    recommend_items = {p['asin']: p for p in recommend_items}.values()  # 중복 제거
    st.subheader(f"Recommended Products for {username_rec}")
    for prod in recommend_items:
        st.write(f"- {prod['name']}: {prod['desc']}")
    if not recommend_items:
        st.info("모든 상품이 블랙리스트 처리되어 추천이 없습니다.")

    # ------------------- 협업 필터링 추천 -------------------
    st.markdown("### 🤝 Collaborative Filtering (User-based)")
    # 1. 가짜 유저-상품-감정 매트릭스 생성
    if st.session_state.reviews:
        review_df = pd.DataFrame(st.session_state.reviews)
        labeler = LabelEncoder()
        review_df['emo_code'] = labeler.fit_transform(review_df['emotion'])
        # pivot table: user x item → emotion label(코드)
        matrix = review_df.pivot_table(index='user', columns='asin', values='emo_code', aggfunc='first').fillna(-1)
        if username_rec in matrix.index:
            sim = cosine_similarity([matrix.loc[username_rec]], matrix)[0]
            similar_users = matrix.index[np.argsort(sim)[::-1][1:3]].tolist()  # 본인 제외 Top 2
            st.write("Similar Users:", ', '.join(similar_users))
            # 비슷한 사용자가 joy 리뷰 많이 남긴 상품 추천
            joy_code = labeler.transform(['joy'])[0]
            rec_df = review_df[(review_df['user'].isin(similar_users)) & (review_df['emo_code'] == joy_code)]
            top_asins = rec_df['asin'].value_counts().index.tolist()
            if top_asins:
                st.write("Collaborative Filtering 추천:", ', '.join(top_asins))
            else:
                st.write("비슷한 사용자가 아직 joy 상품에 리뷰를 남기지 않았습니다.")
        else:
            st.write("아직 충분한 사용자 리뷰 데이터가 없습니다.")
    else:
        st.write("아직 리뷰 데이터가 없습니다.")

# (원하면 더 확장 가능: 감정/키워드 기반 추천, 상품 상세 키워드 클라우드 등)

