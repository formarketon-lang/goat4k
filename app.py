import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

# --- পেজ কনফিগারেশন ---
st.set_page_config(
    page_title="TradeLab Pro · Cash Market Scanner & Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- কাস্টম সিএসএস (ডার্ক থিম ও মোবাইল রেসপনসিভনেস) ---
st.markdown("""
<style>
    .main { background-color: #0b1120; color: #e2e8f0; }
    .stMetric { background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; }
    div[data-testid="stExpander"] { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
    .badge-buy { background-color: #064e3b; color: #34d399; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
    .badge-sell { background-color: #4c0519; color: #fb7185; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
    .badge-watch { background-color: #78350f; color: #fbbf24; padding: 3px 8px; border-radius: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- সেশন স্টেট ইনিশিয়ালাইজেশন ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'stock_dfs' not in st.session_state:
    st.session_state.stock_dfs = {}
if 'preset' not in st.session_state:
    st.session_state.preset = "Trend Follower"

# --- ইউনিভার্স ও সেক্টর ডেটাবেস ---
SECTORS = {
    'Banking': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'BANKBARODA.NS', 'PNB.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS'],
    'Financial Services': ['BAJFINANCE.NS', 'BAJAJFINSV.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'CHOLAFIN.NS', 'SHRIRAMFIN.NS', 'MUTHOOTFIN.NS', 'PFC.NS', 'RECLTD.NS'],
    'IT': ['TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS', 'LTIM.NS', 'PERSISTENT.NS', 'COFORGE.NS', 'MPHASIS.NS'],
    'FMCG': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'DABUR.NS', 'MARICO.NS', 'GODREJCP.NS', 'COLPAL.NS', 'TATACONSUM.NS'],
    'Automobile': ['MARUTI.NS', 'TATAMOTORS.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS', 'BALKRISIND.NS', 'BOSCHLTD.NS'],
    'Healthcare': ['SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS', 'LUPIN.NS', 'TORNTPHARM.NS', 'AUROPHARMA.NS'],
    'Energy': ['RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS', 'GAIL.NS', 'COALINDIA.NS', 'OIL.NS', 'PETRONET.NS', 'HINDPETRO.NS'],
    'Metals': ['TATASTEEL.NS', 'JSWSTEEL.NS', 'HINDALCO.NS', 'VEDL.NS', 'SAIL.NS', 'NMDC.NS', 'JINDALSTEL.NS', 'NATIONALUM.NS'],
    'Capital Goods': ['LT.NS', 'SIEMENS.NS', 'ABB.NS', 'BHEL.NS', 'HAL.NS', 'BEL.NS', 'HAVELLS.NS', 'POLYCAB.NS'],
    'Chemicals': ['PIDILITIND.NS', 'SRF.NS', 'UPL.NS', 'AARTIIND.NS', 'DEEPAKNTR.NS', 'NAVINFLUOR.NS', 'TATACHEM.NS'],
    'Realty': ['DLF.NS', 'GODREJPROP.NS', 'OBEROIRLTY.NS', 'PRESTIGE.NS', 'PHOENIXLTD.NS', 'BRIGADE.NS', 'LODHA.NS'],
    'Telecom': ['BHARTIARTL.NS', 'IDEA.NS', 'INDUSTOWER.NS', 'TATACOMM.NS', 'HFCL.NS', 'TEJASNET.NS'],
    'Consumer Durables': ['TITAN.NS', 'VOLTAS.NS', 'BLUESTARCO.NS', 'CROMPTON.NS', 'DIXON.NS', 'BATAINDIA.NS', 'KALYANKJIL.NS'],
    'Infrastructure': ['ADANIPORTS.NS', 'IRB.NS', 'GMRINFRA.NS', 'IRCON.NS', 'RVNL.NS', 'NBCC.NS'],
    'Utilities': ['NTPC.NS', 'POWERGRID.NS', 'TATAPOWER.NS', 'ADANIPOWER.NS', 'NHPC.NS', 'SJVN.NS', 'JSWENERGY.NS']
}

INDEX_BUCKETS = {
    'All': [sym for sublist in SECTORS.values() for sym in sublist],
    'Nifty 50': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LT.NS', 'BAJFINANCE.NS', 'MARUTI.NS', 'TATAMOTORS.NS', 'SUNPHARMA.NS', 'TITAN.NS'],
    'Nifty Next 50': ['HAL.NS', 'BEL.NS', 'CHOLAFIN.NS', 'DIVISLAB.NS', 'DLF.NS', 'PIDILITIND.NS', 'SIEMENS.NS', 'SRF.NS', 'VEDL.NS', 'TVSMOTOR.NS'],
    'Nifty Midcap 150': ['PERSISTENT.NS', 'COFORGE.NS', 'AARTIIND.NS', 'AUROPHARMA.NS', 'POLYCAB.NS', 'VOLTAS.NS', 'ASHOKLEY.NS', 'FEDERALBNK.NS'],
    'Nifty Smallcap 250': ['HFCL.NS', 'NBCC.NS', 'IRCON.NS', 'BATAINDIA.NS', 'TEJASNET.NS', 'SJVN.NS', 'IDFCFIRSTB.NS'],
    'Nifty Bank': SECTORS['Banking'],
    'Nifty IT': SECTORS['IT'],
    'Nifty FMCG': SECTORS['FMCG'],
    'Nifty Auto': SECTORS['Automobile'],
    'Nifty Metal': SECTORS['Metals'],
    'Nifty Energy': SECTORS['Energy'],
    'Nifty Realty': SECTORS['Realty'],
    'Sensex (BSE 30)': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'ITC.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'MARUTI.NS']
}

# --- টেকনিক্যাল ইন্ডিকেটর ফাংশনসমূহ ---
def calc_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

def calc_macd(series, fast=12, slow=26, signal=9):
    fast_ema = calc_ema(series, fast)
    slow_ema = calc_ema(series, slow)
    macd_line = fast_ema - slow_ema
    sig_line = calc_ema(macd_line, signal)
    hist = macd_line - sig_line
    return macd_line, sig_line, hist

def calc_atr(df, period=14):
    h, l, c = df['High'], df['Low'], df['Close']
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def calc_supertrend(df, period=10, mult=3):
    hl2 = (df['High'] + df['Low']) / 2
    atr = calc_atr(df, period)
    upper = hl2 + (mult * atr)
    lower = hl2 - (mult * atr)
    
    st_line = [np.nan] * len(df)
    st_dir = [1] * len(df)
    
    for i in range(1, len(df)):
        c = df['Close'].iloc[i]
        prev_upper = upper.iloc[i-1] if not np.isnan(upper.iloc[i-1]) else upper.iloc[i]
        prev_lower = lower.iloc[i-1] if not np.isnan(lower.iloc[i-1]) else lower.iloc[i]
        prev_st = st_line[i-1] if not np.isnan(st_line[i-1]) else lower.iloc[i]
        prev_dir = st_dir[i-1]
        
        curr_upper = upper.iloc[i] if upper.iloc[i] < prev_upper or df['Close'].iloc[i-1] > prev_upper else prev_upper
        curr_lower = lower.iloc[i] if lower.iloc[i] > prev_lower or df['Close'].iloc[i-1] < prev_lower else prev_lower
        
        if prev_dir == 1:
            curr_dir = -1 if c < curr_lower else 1
        else:
            curr_dir = 1 if c > curr_upper else -1
            
        st_dir[i] = curr_dir
        st_line[i] = curr_lower if curr_dir == 1 else curr_upper
        
    return pd.Series(st_line, index=df.index), pd.Series(st_dir, index=df.index)

def calc_adx(df, period=14):
    h, l, c = df['High'], df['Low'], df['Close']
    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean()
    
    pdi = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan))
    mdi = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan))
    dx = 100 * ((pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan))
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx.fillna(0), pdi.fillna(0), mdi.fillna(0)

def calc_vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    pv = tp * df['Volume']
    return pv.cumsum() / df['Volume'].cumsum().replace(0, np.nan)

def calc_bollinger(series, period=20, mult=2):
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    up = mid + (mult * std)
    lo = mid - (mult * std)
    bw = (up - lo) / mid.replace(0, np.nan)
    return mid, up, lo, bw

# --- হেডার ও ড্যাশবোর্ড টাইটেল ---
st.title("⚡ TradeLab Pro · Cash Market Scanner & Risk Engine")
st.caption("NSE/BSE ক্যাশ ইকুইটি স্ক্রিনার, রিস্ক ও পজিশন সাইজিং ক্যালকুলেটর এবং ব্যাকটেস্ট ড্যাশবোর্ড।")

# --- মূল ৫টি ধাপ (TABS) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1️⃣ Universe", 
    "2️⃣ Rules", 
    "3️⃣ Risk & Sizing", 
    "4️⃣ Scan & Score", 
    "5️⃣ Results & Backtest"
])

# ==========================================================
# 1. UNIVERSE TAB
# ==========================================================
with tab1:
    st.subheader("Step 1 · Universe Selection & Base Filters")
    col1, col2, col3 = st.columns(3)

# --- ১. Universe & Index Selection ---
col_idx1, col_idx2 = st.columns(2)
with col_idx1:
    sel_exch = st.selectbox("Exchange", ["All", "NSE", "BSE"], index=1)
with col_idx2:
    sel_idx = st.selectbox("Index Bucket", ["All (All Stocks)"] + list(INDEX_BUCKETS.keys()), index=0)

# --- ২. Timeframe & Lookback ---
col_tf1, col_tf2 = st.columns(2)
with col_tf1:
    sel_tf = st.selectbox("Timeframe", ["Daily", "5m", "15m", "60m", "Weekly", "Monthly"], index=0)
with col_tf2:
    sel_period = st.selectbox("Data Lookback Period", ["1 Year", "6 Months", "3 Months", "2 Years", "All"], index=0)

# --- ৩. Market Cap (Bucket + Custom Values) ---
col_mc1, col_mc2, col_mc3 = st.columns(3)
with col_mc1:
    market_cap_bucket = st.selectbox("Market Cap Category", ["All", "Large Cap", "Mid Cap", "Small Cap", "Micro Cap", "Custom/None"], index=0)
with col_mc2:
    min_mcap = st.number_input("Min Market Cap (₹ Cr)", min_value=0.0, value=0.0, step=1000.0, help="0 রাখলে অফ থাকবে")
with col_mc3:
    max_mcap = st.number_input("Max Market Cap (₹ Cr)", min_value=0.0, value=500000.0, step=5000.0, help="উচ্চ সীমা নির্ধারণের জন্য")

# --- ৪. Sector Selection Controls (Select All / None) ---
col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    select_all_sec = st.checkbox("Select All / Deselect All", value=True)
# নিচে সব সেক্টরের চেকবক্স এই টগলের সাথে সমন্বিত থাকবে
          st.markdown("---")
    sec_cols = st.columns(5)
    selected_sectors = []
    for idx, sec in enumerate(SECTORS.keys()):
        with sec_cols[idx % 5]:
            if st.checkbox(sec, value=select_all_sec):
                selected_sectors.append(sec)
                
    circuit_candles = st.number_input(
        "Circuit-lock Check (Last X Candles)", 
        min_value=0, 
        max_value=20, 
        value=0, 
        step=1,
        help="0 রাখলে সার্কিট চেক নিষ্ক্রিয় থাকবে।"
    )

with col2:
    # সর্বোচ্চ দামের সীমা ডিফল্ট হিসেবে অনেক বেশি রাখা হলো
    max_price = st.number_input(
        "Maximum Price (₹)", 
        min_value=0.0, 
        value=100000.0, 
        step=100.0,
        help="ডিফল্ট মান সর্বোচ্চ রাখা হয়েছে যাতে সব দামের স্টক আসে।"
    )
    
    # টার্নওভার ফিল্টার ডিফল্ট 0.0 (বন্ধ)
    min_turnover = st.number_input(
        "Min 20-Day Avg Turnover (₹ Crore)", 
        min_value=0.0, 
        value=0.0, 
        step=1.0,
        help="0 মানে কোনো টার্নওভার ফিল্টার প্রয়োগ হবে না।"
    )
    
    # ASM/GSM এক্সক্লুশন ডিফল্ট False
    exclude_asm_gsm = st.checkbox(
        "Exclude ASM / GSM Surveillance Stocks", 
        value=False,
        help="টিক দিলে সেবির ASM/GSM তালিকার স্টক বাদ যাবে।"
    )
# ==========================================================
# 2. RULES TAB
# ==========================================================
with tab2:
    st.subheader("Step 2 · Technical Rules & Preset Engine")
    
    pcol1, pcol2, pcol3 = st.columns([2, 1, 1])
    with pcol1:
        preset_choice = st.radio("Strategy Presets", ["Trend Follower", "Breakout", "Pullback", "Reversal", "Custom"], horizontal=True)
    with pcol2:
        rule_logic = st.selectbox("Rule Logic", ["AND (All enabled)", "OR (Any enabled)", "Min-N-of-M"], index=2)
    with pcol3:
        min_n = st.number_input("N (for Min-N-of-M)", value=3, min_value=1, max_value=10)
        trade_dir = st.selectbox("Direction", ["BOTH (Buy & Sell)", "BUY Only", "SELL Only"])

    st.markdown("---")
    rcol1, rcol2 = st.columns(2)
    
    # প্রিসেট অনুযায়ী ডিফল্ট ভ্যালু নির্ধারণ
    def_ema = preset_choice in ["Trend Follower", "Custom"]
    def_e200 = preset_choice in ["Trend Follower", "Pullback", "Custom"]
    def_rsi = preset_choice in ["Pullback", "Reversal", "Custom"]
    def_macd = preset_choice in ["Trend Follower", "Reversal", "Custom"]
    def_st = preset_choice in ["Trend Follower", "Pullback", "Custom"]
    def_vol = preset_choice in ["Breakout", "Reversal", "Custom"]
    def_brk = preset_choice in ["Breakout", "Custom"]
    def_sq = preset_choice in ["Breakout", "Custom"]
    def_adx = preset_choice in ["Trend Follower", "Breakout", "Custom"]

    with rcol1:
        with st.expander("EMA Crossover & 200 EMA", expanded=True):
            r_ema = st.checkbox("Enable EMA Crossover", value=def_ema)
            ema_fast = st.number_input("Fast EMA Period", value=9, min_value=2)
            ema_slow = st.number_input("Slow EMA Period", value=21, min_value=3)
            r_e200 = st.checkbox("Close vs EMA 200 (Bullish > EMA200)", value=def_e200)

        with st.expander("RSI & MACD Indicators", expanded=True):
            r_rsi = st.checkbox("Enable RSI Zone", value=def_rsi)
            rsi_lo = st.slider("RSI Lower Bound (Bullish)", 0, 100, 50 if preset_choice != "Pullback" else 35)
            rsi_hi = st.slider("RSI Upper Bound (Bullish)", 0, 100, 70 if preset_choice != "Pullback" else 55)
            r_macd = st.checkbox("Enable MACD Crossover", value=def_macd)

        with st.expander("Supertrend & VWAP", expanded=True):
            r_st = st.checkbox("Enable Supertrend (10, 3)", value=def_st)
            r_vwap = st.checkbox("Session VWAP (Intraday)", value=False)

    with rcol2:
        with st.expander("ADX Trend Strength & Volume Spike", expanded=True):
            r_adx = st.checkbox("Enable ADX Threshold", value=def_adx)
            adx_th = st.slider("Min ADX Value", 10, 50, 20)
            adx_di = st.checkbox("Require +DI / -DI Direction Alignment", value=True)
            r_vol = st.checkbox("Volume Spike (> 20-bar avg)", value=def_vol)
            vol_mult = st.slider("Volume Multiplier (x)", 1.0, 5.0, 1.5, step=0.1)

        with st.expander("Breakout & Bollinger Squeeze", expanded=True):
            r_brk = st.checkbox("Price Breakout (N-bar High/Low)", value=def_brk)
            brk_per = st.selectbox("Breakout Lookback Bars", [20, 52], index=0)
            r_sq = st.checkbox("Bollinger Band Squeeze", value=def_sq)
            sq_pct = st.slider("Bandwidth Percentile Squeeze (≤ %)", 5, 50, 20)

# ==========================================================
# 3. RISK & SIZING TAB
# ==========================================================
with tab3:
    st.subheader("Step 3 · Capital, Risk Management & Sizing")
    rk_col1, rk_col2, rk_col3 = st.columns(3)
    with rk_col1:
        capital = st.number_input("Account Capital (₹)", value=25000, step=1000)
        risk_pct = st.number_input("Risk Per Trade (%)", value=1.0, min_value=0.1, max_value=10.0, step=0.1)
        max_exp = st.number_input("Max Exposure (% of Capital)", value=100, min_value=10, max_value=100)
    with rk_col2:
        atr_stop_m = st.number_input("ATR Stop Multiplier", value=2.0, min_value=0.5, step=0.5)
        atr_tgt_m = st.number_input("ATR Target Multiplier", value=4.0, min_value=1.0, step=0.5)
        min_rr = st.number_input("Minimum Net R:R Required", value=1.5, min_value=0.5, step=0.1)
    with rk_col3:
        round_trip_cost = st.number_input("Est. Round-Trip Cost (%)", value=0.15, step=0.01)
        min_score = st.slider("Minimum Quality Score (0-100)", 0, 100, 50)
        rs_lookback = st.number_input("Relative Strength Lookback (Bars)", value=20, min_value=5)

# ==========================================================
# 4. SCAN & SCORE TAB
# ==========================================================
with tab4:
    st.subheader("Step 4 · Data Source & Multi-Factor Weights")
    dsc1, dsc2 = st.columns(2)
    with dsc1:
        data_mode = st.radio("Data Fetch Mode", ["Live yFinance API", "Upload Local CSV Files", "Deterministic Demo (Offline)"], horizontal=True)
        bench_sym = st.text_input("Benchmark Symbol (for Relative Strength)", value="^NSEI")
    with dsc2:
        st.markdown("**Score Weights (Total: 100% normalized):**")
        w_trend = st.slider("Trend Weight", 0, 100, 30)
        w_mom = st.slider("Momentum Weight", 0, 100, 25)
        w_vol = st.slider("Volume Weight", 0, 100, 20)
        w_rs = st.slider("Relative Strength Weight", 0, 100, 15)
        w_volat = st.slider("Volatility Weight", 0, 100, 10)

    # আপলোড হ্যান্ডলার
    uploaded_files = []
    if data_mode == "Upload Local CSV Files":
        uploaded_files = st.file_uploader("Upload CSV Candles (Date/Time, Open, High, Low, Close, Volume)", accept_multiple_files=True)

# ==========================================================
# ডেটা প্রসেসিং, স্ক্রিনিং ও রিস্ক ক্যালকুলেশন ইঞ্জিন
# ==========================================================
def run_scanner():
    target_symbols = []
    if sel_idx in INDEX_BUCKETS:
        target_symbols = INDEX_BUCKETS[sel_idx]
    
    # সেক্টর ফিল্টার প্রয়োগ
    valid_symbols = []
    for sym in target_symbols:
        for sec, syms in SECTORS.items():
            if sym in syms and sec in selected_sectors:
                valid_symbols.append(sym)
                break
    valid_symbols = list(set(valid_symbols))
    
    if not valid_symbols and data_mode != "Upload Local CSV Files":
        st.warning("বাছাইকৃত ফিল্টারে কোনো স্টক পাওয়া যায়নি। অনুগ্রহ করে সেক্টর বা ইন্ডেক্স পরিবর্তন করুন।")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_results = []
    dfs_dict = {}

    # বেঞ্চমার্ক ডেটা ফেচ
    bench_df = None
    if data_mode == "Live yFinance API":
        try:
            bench_df = yf.download(bench_sym, period="1y", interval="1d", progress=False)
            if isinstance(bench_df.columns, pd.MultiIndex):
                bench_df.columns = bench_df.columns.get_level_values(0)
        except Exception:
            pass

    total = len(valid_symbols) if data_mode != "Upload Local CSV Files" else len(uploaded_files)
    
    for i, item in enumerate(valid_symbols if data_mode != "Upload Local CSV Files" else uploaded_files):
        sym_name = item if data_mode != "Upload Local CSV Files" else item.name.split('.')[0]
        status_text.text(f"Scanning ({i+1}/{total}): {sym_name}...")
        progress_bar.progress((i + 1) / total)

        df = None
        if data_mode == "Live yFinance API":
            try:
                tf_map = {"Daily": "1d", "5m": "5m", "15m": "15m", "60m": "1h", "Weekly": "1wk", "Monthly": "1mo"}
                df = yf.download(item, period="1y", interval=tf_map.get(sel_tf, "1d"), progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
            except Exception:
                continue
        elif data_mode == "Upload Local CSV Files":
            try:
                df = pd.read_csv(item)
                df.columns = [c.capitalize() for c in df.columns]
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
            except Exception:
                continue
        else: # Deterministic Demo
            dates = pd.date_range(end=datetime.today(), periods=250, freq='B')
            np.random.seed(abs(hash(item)) % 100000)
            p = 100.0 + np.cumsum(np.random.randn(250) * 2)
            df = pd.DataFrame({
                'Open': p + np.random.randn(250),
                'High': p + abs(np.random.randn(250)) * 2,
                'Low': p - abs(np.random.randn(250)) * 2,
                'Close': p,
                'Volume': np.random.randint(50000, 500000, 250)
            }, index=dates)

        if df is None or len(df) < 30:
            continue

        close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        chg_pct = ((close - prev_close) / prev_close) * 100
        vol = df['Volume'].iloc[-1]
        avg_vol_20 = df['Volume'].tail(20).mean()

        # ইউনিভার্স বেস ফিল্টার
        if close < min_price or avg_vol_20 < min_vol:
            continue

        # টেকনিক্যাল ক্যালকুলেশন
        df['EMA_Fast'] = calc_ema(df['Close'], ema_fast)
        df['EMA_Slow'] = calc_ema(df['Close'], ema_slow)
        df['EMA_200'] = calc_ema(df['Close'], 200)
        df['RSI'] = calc_rsi(df['Close'], 14)
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = calc_macd(df['Close'])
        df['ATR'] = calc_atr(df, 14)
        df['ST_Line'], df['ST_Dir'] = calc_supertrend(df, 10, 3)
        df['ADX'], df['PDI'], df['MDI'] = calc_adx(df, 14)
        df['VWAP'] = calc_vwap(df)
        df['BB_Mid'], df['BB_Up'], df['BB_Lo'], df['BB_Width'] = calc_bollinger(df['Close'], 20, 2)

        dfs_dict[sym_name] = df

        # রুল মূল্যায়ন (Bullish / Bearish)
        rules_passed = 0
        total_enabled = 0
        rule_details = []

        # 1. EMA
        if r_ema:
            total_enabled += 1
            passed = df['EMA_Fast'].iloc[-1] > df['EMA_Slow'].iloc[-1]
            if passed: rules_passed += 1
            rule_details.append(f"EMA Cross: {'PASS' if passed else 'FAIL'}")

        # 2. EMA200
        if r_e200:
            total_enabled += 1
            passed = close > df['EMA_200'].iloc[-1]
            if passed: rules_passed += 1
            rule_details.append(f"EMA 200: {'PASS' if passed else 'FAIL'}")

        # 3. RSI
        if r_rsi:
            total_enabled += 1
            passed = rsi_lo <= df['RSI'].iloc[-1] <= rsi_hi
            if passed: rules_passed += 1
            rule_details.append(f"RSI Zone: {'PASS' if passed else 'FAIL'}")

        # 4. MACD
        if r_macd:
            total_enabled += 1
            passed = df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1]
            if passed: rules_passed += 1
            rule_details.append(f"MACD Cross: {'PASS' if passed else 'FAIL'}")

        # 5. Supertrend
        if r_st:
            total_enabled += 1
            passed = df['ST_Dir'].iloc[-1] == 1
            if passed: rules_passed += 1
            rule_details.append(f"Supertrend: {'PASS' if passed else 'FAIL'}")

        # 6. ADX
        if r_adx:
            total_enabled += 1
            passed = df['ADX'].iloc[-1] >= adx_th and (not adx_di or df['PDI'].iloc[-1] > df['MDI'].iloc[-1])
            if passed: rules_passed += 1
            rule_details.append(f"ADX: {'PASS' if passed else 'FAIL'}")

        # 7. Volume Spike
        if r_vol:
            total_enabled += 1
            passed = vol >= (vol_mult * avg_vol_20)
            if passed: rules_passed += 1
            rule_details.append(f"Vol Spike: {'PASS' if passed else 'FAIL'}")

        # 8. Breakout
        if r_brk:
            total_enabled += 1
            prior_high = df['High'].iloc[-brk_per-1:-1].max()
            passed = close > prior_high
            if passed: rules_passed += 1
            rule_details.append(f"Breakout {brk_per}: {'PASS' if passed else 'FAIL'}")

        # 9. Bollinger Squeeze
        if r_sq:
            total_enabled += 1
            recent_bw = df['BB_Width'].iloc[-100:]
            pct_rank = (recent_bw <= df['BB_Width'].iloc[-1]).mean() * 100
            passed = pct_rank <= sq_pct
            if passed: rules_passed += 1
            rule_details.append(f"BB Squeeze: {'PASS' if passed else 'FAIL'}")

        # লজিক কম্বিনেশন
        logic_pass = False
        if total_enabled == 0:
            logic_pass = True
        elif "AND" in rule_logic:
            logic_pass = (rules_passed == total_enabled)
        elif "OR" in rule_logic:
            logic_pass = (rules_passed > 0)
        else: # Min-N-of-M
            logic_pass = (rules_passed >= min(min_n, total_enabled))

        # রিস্ক ও পজিশন সাইজিং
        atr = df['ATR'].iloc[-1] if not np.isnan(df['ATR'].iloc[-1]) else close * 0.02
        stop_loss = max(close - (atr * atr_stop_m), 0.5)
        target = close + (atr * atr_tgt_m)
        risk_per_share = max(close - stop_loss, 0.01)
        risk_budget = capital * (risk_pct / 100)
        
        qty_risk = int(risk_budget // risk_per_share)
        qty_cap = int(capital // close)
        qty_exp = int((capital * (max_exp / 100)) // close)
        qty = max(0, min(qty_risk, qty_cap, qty_exp))
        
        gross_rr = (target - close) / (close - stop_loss)
        cost_val = close * (round_trip_cost / 100)
        net_rr = (target - close - cost_val) / (close - stop_loss + cost_val)

        # স্কোরিং সিস্টেম (0-100)
        s_trend = 100 if close > df['EMA_200'].iloc[-1] and df['EMA_Fast'].iloc[-1] > df['EMA_Slow'].iloc[-1] else 50
        s_mom = 100 if 50 <= df['RSI'].iloc[-1] <= 65 else 40
        s_vol = min(100, int((vol / avg_vol_20) * 50))
        
        # রিলেটিভ স্ট্রেন্থ
        s_rs = 50
        if bench_df is not None and len(bench_df) >= rs_lookback:
            stock_ret = (close / df['Close'].iloc[-rs_lookback]) - 1
            bench_ret = (bench_df['Close'].iloc[-1] / bench_df['Close'].iloc[-rs_lookback]) - 1
            rs_diff = stock_ret - bench_ret
            s_rs = int(np.clip((rs_diff + 0.05) / 0.10 * 100, 0, 100))

        s_volat = 70
        norm_w = w_trend + w_mom + w_vol + w_rs + w_volat
        final_score = (s_trend * w_trend + s_mom * w_mom + s_vol * w_vol + s_rs * w_rs + s_volat * w_volat) / norm_w

        # সিগন্যাল নির্ধারণ
        signal = "WATCH"
        if logic_pass and final_score >= min_score and net_rr >= min_rr and qty > 0:
            signal = "BUY"
        elif not logic_pass and rules_passed == 0:
            signal = "SELL"

        scan_results.append({
            'Symbol': sym_name,
            'Signal': signal,
            'Score': round(final_score, 1),
            'Price (₹)': round(close, 2),
            'Change %': round(chg_pct, 2),
            'Volume': int(vol),
            'Entry': round(close, 2),
            'Stop': round(stop_loss, 2),
            'Target': round(target, 2),
            'Qty': qty,
            'Net R:R': round(net_rr, 2),
            'Exposure (₹)': round(qty * close, 2),
            'Rules Passed': f"{rules_passed}/{total_enabled}"
        })

    status_text.text("স্ক্যান সফলভাবে সম্পন্ন হয়েছে!")
    st.session_state.results = scan_results
    st.session_state.stock_dfs = dfs_dict

# ==========================================================
# 5. RESULTS & BACKTEST TAB
# ==========================================================
with tab5:
    st.subheader("Step 5 · Scan Results, Interactive Chart & Backtest")
    
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("🚀 Run Live Scan Now", type="primary", use_container_width=True):
            run_scanner()
            
    if st.session_state.results:
        res_df = pd.DataFrame(st.session_state.results)
        
        # ফিল্টার ও সর্টিং টুলবার
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            sym_search = st.text_input("🔍 Search Symbol", "")
        with fcol2:
            sig_filter = st.selectbox("Signal Filter", ["ALL", "BUY", "SELL", "WATCH"])
        with fcol3:
            sort_metric = st.selectbox("Sort By", ["Score", "Change %", "Net R:R", "Price (₹)", "Volume"])

        filtered_df = res_df.copy()
        if sym_search:
            filtered_df = filtered_df[filtered_df['Symbol'].str.contains(sym_search.upper())]
        if sig_filter != "ALL":
            filtered_df = filtered_df[filtered_df['Signal'] == sig_filter]

        filtered_df = filtered_df.sort_values(by=sort_metric, ascending=False)
        st.dataframe(filtered_df, use_container_width=True)

        # CSV এক্সপোর্ট বাটন
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Results to CSV", csv_data, "tradelab_scan_results.csv", "text/csv")

        st.markdown("---")
        # বিস্তারিত স্টক বিশ্লেষণ এবং চার্ট ভিউ
        st.subheader("📊 Deep Dive Stock Analysis & Backtest Charts")
        sel_stock = st.selectbox("বিশ্লেষণের জন্য স্টক নির্বাচন করুন", filtered_df['Symbol'].tolist())

        if sel_stock in st.session_state.stock_dfs:
            sdf = st.session_state.stock_dfs[sel_stock]
            row_data = filtered_df[filtered_df['Symbol'] == sel_stock].iloc[0]

            # মেট্রিক্স কার্ডসমূহ
            mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
            mcol1.metric("Current Price", f"₹{row_data['Price (₹)']}", f"{row_data['Change %']}%")
            mcol2.metric("Target / Stop", f"₹{row_data['Target']} / ₹{row_data['Stop']}")
            mcol3.metric("Trade Quantity", f"{row_data['Qty']} Shares")
            mcol4.metric("Capital Exposure", f"₹{row_data['Exposure (₹)']}")
            mcol5.metric("Quality Score", f"{row_data['Score']}/100")

            # চার্ট ১: ক্যান্ডেলস্টিক এবং ট্রেড প্ল্যান লেভেল
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.7, 0.3])

            plot_candles = sdf.tail(100)
            fig.add_trace(go.Candlestick(
                x=plot_candles.index,
                open=plot_candles['Open'], high=plot_candles['High'],
                low=plot_candles['Low'], close=plot_candles['Close'],
                name="OHLC"
            ), row=1, col=1)

            # EMA এবং Supertrend লাইন
            fig.add_trace(go.Scatter(x=plot_candles.index, y=plot_candles['EMA_Fast'], line=dict(color='orange', width=1.2), name=f"EMA {ema_fast}"), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_candles.index, y=plot_candles['EMA_Slow'], line=dict(color='cyan', width=1.2), name=f"EMA {ema_slow}"), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_candles.index, y=plot_candles['ST_Line'], line=dict(color='yellow', dash='dash'), name="Supertrend"), row=1, col=1)

            # ট্রেড প্ল্যান অনুভূমিক লাইন
            fig.add_hline(y=row_data['Target'], line_dash="dash", line_color="#10b981", annotation_text="Target", row=1, col=1)
            fig.add_hline(y=row_data['Stop'], line_dash="dash", line_color="#f43f5e", annotation_text="Stop Loss", row=1, col=1)

            # ভলিউম বার
            colors = ['#10b981' if c >= o else '#f43f5e' for c, o in zip(plot_candles['Close'], plot_candles['Open'])]
            fig.add_trace(go.Bar(x=plot_candles.index, y=plot_candles['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

            fig.update_layout(
                title=f"{sel_stock} Candlestick & Trade Levels View",
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                height=520,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

            # চার্ট ২: হিস্টোরিক্যাল ব্যাকটেস্ট (Equity Curve & Drawdown)
            st.markdown("#### 📈 Historical Strategy Backtest (Equity Curve & Drawdown)")
            
            # সিম্পল ব্যাকটেস্ট সিমুলেশন (EMA Crossover Strategy)
            backtest_df = sdf.copy()
            backtest_df['Signal'] = np.where(backtest_df['EMA_Fast'] > backtest_df['EMA_Slow'], 1, 0)
            backtest_df['Market_Returns'] = backtest_df['Close'].pct_change()
            backtest_df['Strategy_Returns'] = backtest_df['Market_Returns'] * backtest_df['Signal'].shift(1)
            
            # ইকুইটি ও ড্রডাউন
            backtest_df['Equity_Curve'] = capital * (1 + backtest_df['Strategy_Returns']).cumprod()
            backtest_df['Peak'] = backtest_df['Equity_Curve'].cummax()
            backtest_df['Drawdown'] = ((backtest_df['Equity_Curve'] - backtest_df['Peak']) / backtest_df['Peak']) * 100

            bfig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=["Equity Curve (₹)", "Drawdown %"])
            
            bfig.add_trace(go.Scatter(x=backtest_df.index, y=backtest_df['Equity_Curve'], line=dict(color='#38bdf8', width=2), name="Strategy Equity"), row=1, col=1)
            bfig.add_trace(go.Scatter(x=backtest_df.index, y=backtest_df['Drawdown'], fill='tozeroy', line=dict(color='#f43f5e', width=1), name="Drawdown %"), row=2, col=1)

            bfig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20), xaxis_rangeslider_visible=False)
            st.plotly_chart(bfig, use_container_width=True)
            
            # ব্যাকটেস্ট সারাংশ পরিসংখ্যান
            total_ret = ((backtest_df['Equity_Curve'].iloc[-1] - capital) / capital) * 100
            max_dd = backtest_df['Drawdown'].min()
            bcol1, bcol2, bcol3 = st.columns(3)
            bcol1.metric("Final Strategy Capital", f"₹{round(backtest_df['Equity_Curve'].iloc[-1], 2)}")
            bcol2.metric("Total Return", f"{round(total_ret, 2)}%")
            bcol3.metric("Max Drawdown", f"{round(max_dd, 2)}%")
    else:
        st.info("👆 স্ক্যান শুরু করতে ওপরের 'Run Live Scan Now' বাটনে ক্লিক করুন।")
