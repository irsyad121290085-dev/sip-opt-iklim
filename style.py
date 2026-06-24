import streamlit as st

def apply_global_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #f3fff4 0%, #eef7ff 45%, #fff8ec 100%);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f3d2e 0%, #14532d 100%);
        }

        section[data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            padding: 18px;
            border-radius: 18px;
            border-left: 6px solid #22c55e;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #14532d;
        }

        .hero-box {
            background: linear-gradient(135deg, #14532d 0%, #0f766e 55%, #2563eb 100%);
            padding: 28px;
            border-radius: 24px;
            color: white;
            margin-bottom: 24px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
        }

        .hero-box h1 {
            color: white;
            margin-bottom: 8px;
        }

        .hero-box p {
            color: #ecfeff;
            font-size: 17px;
        }

        .card-box {
            background: white;
            padding: 20px;
            border-radius: 18px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            margin-bottom: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def hero(title, subtitle=""):
    st.markdown(
        f"""
        <div class="hero-box">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )