"""
=============================================================================
INTERNSHIP TRACKER DASHBOARD 
=============================================================================
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys
from selenium.webdriver.common.by import By

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Internship Tracker Dashboard",
    page_icon="💼",
    layout="wide"
)

if 'scraping' not in st.session_state:
    st.session_state.scraping = False
if 'scrape_results' not in st.session_state:
    st.session_state.scrape_results = None

st.title("💼 Internship Tracker Dashboard")
st.markdown("---")

@st.cache_data
def load_internships():
    if os.path.exists('internships.csv'):
        # FIX: keep_default_na=False prevents "N/A" strings from becoming NaN floats
        df = pd.read_csv('internships.csv', keep_default_na=False)
        # Double safety: Convert all text columns to strings and fill empty spots
        text_cols = ['title', 'company', 'location', 'description', 'job_type']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', 'Unknown')
        return df
    return pd.DataFrame()

@st.cache_data
def load_usage_logs():
    if os.path.exists('usage_log.json'):
        try:
            with open('usage_log.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def calculate_time_savings(logs):
    search_count = sum(1 for log in logs if log.get('action') == 'search_complete')
    manual_time_per_session = 37.5
    automated_time_per_session = 5
    time_saved_per_session = manual_time_per_session - automated_time_per_session
    total_time_saved = search_count * time_saved_per_session
    
    return {
        'sessions': search_count,
        'time_saved_minutes': total_time_saved,
        'time_saved_hours': total_time_saved / 60,
        'manual_time': search_count * manual_time_per_session,
        'automated_time': search_count * automated_time_per_session,
        'efficiency_percent': ((manual_time_per_session - automated_time_per_session) / manual_time_per_session) * 100
    }

tab1, tab2, tab3 = st.tabs(["🔍 Search Jobs", "💼 Job Listings", "📊 Analytics"])

with tab1:
    st.header("🔍 Search & Scrape Internships")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv('WRIGHT_STATE_EMAIL')
    username = os.getenv('WRIGHT_STATE_USERNAME')
    password = os.getenv('WRIGHT_STATE_PASSWORD')
    
    credentials_configured = all([
        email and email != "yourname@wright.edu",
        username and username != "your_campus_username",
        password and password != "your_password"
    ])
    
    if not credentials_configured:
        st.warning("⚠️ Credentials not configured!")
        st.info("""
        **Setup Required:**
        1. Create a `.env` file in the project directory
        2. Add your credentials:
        ```
        WRIGHT_STATE_EMAIL=yourname@wright.edu
        WRIGHT_STATE_USERNAME=your_campus_username
        WRIGHT_STATE_PASSWORD=your_password
        ```
        3. Refresh this page
        """)
        
        st.markdown("---")
        st.subheader("Or enter credentials manually:")
        
        col1, col2 = st.columns(2)
        with col1:
            manual_email = st.text_input("Wright State Email", key="manual_email")
            manual_username = st.text_input("Campus Username", key="manual_username")
        with col2:
            manual_password = st.text_input("Password", type="password", key="manual_password")
        
        if manual_email and manual_username and manual_password:
            credentials_configured = True
            email = manual_email
            username = manual_username
            password = manual_password
    
    if credentials_configured:
        st.success("✅ Credentials configured!")
        
        st.markdown("### 🎯 Search Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            major = st.text_input(
                "Major / Keywords",
                value="",
                help="Leave blank for ALL jobs, or enter: Computer Science, Software, etc."
            )
        
        with col2:
            location = st.text_input(
                "Location",
                value="",
                help="Leave blank for ALL locations, or enter: Remote, Ohio, etc."
            )
        
        with col3:
            max_pages = st.number_input(
                "Pages to Scrape",
                min_value=1,
                max_value=5,
                value=1,
                help="Start with 1 page for testing"
            )
        
        max_jobs = st.slider(
            "Maximum Jobs to Scrape in Detail",
            min_value=5,
            max_value=50,
            value=10,
            help="How many jobs to scrape full details for"
        )
        
        st.info("💡 **Tip:** Start with blank search (ALL jobs) to test if scraping works!")
        
        if st.button("🚀 Start Scraping", type="primary", disabled=st.session_state.scraping):
            st.session_state.scraping = True
            st.session_state.scrape_results = None
            st.rerun()
        
        if st.session_state.scraping:
            st.markdown("---")
            st.info("🤖 Scraping in progress... This may take a few minutes.")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.expander("📋 View Detailed Logs", expanded=True)
            
            try:
                from internship_tracker import InternshipTracker
                
                status_text.text("⚙️ Initializing tracker...")
                with log_container:
                    st.text("Initializing InternshipTracker...")
                progress_bar.progress(10)
                
                tracker = InternshipTracker(
                    email=email,
                    username=username,
                    password=password,
                    headless=False
                )
                
                status_text.text("🔐 Logging in to Handshake...")
                with log_container:
                    st.text("Starting login process...")
                    st.text("This may take 30-60 seconds...")
                progress_bar.progress(20)
                
                if not tracker.login():
                    st.error("❌ Login failed! Please check your credentials.")
                    with log_container:
                        st.error("Login failed - verify credentials")
                    st.session_state.scraping = False
                    st.stop()
                
                status_text.text("✅ Login successful!")
                with log_container:
                    st.success("✓ Login successful!")
                    st.text(f"Current URL: {tracker.driver.current_url}")
                progress_bar.progress(30)
                
                search_text = "ALL jobs" if not major and not location else f"'{major}' in '{location}'"
                status_text.text(f"🔍 Searching for {search_text}...")
                with log_container:
                    st.text(f"Searching: {major if major else 'ALL'} / {location if location else 'ALL'}")
                    st.text(f"Max pages: {max_pages}")
                    st.text("This will take 1-2 minutes...")
                progress_bar.progress(40)
                
                job_urls = tracker.search_jobs(major, location, max_pages)
                
                with log_container:
                    st.text(f"\n{'='*50}")
                    st.text(f"Search complete! Found {len(job_urls)} job URLs")
                    st.text(f"{'='*50}")
                    
                    if len(job_urls) > 0:
                        st.success(f"✅ Found {len(job_urls)} jobs!")
                        st.text("\nSample URLs:")
                        for i, url in enumerate(job_urls[:5], 1):
                            st.text(f"  {i}. {url}")
                        if len(job_urls) > 5:
                            st.text(f"  ... and {len(job_urls) - 5} more")
                    else:
                        st.error("❌ No jobs found!")
                        st.text("\nPossible reasons:")
                        st.text("1. No internships currently posted")
                        st.text("2. Page structure may have changed")
                        st.text("3. Access restrictions on your account")
                        st.text("\nCheck these files:")
                        st.text("- debug_initial_page.png")
                        st.text("- debug_page_source.html")
                        st.text("- internship_tracker.log")
                
                if not job_urls:
                    st.warning("⚠️ No jobs found.")
                    
                    st.info("""
                    **Troubleshooting Steps:**
                    1. Check if you can manually see jobs in Handshake
                    2. Look at debug_initial_page.png - what do you see?
                    3. Open debug_page_source.html - are there job listings?
                    4. Check internship_tracker.log for detailed errors
                    5. Try searching for "ALL" jobs (leave fields blank)
                    """)
                    
                    try:
                        page_text = tracker.driver.find_element(By.TAG_NAME, "body").text
                        with log_container:
                            st.text("\n📄 Page content preview:")
                            st.text(page_text[:300])
                    except:
                        pass
                    
                    tracker.close()
                    st.session_state.scraping = False
                    st.stop()
                
                status_text.text(f"✅ Found {len(job_urls)} jobs!")
                progress_bar.progress(50)
                
                jobs_to_scrape = min(len(job_urls), max_jobs)
                status_text.text(f"📋 Scraping {jobs_to_scrape} job details...")
                
                with log_container:
                    st.text(f"\n{'='*50}")
                    st.text(f"Starting detailed scraping of {jobs_to_scrape} jobs...")
                    st.text(f"{'='*50}\n")
                
                jobs = []
                for i, url in enumerate(job_urls[:jobs_to_scrape], 1):
                    progress = 50 + int((i / jobs_to_scrape) * 40)
                    progress_bar.progress(progress)
                    status_text.text(f"📋 Scraping job {i}/{jobs_to_scrape}...")
                    
                    with log_container:
                        st.text(f"[{i}/{jobs_to_scrape}] Scraping: {url}")
                    
                    job = tracker.scrape_job_details(url)
                    jobs.append(job)
                    
                    with log_container:
                        if 'error' not in job:
                            st.text(f"  ✓ {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                        else:
                            st.text(f"  ✗ Error: {job.get('error', 'Unknown')}")
                
                progress_bar.progress(90)
                status_text.text("💾 Saving results...")
                
                tracker.save_to_file(jobs, format="csv")
                
                with log_container:
                    st.text("\n✓ Saved to internships.csv")
                
                tracker.close()
                
                progress_bar.progress(100)
                status_text.text("✅ Scraping complete!")
                
                st.success(f"🎉 Successfully scraped {len(jobs)} jobs!")
                
                df_results = pd.DataFrame(jobs)
                st.dataframe(df_results[['title', 'company', 'location']], use_container_width=True)
                
                # Clear caches properly
                load_internships.clear()
                load_usage_logs.clear()
                
                st.session_state.scraping = False
                st.session_state.scrape_results = jobs
                
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error during scraping: {str(e)}")
                import traceback
                error_details = traceback.format_exc()
                
                with log_container:
                    st.error("\nFull error traceback:")
                    st.code(error_details)
                
                st.info("""
                **Error occurred. Check:**
                1. internship_tracker.log file
                2. debug_initial_page.png screenshot
                3. debug_page_source.html file
                """)
                
                st.session_state.scraping = False
        
        if st.session_state.scrape_results and not st.session_state.scraping:
            st.markdown("---")
            st.success(f"✅ Last scrape: {len(st.session_state.scrape_results)} jobs found")
            
            if st.button("🔄 Clear Results"):
                st.session_state.scrape_results = None
                st.rerun()

with tab2:
    st.header("💼 Job Listings")
    
    df_jobs = load_internships()
    
    if not df_jobs.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # FIX: Convert to string before sorting to prevent TypeError (Str < NaN)
            companies_list = df_jobs['company'].dropna().astype(str).unique().tolist()
            companies = ['All'] + sorted(companies_list)
            selected_company = st.selectbox("Filter by Company", companies)
        
        with col2:
            # FIX: Convert to string before sorting
            locations_list = df_jobs['location'].dropna().astype(str).unique().tolist()
            locations = ['All'] + sorted(locations_list)
            selected_location = st.selectbox("Filter by Location", locations)
        
        with col3:
            search_term = st.text_input("Search in titles", "")
        
        filtered_df = df_jobs.copy()
        if selected_company != 'All':
            filtered_df = filtered_df[filtered_df['company'].astype(str) == selected_company]
        if selected_location != 'All':
            filtered_df = filtered_df[filtered_df['location'].astype(str) == selected_location]
        if search_term:
            filtered_df = filtered_df[filtered_df['title'].astype(str).str.contains(search_term, case=False, na=False)]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", len(df_jobs))
        with col2:
            st.metric("Filtered Jobs", len(filtered_df))
        with col3:
            st.metric("Companies", df_jobs['company'].nunique())
        with col4:
            st.metric("Locations", df_jobs['location'].nunique())
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            top_companies = filtered_df['company'].value_counts().head(10).reset_index()
            top_companies.columns = ['company', 'count']
            fig_companies = px.bar(
                top_companies,
                x='count',
                y='company',
                orientation='h',
                title='Top 10 Companies'
            )
            st.plotly_chart(fig_companies, use_container_width=True)
        
        with col2:
            location_counts = filtered_df['location'].value_counts().head(10).reset_index()
            location_counts.columns = ['location', 'count']
            fig_locations = px.bar(
                location_counts,
                x='count',
                y='location',
                orientation='h',
                title='Top 10 Locations'
            )
            st.plotly_chart(fig_locations, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 Job Details")
        
        for idx, row in filtered_df.iterrows():
            with st.expander(f"**{row['title']}** at {row['company']} - {row['location']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Company:** {row['company']}")
                    st.markdown(f"**Location:** {row['location']}")
                    st.markdown(f"**Type:** {row.get('job_type', 'Internship')}")
                    
                    desc = str(row.get('description', 'N/A'))
                    if desc != 'nan' and desc != 'N/A':
                        st.markdown(f"**Description:** {desc[:200]}...")
                    
                    st.markdown(f"**Scraped:** {row['date_scraped']}")
                
                with col2:
                    st.link_button("🔗 View Job", row['url'])
        
        st.markdown("---")
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Jobs (CSV)",
            data=csv,
            file_name=f"filtered_internships_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("📭 No jobs scraped yet!")
        st.markdown("""
        ### Get Started:
        1. Go to the **🔍 Search Jobs** tab
        2. Enter your search criteria (or leave blank for ALL)
        3. Click **Start Scraping**
        4. Jobs will appear here automatically!
        """)

with tab3:
    st.header("📊 Usage Analytics & Time Savings")
    
    logs = load_usage_logs()
    
    if logs:
        time_savings = calculate_time_savings(logs)
        df_jobs = load_internships()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Jobs", len(df_jobs) if not df_jobs.empty else 0)
        
        with col2:
            st.metric("🔍 Sessions", time_savings['sessions'])
        
        with col3:
            st.metric(
                "⏱️ Time Saved",
                f"{time_savings['time_saved_hours']:.1f} hrs",
                delta=f"{time_savings['efficiency_percent']:.0f}% efficient"
            )
        
        with col4:
            st.metric("📈 Actions", len(logs))
        
        st.markdown("---")
        st.subheader("⏱️ Time Savings Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            time_data = pd.DataFrame({
                'Process': ['Manual', 'Automated', 'Time Saved'],
                'Minutes': [
                    time_savings['manual_time'],
                    time_savings['automated_time'],
                    time_savings['time_saved_minutes']
                ]
            })
            
            fig_time = px.bar(
                time_data,
                x='Process',
                y='Minutes',
                title='Time Comparison',
                color='Process',
                color_discrete_map={
                    'Manual': '#ff6b6b',
                    'Automated': '#51cf66',
                    'Time Saved': '#339af0'
                }
            )
            st.plotly_chart(fig_time, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Efficiency Metrics")
            st.write(f"**Total Sessions:** {time_savings['sessions']}")
            st.write(f"**Manual Time/Session:** 37.5 min")
            st.write(f"**Automated Time/Session:** 5 min")
            st.write(f"**Saved/Session:** 32.5 min")
            st.write(f"**Total Time Saved:** {time_savings['time_saved_hours']:.1f} hrs")
            st.write(f"**Efficiency:** {time_savings['efficiency_percent']:.0f}%")
            st.progress(max(0, min(1.0, time_savings['efficiency_percent'] / 100)))
        
        st.markdown("---")
        st.subheader("📈 Usage Statistics")
        
        df_logs = pd.DataFrame(logs)
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
        df_logs['date'] = df_logs['timestamp'].dt.date
        
        col1, col2 = st.columns(2)
        
        with col1:
            daily_actions = df_logs.groupby('date').size().reset_index(name='count')
            fig_usage = px.line(daily_actions, x='date', y='count', title='Daily Usage', markers=True)
            st.plotly_chart(fig_usage, use_container_width=True)
        
        with col2:
            action_counts = df_logs['action'].value_counts().reset_index()
            action_counts.columns = ['action', 'count']
            fig_actions = px.pie(action_counts, values='count', names='action', title='Actions')
            st.plotly_chart(fig_actions, use_container_width=True)
        
        st.subheader("🕐 Recent Activity")
        recent_logs = df_logs.tail(20)[['timestamp', 'action', 'details']].sort_values('timestamp', ascending=False)
        st.dataframe(recent_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No usage data yet. Start scraping to generate statistics!")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Internship Tracker Dashboard v2.1 | Fixed & Robust</p>
    <p>💡 Saving time, one search at a time!</p>
</div>
""", unsafe_allow_html=True)