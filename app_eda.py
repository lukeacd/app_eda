import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.logged_in:
            st.success(f"{st.session_state.user_email}님 환영합니다.")
        st.markdown(
            """
---
**Population Trends Dataset**  
- File: population_trends.csv  
- Description: Yearly and regional population, births, and deaths statistics  
"""
        )

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")

        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return

        # --- 기본 로드 및 공통 전처리 ---
        df = pd.read_csv(uploaded)
        df.replace('-', 0, inplace=True)
        # Region 한글→영문 매핑
        mapping = {
            '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju','대전':'Daejeon',
            '울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
            '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju','전국':'Nationwide'
        }
        df['Region'] = df['지역'].map(mapping)
        df['Year']   = pd.to_numeric(df['연도'], errors='coerce')
        df['Population'] = pd.to_numeric(df['인구'], errors='coerce')

        # 탭 생성
        tab_labels = ["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"]
        tabs = st.tabs(tab_labels)

        # --------------------- 탭 0: 기초 통계 ---------------------
        with tabs[0]:
            st.header("기초 통계 (Summary Statistics)")

            # Sejong 만 전처리
            df_sejong = df[df['Region'] == 'Sejong'].copy()
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df_sejong[col] = pd.to_numeric(df_sejong[col], errors='coerce')

            # 구조 출력
            buffer = io.StringIO()
            df_sejong.info(buf=buffer)
            st.subheader("Sejong DataFrame Info")
            st.text(buffer.getvalue())

            # 요약 통계
            st.subheader("Sejong Descriptive Statistics")
            st.dataframe(df_sejong[['인구','출생아수(명)','사망자수(명)']].describe())

        # --------------------- 탭 1: 연도별 추이 + 예측 ---------------------
        with tabs[1]:
            st.header("연도별 추이 + 2035년 예측 (Yearly Trend + Forecast)")

            df_nat = df[df['Region']=='Nationwide'].copy()
            for col in ['출생아수(명)','사망자수(명)']:
                df_nat[col] = pd.to_numeric(df_nat[col], errors='coerce')
            df_nat.sort_values('Year', inplace=True)

            # 최근 3년 순증가량 평균
            df_nat['net_change'] = df_nat['출생아수(명)'] - df_nat['사망자수(명)']
            avg_net = df_nat.tail(3)['net_change'].mean()

            # Forecast 생성
            last_year = int(df_nat['Year'].max())
            last_pop  = df_nat.loc[df_nat['Year']==last_year,'Population'].iat[0]
            years_pred = list(range(last_year+1, 2036))
            pops_pred  = []
            pop_temp   = last_pop
            for _ in years_pred:
                pop_temp += avg_net
                pops_pred.append(pop_temp)
            df_pred = pd.DataFrame({'Year': years_pred, 'Forecast': pops_pred})

            # 플롯
            fig, ax = plt.subplots()
            ax.plot(df_nat['Year'], df_nat['Population'], marker='o', label='History')
            ax.plot(df_pred['Year'], df_pred['Forecast'], marker='x', linestyle='--', label='Forecast')
            ax.set_title('Nationwide Population Trend')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend()
            st.pyplot(fig)

        # --------------------- 탭 2: 지역별 분석 + 5년 변화량 ---------------------
        with tabs[2]:
            st.header("지역별 분석 (Regional Analysis)")

            df_reg = df[df['Region']!='Nationwide'].copy()
            df_reg['Population'] = pd.to_numeric(df_reg['Population'], errors='coerce')

            # Pivot table
            pivot = df_reg.pivot(index='Region', columns='Year', values='Population')
            st.subheader("Population Pivot Table")
            st.dataframe(pivot)

            # 5년 변화량 & 비율
            max_year   = int(df_reg['Year'].max())
            start_year = max_year - 5
            pivot['change_5yr'] = pivot[max_year] - pivot[start_year]
            pivot['pct_5yr']    = pivot['change_5yr'] / pivot[start_year] * 100
            pivot_sorted = pivot.sort_values('change_5yr', ascending=False)

            # 수평 막대그래프
            fig1, ax1 = plt.subplots()
            sns.barplot(x=pivot_sorted['change_5yr']/1000, y=pivot_sorted.index, ax=ax1)
            ax1.set_title('5-Year Population Change by Region')
            ax1.set_xlabel('Change (Thousands)')
            ax1.set_ylabel('Region')
            for p in ax1.patches:
                ax1.text(p.get_width()+0.1, p.get_y()+p.get_height()/2, f"{p.get_width():.1f}", va='center')
            st.pyplot(fig1)

            # 변화율 막대그래프
            fig2, ax2 = plt.subplots()
            sns.barplot(x=pivot_sorted['pct_5yr'], y=pivot_sorted.index, ax=ax2)
            ax2.set_title('5-Year % Population Change by Region')
            ax2.set_xlabel('% Change')
            ax2.set_ylabel('Region')
            for p in ax2.patches:
                ax2.text(p.get_width()+0.5, p.get_y()+p.get_height()/2, f"{p.get_width():.1f}%", va='center')
            st.pyplot(fig2)

        # --------------------- 탭 3: 증감 상위 100 사례 ---------------------
        with tabs[3]:
            st.header("Top 100 Yearly Change Cases (Styled Table)")

            df_all = df.copy()
            df_all['Population'] = pd.to_numeric(df_all['Population'], errors='coerce')
            df_all.sort_values(['Region','Year'], inplace=True)
            df_all['diff'] = df_all.groupby('Region')['Population'].diff()

            top100 = (
                df_all.dropna(subset=['diff'])
                      .nlargest(100, 'diff')
                      [['Region','Year','diff']]
                      .rename(columns={'diff':'Change'})
            )

            def highlight(val):
                return 'background-color: #c6dbef' if val>0 else 'background-color: #fcbba1'

            styled = (
                top100.style
                      .format({'Change':'{:,.0f}'})
                      .applymap(highlight, subset=['Change'])
                      .set_caption("Top 100 Population Changes")
            )
            st.dataframe(styled)

        # --------------------- 탭 4: 누적 영역 시각화 ---------------------
        with tabs[4]:
            st.header("시각화 (Visualization)")

            df_area = df[df['Region']!='Nationwide'].copy()
            df_area['Population'] = pd.to_numeric(df_area['Population'], errors='coerce')
            area_df = df_area.pivot(index='Year', columns='Region', values='Population')

            fig3, ax3 = plt.subplots(figsize=(10,6))
            colors = sns.color_palette('tab20', n_colors=area_df.shape[1])
            area_df.plot(kind='area', ax=ax3, stacked=True, color=colors)
            ax3.set_title('Population by Region Over Years')
            ax3.set_xlabel('Year')
            ax3.set_ylabel('Population')
            ax3.legend(title='Region', bbox_to_anchor=(1.05,1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig3)



# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()