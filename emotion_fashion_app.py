import streamlit as st
import pandas as pd
import json

# 샘플 상품 데이터 (id, 이름, 카테고리)
products = [
    {"asin": "A1", "name": "Phone Case", "category": "case"},
    {"asin": "A2", "name": "Wireless Charger", "category": "charger"},
    {"asin": "A3", "name": "Earphones", "category": "audio"},
    {"asin": "A4", "name": "Screen Protector", "category": "case"},
]
product_df = pd.DataFrame(products)

# 샘플 유저 리뷰 메모리(간단 데모, 실제는 DB/CSV)
if 'user_reviews' not in st.session_state:
    st.session_state.user_reviews = []

# Rule-based 감정 태깅
def rule_based_emotion(text):
    text = text.lower()
    if "good" in text or "love" in text or "happy" in text:
        return "joy"
    if "bad" in text or "angry" in text or "hate" in text:
        return "anger"
    return "neutral"

# 1. 상품 목록
st.title("Mini Emotion-Aware Shopping Mall Demo")
st.header("Products")
for _, row in product_df.iterrows():
    st.write(f"**{row['name']}**")
    if st.button(f"View Details: {row['name']}", key=row['asin']):
        st.session_state['current_product'] = row['asin']

# 2. 상세페이지 + 리뷰
if 'current_product' in st.session_state:
    asin = st.session_state['current_product']
    prod = product_df[product_df['asin']==asin].iloc[0]
    st.subheader(f"Product Detail: {prod['name']}")
    reviews = [r for r in st.session_state.user_reviews if r['asin']==asin]
    for r in reviews:
        st.write(f"{r['user']}: {r['text']} ({r['emotion']})")
    # 리뷰 작성
    user = st.text_input("Your Name")
    review_text = st.text_area("Leave a Review")
    if st.button("Submit Review"):
        emotion = rule_based_emotion(review_text)
        st.session_state.user_reviews.append({'asin':asin, 'user':user, 'text':review_text, 'emotion':emotion})
        st.success(f"Review added! (Detected emotion: {emotion})")

# 3. 추천(감정 기반)
st.header("Your Recommendations")
if st.session_state.user_reviews:
    user_name = st.session_state.user_reviews[-1]['user']
    neg_items = [r['asin'] for r in st.session_state.user_reviews if r['user']==user_name and r['emotion'] in ['anger', 'sad']]
    # 부정적 감정 남긴 상품 카테고리 제외!
    neg_cats = product_df[product_df['asin'].isin(neg_items)]['category'].unique()
    recs = product_df[~product_df['category'].isin(neg_cats)]
    st.write(f"Since you disliked {list(neg_cats)}, we recommend:")
    for _, row in recs.iterrows():
        st.write(f"- {row['name']}")
else:
    st.write("Leave a review to get recommendations!")
