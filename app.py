import streamlit as st
from ai_engine import analyze_emails

st.set_page_config(
    page_title="Inbox Copilot",
    page_icon="📬",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background-color: #F7F3EE !important; }
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden; }

.site-header {
    padding: 18px 40px;
    border-bottom: 1px solid #E0D8D0;
    background: #F7F3EE;
}
.site-logo { font-family: 'Playfair Display', serif; font-size: 20px; color: #2C2C2C; font-weight: 400; }
.site-logo em { color: #E8845A; font-style: normal; }

.intro-page { text-align: center; padding: 80px 24px 60px; background: #F7F3EE; }
.intro-eyebrow { font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: #C4B8AF; margin-bottom: 20px; }
.intro-h1 { font-family: 'Playfair Display', serif; font-size: 58px; line-height: 1.1; color: #2C2C2C; font-weight: 400; margin-bottom: 20px; }
.intro-h1 em { color: #E8845A; font-style: italic; }
.intro-p { font-size: 16px; color: #9A8E87; line-height: 1.75; max-width: 440px; margin: 0 auto 40px; font-weight: 300; }
.pill-row { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-bottom: 40px; }
.pill { background: #FFF8F3; border: 1px solid #EAE0D8; border-radius: 100px; padding: 7px 16px; font-size: 12px; color: #7A6F67; }

.slabel { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: #C4B8AF; font-weight: 600; margin: 24px 0 10px; display: block; }

.output-panel { background: #FFFCF9; border: 1px solid #E0D8D0; border-radius: 16px; padding: 32px; min-height: 500px; }
.output-panel-title { font-family: 'Playfair Display', serif; font-size: 13px; color: #C4B8AF; font-weight: 400; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 24px; padding-bottom: 14px; border-bottom: 1px solid #EDE8E3; }

.result-count { font-family: 'Playfair Display', serif; font-size: 22px; color: #2C2C2C; font-weight: 400; margin-bottom: 20px; }
.opp { display: flex; gap: 16px; padding: 18px 0; border-bottom: 1px solid #EDE8E3; align-items: flex-start; }
.opp:last-child { border-bottom: none; }
.opp-n { font-family: 'Playfair Display', serif; font-size: 26px; color: #E0D6CE; min-width: 30px; line-height: 1; }
.opp-n.g { color: #E8C97A; }
.opp-n.s { color: #B8C4CC; }
.opp-n.b { color: #D4A882; }
.opp-body { flex: 1; }
.opp-title { font-size: 14px; font-weight: 500; color: #2C2C2C; margin-bottom: 8px; line-height: 1.4; }
.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.t { font-size: 11px; font-weight: 500; padding: 3px 10px; border-radius: 100px; }
.t-type { background: #FFF0E8; color: #C4622A; }
.t-date { background: #F2EEF8; color: #8B64B8; }
.t-high { background: #FEF0F0; color: #CC4C4C; }
.t-medium { background: #FEF8EC; color: #B8891A; }
.t-low { background: #EDFAF3; color: #2E9E5E; }
.opp-why { font-size: 12px; color: #7A6F67; line-height: 1.55; margin-bottom: 4px; }
.opp-next { font-size: 12px; color: #E8845A; font-weight: 500; }
.opp-score { text-align: right; min-width: 48px; }
.opp-pct { font-family: 'Playfair Display', serif; font-size: 26px; color: #2C2C2C; line-height: 1; }
.opp-pct-lbl { font-size: 9px; color: #C4B8AF; text-transform: uppercase; letter-spacing: 0.06em; }

.empty { text-align: center; padding: 60px 0; }
.empty-icon { font-size: 44px; margin-bottom: 14px; }
.empty-txt { font-size: 13px; line-height: 1.7; color: #C4B8AF; }

.stTextArea > div > div > textarea {
    background: #FFFCF9 !important; border: 1.5px solid #D8CFC6 !important;
    border-radius: 12px !important; font-size: 13px !important; color: #2C2C2C !important;
    font-family: 'DM Sans', sans-serif !important; padding: 12px !important;
}
.stTextInput > div > div > input {
    background: #FFFCF9 !important; border: 1.5px solid #D8CFC6 !important;
    border-radius: 10px !important; font-size: 13px !important; color: #2C2C2C !important;
}
.stNumberInput > div > div > input {
    background: #FFFCF9 !important; border: 1.5px solid #D8CFC6 !important;
    border-radius: 10px !important; font-size: 13px !important;
}
div[data-baseweb="select"] > div {
    background: #FFFCF9 !important; border: 1.5px solid #D8CFC6 !important;
    border-radius: 10px !important; font-size: 13px !important;
}
div[data-baseweb="tag"] { background: #EDE8E3 !important; border-radius: 100px !important; }
.stButton > button {
    background: #2C2C2C !important; color: #F7F3EE !important; border: none !important;
    border-radius: 100px !important; font-size: 14px !important; font-weight: 500 !important;
    padding: 12px 28px !important; width: 100% !important;
    font-family: 'DM Sans', sans-serif !important;
    margin-bottom: 24px !important;
}
.stButton > button:hover { background: #E8845A !important; }
p, label { color: #9A8E87 !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "intro"

if st.session_state.page == "intro":
    st.markdown("""
    <div class="intro-page">
        <div class="intro-eyebrow">✦ Softec AI Hackathon 2026</div>
        <div class="intro-h1">Your inbox holds<br><em>opportunities</em><br>you are missing.</div>
        <div class="intro-p">Paste your emails, fill your profile — we find every real chance, ranked by what matters most for you right now.</div>
        <div class="pill-row">
            <div class="pill">📬 Spam filtered</div>
            <div class="pill">🎯 Personalized ranking</div>
            <div class="pill">⚡ Urgency alerts</div>
            <div class="pill">✅ Action checklist</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    _, mid, _ = st.columns([1.5, 1, 1.5])
    with mid:
        if st.button("Get started →"):
            st.session_state.page = "app"
            st.rerun()

else:
    st.markdown('<div class="site-header"><span class="site-logo">Inbox <em>Copilot</em></span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown('<span class="slabel">Step 1 — Paste Emails</span>', unsafe_allow_html=True)
        st.caption("Separate multiple emails with  ---")
        emails_input = st.text_area(
            label="e", height=200,
            placeholder="Subject: Google Summer of Code 2026\nDeadline: May 10, 2026\nWe need CS students with Python...\n\n---\n\nSubject: HEC Scholarship 2026\nEligibility: CGPA 3.0+...",
            label_visibility="collapsed"
        )
        st.markdown('<span class="slabel">Step 2 — Your Profile</span>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            degree = st.selectbox("Degree", ["BS", "MS", "PhD"])
            semester = st.selectbox("Semester", ["1st","2nd","3rd","4th","5th","6th","7th","8th"])
        with c2:
            cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, value=3.2, step=0.1)
            program = st.text_input("Program", placeholder="e.g. Computer Science")
        skills = st.text_input("Skills", placeholder="e.g. Python, React, Machine Learning")
        opp_types = st.multiselect(
            "Preferred Types",
            ["Internship","Scholarship","Fellowship","Competition","Research","Admission"],
            default=["Internship","Scholarship"]
        )
        c3, c4 = st.columns(2)
        with c3:
            financial_need = st.selectbox("Financial Need", ["Low","Medium","High"])
        with c4:
            location = st.selectbox("Location", ["Pakistan","International","Both"])
        experience = st.text_area("Past Experience", height=68,
                                   placeholder="e.g. Interned at startup, won ICPC regionals...")
        st.markdown("<br>", unsafe_allow_html=True)
        go = st.button("Analyze my inbox →")
        st.markdown("<br><br>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="output-panel">', unsafe_allow_html=True)
        st.markdown('<div class="output-panel-title">📬 Results</div>', unsafe_allow_html=True)

        if go:
            if not emails_input.strip():
                st.error("Please paste at least one email.")
            else:
                with st.spinner("Reading your emails..."):
                    profile = {
                        "degree": degree, "semester": semester,
                        "cgpa": cgpa, "program": program,
                        "skills": skills, "opp_types": opp_types,
                        "financial_need": financial_need,
                        "location": location, "experience": experience
                    }
                    results = analyze_emails(emails_input, profile)

                if not results:
                    st.markdown('<div class="empty"><div class="empty-icon">🔍</div><div class="empty-txt">No real opportunities found.<br>Try more detailed emails.</div></div>', unsafe_allow_html=True)
                else:
                    n = len(results)
                    st.markdown(f'<div class="result-count">Found {n} opportunit{"y" if n==1 else "ies"}</div>', unsafe_allow_html=True)
                    for r in results:
                        rk = r['rank']
                        nc = "g" if rk==1 else "s" if rk==2 else "b" if rk==3 else ""
                        urg = r['urgency'].upper()
                        uc = f"t-{urg.lower()}"
                        reqs = " · ".join(r.get('requirements',[])[:3]) or "—"
                        st.markdown(f"""
                        <div class="opp">
                            <div class="opp-n {nc}">{rk}</div>
                            <div class="opp-body">
                                <div class="opp-title">{r['title']}</div>
                                <div class="tags">
                                    <span class="t t-type">{r['type']}</span>
                                    <span class="t t-date">📅 {r['deadline']}</span>
                                    <span class="t {uc}">⚡ {urg}</span>
                                </div>
                                <div class="opp-why">💡 {r['why_matters']}</div>
                                <div class="opp-why">📋 {reqs}</div>
                                <div class="opp-next">→ {r['next_steps']}</div>
                            </div>
                            <div class="opp-score">
                                <div class="opp-pct">{r['match_score']}</div>
                                <div class="opp-pct-lbl">match %</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty"><div class="empty-icon">📬</div><div class="empty-txt">Fill your profile and paste your emails,<br>then hit Analyze.</div></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
