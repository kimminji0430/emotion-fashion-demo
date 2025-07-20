import streamlit as st
import pandas as pd
import json

# 1. 데이터 불러오기 (샘플 파일명)
@st.cache_data
def load_data():
    df = pd.read_csv('reviews_with_tfidf_emotion_sample.csv')
    with open('product_profiles.json', encoding='utf-8') as f:
        product_profiles = json.load(f)
    return df, product_profiles

df, product_profiles = load_data()
emotions = ['joy', 'anger', 'sad', 'surprise']

st.title("Emotion-aware Fashion Recommendation Demo")

# 2. 사용자 ID 선택
user_ids = df['reviewerID'].dropna().unique().tolist()
selected_user = st.selectbox("Select User ID", user_ids)

# 3. 추천 모드
rec_mode = st.selectbox("Recommendation Mode", ["Positive Only", "Exclude Negative", "All"])

# 4. (선택) 감정별 상위 키워드 확인
if st.checkbox("Show Top Keywords by Emotion"):
    st.subheader("Top Keywords by Emotion")
    for emo in emotions:
        # product_profiles를 활용해 모든 키워드 수집
        all_words = []
        for asin in df['asin'].unique():
            try:
                all_words += list(product_profiles[str(asin)][f'{emo}_keyword_counts'].keys())
            except:
                pass
        top_words = pd.Series(all_words).value_counts().head(10)
        st.write(f"**{emo.capitalize()}**: {', '.join(top_words.index)}")

# 5. 추천 시스템 (부정감정 상품 제외/포함)
st.header("Personalized Product Recommendation")

def get_negative_items(user_id):
    neg_emotions = ['anger', 'sad']
    user_neg_items = df[(df['reviewerID'] == user_id) & (df['emotion_pred'].isin(neg_emotions))]['asin'].unique().tolist()
    return user_neg_items

def recommend_products(user_id, top_n=5, exclude_negative=True):
    neg_items = get_negative_items(user_id) if exclude_negative else []
    joy_items = df[df['emotion_pred'] == 'joy']['asin'].value_counts().index.tolist()
    rec_items = [item for item in joy_items if item not in neg_items][:top_n]
    rec_df = df[df['asin'].isin(rec_items)][['asin', 'summary', 'reviewText', 'emotion_pred']].drop_duplicates('asin')
    return rec_df

if st.button("Show Recommendations"):
    exclude_negative = (rec_mode != "All")
    rec_df = recommend_products(selected_user, exclude_negative=(rec_mode=="Exclude Negative"))
    if rec_df.empty:
        st.warning("No suitable recommendations found.")
    else:
        st.write("**Recommended Products:**")
        st.dataframe(rec_df)

# 6. (선택) 상품별 감정 분포 차트
if st.checkbox("Show Emotion Distribution for Top Products"):
    item_emotion = df.groupby(['asin', 'emotion_pred']).size().unstack(fill_value=0)
    item_emotion = item_emotion.reindex(columns=emotions, fill_value=0)
    top_items = item_emotion.sum(axis=1).sort_values(ascending=False).head(5).index
    st.subheader("Top 5 Products - Review Distribution by Emotion")
    st.bar_chart(item_emotion.loc[top_items])

# 7. (선택) 상품별 대표 키워드(감정별)
if st.checkbox("Show Product Profile (Top 1)"):
    item_emotion = df.groupby(['asin', 'emotion_pred']).size().unstack(fill_value=0)
    item_emotion = item_emotion.reindex(columns=emotions, fill_value=0)
    top_items = item_emotion.sum(axis=1).sort_values(ascending=False).head(1).index
    asin_example = str(top_items[0])
    st.write(f"**ASIN: {asin_example} Product Profile:**")
    st.json(product_profiles[asin_example])

st.info("Made by Minji with Streamlit | think about it step-by-step.")
