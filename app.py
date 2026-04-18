import streamlit as st
from ai_engine import analyze_emails

st.set_page_config(
    page_title="Opportunity Inbox Copilot",
    page_icon="📬",
    layout="wide"
)

st.markdown("""<style>
    .main-title { font-size: 38px; font-weight: 700; color: #4F8BF9; text-align: center; }
    .sub-title { font-size: 16px; color: #888; text-align: center; margin-bottom: 20px; }
    .card { background-color: #1E1E2E; border-radius: 12px; padding: 20px; 
            border-left: 4px solid #4F8BF9; margin-bottom: 12px; }
    .rank-1 { border-left: 4px solid #FFD700; }
    .rank-2 { border-left: 4px solid #C0C0C0; }
    .rank-3 { border-left: 4px solid #CD7F32; }
    .urgent { color: #FF4B4B; font-weight: 600; }
    .tag { display: inline-block; padding: 2px 10px; border-radius: 20px; 
           font-size: 12px; margin: 2px; }
</style>""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<p class="main-title">📬 Opportunity Inbox Copilot</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Paste your emails · Fill your profile · Get your ranked opportunity list</p>', unsafe_allow_html=True)
st.markdown("---")

# --- TWO COLUMN LAYOUT ---
left_col, right_col = st.columns([1, 1])

# =====================
# LEFT: EMAIL INPUT
# =====================
with left_col:
    st.markdown("### 📧 Step 1 — Paste Your Emails")
    st.caption("Paste 5–15 emails separated by '---' between each email")
    
    emails_input = st.text_area(
        label="Paste emails here",
        height=300,
        placeholder="""Subject: Google Summer Internship 2026
Deadline: May 15, 2026
We are looking for CS students with Python skills...

---

Subject: DAAD Scholarship for Pakistani Students
Deadline: June 30, 2026
Eligibility: CGPA above 3.0...""",
        label_visibility="collapsed"
    )
    
    st.markdown("### 👤 Step 2 — Your Student Profile")
    
    # Row 1
    c1, c2 = st.columns(2)
    with c1:
        degree = st.selectbox("Degree", ["BS", "MS", "PhD"])
        semester = st.selectbox("Semester", ["1st","2nd","3rd","4th","5th","6th","7th","8th"])
    with c2:
        cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, value=3.2, step=0.1)
        program = st.text_input("Program", placeholder="e.g. Computer Science")
    
    # Row 2
    skills = st.text_input("Skills & Interests", placeholder="e.g. Python, AI, Web Dev, Data Science")
    
    opp_types = st.multiselect(
        "Preferred Opportunity Types",
        ["Internship", "Scholarship", "Fellowship", "Competition", "Research", "Admission"],
        default=["Internship", "Scholarship"]
    )
    
    c3, c4 = st.columns(2)
    with c3:
        financial_need = st.selectbox("Financial Need", ["Low", "Medium", "High"])
    with c4:
        location = st.selectbox("Location Preference", ["Pakistan", "International", "Both"])
    
    experience = st.text_area("Past Experience (brief)", height=80,
                               placeholder="e.g. 1 internship at startup, won ICPC regionals...")

# =====================
# RIGHT: RESULTS
# =====================
with right_col:
    st.markdown("### 🏆 Step 3 — Your Ranked Opportunities")
    
    analyze_btn = st.button("🚀 Analyze My Inbox", use_container_width=True, type="primary")
    
    if analyze_btn:
        if not emails_input.strip():
            st.error("❌ Please paste at least one email first!")
        else:
            with st.spinner("🤖 AI is reading your emails..."):
                # Build student profile from form inputs
                profile = {
                    "degree": degree,
                    "semester": semester,
                    "cgpa": cgpa,
                    "program": program,
                    "skills": skills,
                    "opp_types": opp_types,
                    "financial_need": financial_need,
                    "location": location,
                    "experience": experience
                }

                # Call the AI engine
                results = analyze_emails(emails_input, profile)

                if not results:
                    st.warning("⚠️ No valid opportunities found in your emails. They might be spam or non-opportunity content.")
                else:
                    st.markdown("---")
                
                for r in results:
                    rank_class = f"rank-{r['rank']}" if r['rank'] <= 3 else "card"
                    medal = "🥇" if r['rank']==1 else "🥈" if r['rank']==2 else "🥉" if r['rank']==3 else f"#{r['rank']}"
                    urgency_color = "#FF4B4B" if r['urgency']=="HIGH" else "#FFA500" if r['urgency']=="MEDIUM" else "#4CAF50"
                    
                    st.markdown(f"""
                    <div class="card {rank_class}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:18px; font-weight:700; color:#fff;">{medal} {r['title']}</span>
                            <span style="font-size:22px; font-weight:800; color:#4F8BF9;">{r['match_score']}%</span>
                        </div>
                        <div style="margin:6px 0;">
                            <span style="background:#2a2a3e; color:#aaa; padding:2px 10px; border-radius:20px; font-size:12px; margin-right:6px;">📁 {r['type']}</span>
                            <span style="background:#2a2a3e; color:#aaa; padding:2px 10px; border-radius:20px; font-size:12px; margin-right:6px;">📅 {r['deadline']}</span>
                            <span style="background:#2a2a3e; color:{urgency_color}; padding:2px 10px; border-radius:20px; font-size:12px;">⚡ {r['urgency']} URGENCY</span>
                        </div>
                        <div style="color:#ccc; font-size:13px; margin:8px 0;">💡 <b>Why it matters:</b> {r['why_matters']}</div>
                        <div style="color:#ccc; font-size:13px; margin:4px 0;">📋 <b>Requirements:</b> {', '.join(r['requirements'])}</div>
                        <div style="color:#4F8BF9; font-size:13px; margin-top:8px;">➡️ <b>Next step:</b> {r['next_steps']}</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        # Empty state
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; border:2px dashed #4F8BF9; 
                    border-radius:15px; color:#888; margin-top:20px;">
            <div style="font-size:50px;">📬</div>
            <div style="font-size:18px; color:#ccc; margin-top:10px;">
                Fill in your profile and paste your emails
            </div>
            <div style="font-size:13px; margin-top:8px;">
                AI will rank your opportunities instantly
            </div>
        </div>
        """, unsafe_allow_html=True)