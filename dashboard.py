# ============================================================
# dashboard.py
# Monitoring dashboard untuk AI Code Reviewer
#
# Cara jalankan: streamlit run dashboard.py
# ============================================================

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Code Reviewer Dashboard",
    page_icon="🤖",
    layout="wide",
)

# ============================================================
# LOAD DATA DARI DATABASE
# ============================================================
def load_data():
    """Load review history dari database"""
    # Coba SUPABASE_URL dulu, kalau tidak ada coba DATABASE_URL
    db_url = os.getenv("SUPABASE_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        return None

    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT id, repo_name, pr_number, pr_title, review_result, created_at FROM review_history ORDER BY created_at DESC"
            ))
            rows = result.fetchall()
            if not rows:
                return None
            df = pd.DataFrame(rows, columns=['id', 'repo_name', 'pr_number', 'pr_title', 'review_result', 'created_at'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def generate_sample_data():
    """Generate sample data kalau database kosong"""
    import random
    now = datetime.now()
    data = []
    issue_types = ['SQL Injection', 'Hardcoded Secret', 'No Error Handling',
                   'Division by Zero', 'Memory Leak', 'Poor Naming', 'Missing Validation']
    repos = ['Kesyaw/ai-code-reviewer', 'Kesyaw/web-app', 'Kesyaw/api-service']

    for i in range(50):
        created = now - timedelta(days=random.randint(0, 30),
                                  hours=random.randint(0, 23))
        issue = random.choice(issue_types)
        data.append({
            'id': i + 1,
            'repo_name': random.choice(repos),
            'pr_number': random.randint(1, 100),
            'pr_title': f'feat: {random.choice(["add feature", "fix bug", "refactor code", "update deps"])}',
            'review_result': f'**Security Issues**\n[SEVERITY: HIGH] {issue}: Found in the code.',
            'created_at': created,
        })

    return pd.DataFrame(data)

def classify_issues(review_text):
    """Classify jenis issue dari teks review"""
    issues = []
    text_lower = review_text.lower()
    if 'sql injection' in text_lower:
        issues.append('SQL Injection')
    if 'hardcoded' in text_lower or 'password' in text_lower or 'secret' in text_lower:
        issues.append('Hardcoded Secret')
    if 'error handling' in text_lower or 'exception' in text_lower:
        issues.append('No Error Handling')
    if 'division by zero' in text_lower:
        issues.append('Division by Zero')
    if 'memory leak' in text_lower:
        issues.append('Memory Leak')
    if 'performance' in text_lower or 'n+1' in text_lower:
        issues.append('Performance Issue')
    if 'security' in text_lower:
        issues.append('Security Issue')
    if not issues:
        issues.append('Code Quality')
    return issues

# ============================================================
# LOAD DATA
# ============================================================
df = load_data()
using_sample = False

if df is None or len(df) == 0:
    df = generate_sample_data()
    using_sample = True

# ============================================================
# HEADER
# ============================================================
st.title("🤖 AI Code Reviewer Dashboard")
st.markdown("Monitoring semua Pull Request yang direview oleh AI Agent")

if using_sample:
    st.info("📊 Menampilkan sample data — hubungkan database untuk data real")

st.divider()

# ============================================================
# METRICS ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)

total_reviews = len(df)
today_reviews = len(df[df['created_at'].dt.date == datetime.now().date()])
this_week = len(df[df['created_at'] >= datetime.now() - timedelta(days=7)])
unique_repos = df['repo_name'].nunique()

with col1:
    st.metric("Total Reviews", total_reviews, delta=f"+{today_reviews} hari ini")
with col2:
    st.metric("Review Minggu Ini", this_week)
with col3:
    st.metric("Repositories", unique_repos)
with col4:
    avg_per_day = round(total_reviews / max((df['created_at'].max() - df['created_at'].min()).days, 1), 1)
    st.metric("Rata-rata per Hari", avg_per_day)

st.divider()

# ============================================================
# CHARTS ROW 1
# ============================================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Trend Review per Hari")
    daily = df.groupby(df['created_at'].dt.date).size().reset_index()
    daily.columns = ['date', 'count']
    daily = daily.sort_values('date')

    fig_trend = px.area(
        daily, x='date', y='count',
        color_discrete_sequence=['#667eea'],
        labels={'date': 'Tanggal', 'count': 'Jumlah Review'}
    )
    fig_trend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("🏷️ Jenis Issue Paling Sering")
    all_issues = []
    for review in df['review_result']:
        all_issues.extend(classify_issues(str(review)))

    issue_counts = pd.Series(all_issues).value_counts().reset_index()
    issue_counts.columns = ['issue', 'count']

    fig_issues = px.bar(
        issue_counts, x='count', y='issue',
        orientation='h',
        color='count',
        color_continuous_scale='Blues',
        labels={'count': 'Jumlah', 'issue': 'Jenis Issue'}
    )
    fig_issues.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_issues, use_container_width=True)

# ============================================================
# CHARTS ROW 2
# ============================================================
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("📦 Review per Repository")
    repo_counts = df['repo_name'].value_counts().reset_index()
    repo_counts.columns = ['repo', 'count']

    fig_repo = px.pie(
        repo_counts, values='count', names='repo',
        color_discrete_sequence=px.colors.sequential.Blues_r,
        hole=0.4,
    )
    fig_repo.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_repo, use_container_width=True)

with col_right2:
    st.subheader("📅 Heatmap Aktivitas")
    df['hour'] = df['created_at'].dt.hour
    df['day'] = df['created_at'].dt.day_name()

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = df.groupby(['day', 'hour']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='day', columns='hour', values='count').fillna(0)
    heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])

    fig_heat = px.imshow(
        heatmap_pivot,
        color_continuous_scale='Blues',
        labels=dict(x="Jam", y="Hari", color="Review"),
        aspect="auto",
    )
    fig_heat.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ============================================================
# RECENT REVIEWS TABLE
# ============================================================
st.subheader("📋 Recent Reviews")

# Filter
col_f1, col_f2 = st.columns(2)
with col_f1:
    repo_filter = st.selectbox(
        "Filter by repo",
        ["All"] + list(df['repo_name'].unique())
    )
with col_f2:
    days_filter = st.slider("Tampilkan N hari terakhir", 1, 30, 7)

filtered_df = df.copy()
if repo_filter != "All":
    filtered_df = filtered_df[filtered_df['repo_name'] == repo_filter]
filtered_df = filtered_df[
    filtered_df['created_at'] >= datetime.now() - timedelta(days=days_filter)
]

display_df = filtered_df[['created_at', 'repo_name', 'pr_number', 'pr_title']].copy()
display_df.columns = ['Waktu', 'Repository', 'PR #', 'Judul PR']
display_df['Waktu'] = display_df['Waktu'].dt.strftime('%Y-%m-%d %H:%M')
display_df = display_df.sort_values('Waktu', ascending=False)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ============================================================
# DETAIL REVIEW
# ============================================================
st.subheader("🔍 Detail Review")
if len(filtered_df) > 0:
    pr_options = [f"PR #{row['pr_number']} — {row['pr_title']}" for _, row in filtered_df.iterrows()]
    selected = st.selectbox("Pilih PR untuk lihat detail review:", pr_options)

    if selected:
        pr_num = int(selected.split('#')[1].split(' ')[0])
        review_row = filtered_df[filtered_df['pr_number'] == pr_num].iloc[0]
        st.markdown(f"**Repository:** {review_row['repo_name']}")
        st.markdown(f"**Waktu:** {review_row['created_at']}")
        st.markdown("**Hasil Review:**")
        st.markdown(review_row['review_result'])
else:
    st.info("Tidak ada review dalam periode yang dipilih")


# ============================================================
# AI REVIEW HISTORY — Full review text
# ============================================================
st.divider()
st.subheader("🤖 AI Review History")
st.markdown("Semua review yang pernah diposting oleh AI Agent ke GitHub PR")

for _, row in filtered_df.sort_values('created_at', ascending=False).iterrows():
    with st.expander(f"PR #{row['pr_number']} — {row['pr_title']} | {row['created_at'].strftime('%Y-%m-%d %H:%M')}"):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**Repository**")
            st.markdown(f"**PR Number**")
            st.markdown(f"**Waktu**")
        with col2:
            st.markdown(f"`{row['repo_name']}`")
            st.markdown(f"#{row['pr_number']}")
            st.markdown(f"{row['created_at'].strftime('%Y-%m-%d %H:%M')}")
        st.divider()
        st.markdown(row['review_result'])