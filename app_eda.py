import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ===== 네비게이션용 스텁 정의 시작 =====
def Login():
    st.header("🔐 로그인")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.logged_in = True
            st.session_state.id_token = user['idToken']
            st.session_state.user_email = email
            uid = user['localId']
            user_data = firestore.child("users").child(uid).get(st.session_state.id_token).val()
            st.session_state.user_name = user_data.get("name", "")
            st.session_state.user_gender = user_data.get("gender", "")
            st.session_state.user_phone = user_data.get("phone", "")
            st.success("로그인 성공!")
            st.experimental_rerun()
        except Exception:
            st.error("로그인 실패: 이메일 또는 비밀번호를 확인하세요.")

def Register(prev_url):
    st.header("📝 회원가입")
    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm Password", type="password")
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["","Male","Female","Other"])
        phone = st.text_input("Phone")
        submitted = st.form_submit_button("Register")
    if submitted:
        if password != password2:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                uid = user['localId']
                token = user['idToken']
                firestore.child("users").child(uid).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone
                }, token)
                st.success("회원가입 완료! 로그인 페이지로 이동합니다.")
                st.experimental_rerun()
            except Exception as e:
                msg = str(e)
                if 'EMAIL_EXISTS' in msg:
                    st.error("이미 사용 중인 이메일입니다. 다른 이메일을 사용해주세요.")
                else:
                    st.error(f"회원가입 오류: {msg}")

def FindPassword():
    st.header("🔎 비밀번호 찾기")
    with st.form("pw_form"):
        email = st.text_input("Email")
        submitted = st.form_submit_button("Send Reset Email")
    if submitted:
        try:
            auth.send_password_reset_email(email)
            st.success("비밀번호 재설정 이메일이 발송되었습니다.")
        except Exception:
            st.error("이메일 전송 중 오류가 발생했습니다.")

def UserInfo():
    st.header("👤 내 정보")
    if not st.session_state.logged_in:
        st.warning("먼저 로그인해 주세요.")
    else:
        st.write(f"**Email:** {st.session_state.user_email}")
        st.write(f"**Name:** {st.session_state.user_name}")
        st.write(f"**Gender:** {st.session_state.user_gender}")
        st.write(f"**Phone:** {st.session_state.user_phone}")

def Logout():
    st.session_state.clear()
    st.success("로그아웃 되었습니다.")
    st.experimental_rerun()

# Firebase 설정
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798-firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.logged_in:
            st.success(f"{st.session_state.user_email}님 환영합니다.")
        st.markdown("""
---
**Population Trends Dataset**  
- File: `population_trends.csv`  
- Description: Yearly and regional population, births, and deaths statistics  
"""
        )

class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return
        df = pd.read_csv(uploaded)
        df.replace('-', 0, inplace=True)
        df['Population'] = pd.to_numeric(df['인구'], errors='coerce')
        df['Year'] = df['연도']
        df['Region_KR'] = df['지역']
        mapping = {
            '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju','대전':'Daejeon',
            '울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
            '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju','전국':'Nationwide'
        }
        df['Region'] = df['Region_KR'].map(mapping)
        tab_labels = ["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"]
        tabs = st.tabs(tab_labels)
        with tabs[0]:
            st.header("기초 통계 (Summary Statistics)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.subheader("DataFrame Info")
            st.text(buffer.getvalue())
            st.subheader("Descriptive Statistics")
            st.dataframe(df[['Population']].describe())
        with tabs[1]:
            st.header("연도별 추이 (Yearly Trend)")
            df_nat = df[df['Region']=='Nationwide'].sort_values('Year')
            fig, ax = plt.subplots()
            ax.plot(df_nat['Year'], df_nat['Population'], marker='o')
            ax.set_title('Nationwide Population Trend')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            st.pyplot(fig)
        with tabs[2]:
            st.header("지역별 분석 (Regional Analysis)")
            df_reg = df[df['Region']!='Nationwide'].copy()
            pivot = df_reg.pivot(index='Region', columns='Year', values='Population')
            st.subheader("Population Pivot Table")
            st.dataframe(pivot.style.format(",.0f"))
        with tabs[3]:
            st.header("변화량 분석 (Change Analysis)")
            df_reg.sort_values(['Region','Year'], inplace=True)
            df_reg['diff'] = df_reg.groupby('Region')['Population'].diff()
            top_diff = df_reg.dropna(subset=['diff']).nlargest(100, 'diff')
            st.subheader("Top 100 Yearly Increase Cases")
            st.dataframe(
                top_diff[['Region','Year','diff']]
                .rename(columns={'diff':'Change'})
                .style.format({'Change':",.0f"})
            )
        with tabs[4]:
            st.header("시각화 (Visualization)")
            df_area = df[df['Region']!='Nationwide']
            area_df = df_area.pivot(index='Year', columns='Region', values='Population')
            fig2, ax2 = plt.subplots(figsize=(10,6))
            colors = sns.color_palette('tab20', n_colors=area_df.shape[1])
            area_df.plot(kind='area', ax=ax2, stacked=True, color=colors)
            ax2.set_title('Population by Region Over Years')
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Population')
            ax2.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig2)
# 페이지 네비게이션
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]
selected_page = st.navigation(pages)
selected_page.run()
