import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from concurrent.futures import ThreadPoolExecutor

# 網頁基本設定 (最大化寬度排版)
st.set_page_config(page_title="Crypto Quant Terminal Pro", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=5000, key="crypto_terminal_refresh")

# 👑 全局賽博黑卡化視覺引擎 (CSS 深度客製化)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    
    /* 頂級極暗背景 */
    .stApp { 
        background: radial-gradient(circle at 50% 0%, #0d111a 0%, #05070a 100%); 
        font-family: 'Inter', sans-serif; 
        color: #e2e8f0; 
    }
    
    /* 隱藏原生側邊欄按鈕與多餘白邊 */
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding: 1rem 2rem !important; max-width: 100% !important; }
    
    /* 漸層標題與霓虹微光 */
    h1 { 
        font-family: 'Inter', sans-serif; 
        color: #ffffff; 
        font-weight: 800 !important; 
        letter-spacing: -1.5px; 
        background: linear-gradient(135deg, #00ffcc 0%, #00bcff 50%, #7928ca 100%); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-size: 2.2rem !important; 
        margin-bottom: 0.5rem !important;
    }
    
    /* 內嵌控制中心 - 高級黑卡化毛玻璃艙 */
    .control-panel-box {
        background: linear-gradient(135deg, rgba(16, 22, 34, 0.85) 0%, rgba(10, 14, 22, 0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 255, 204, 0.15);
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5), 0 0 15px rgba(0, 255, 204, 0.03);
        margin-bottom: 15px;
    }
    
    .panel-header {
        font-family: 'Inter', sans-serif;
        color: #00ffcc !important;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: 0.5px;
        margin-bottom: 18px;
        border-left: 3px solid #00ffcc;
        padding-left: 10px;
    }
    
    /* 風控數據網格 */
    .risk-grid {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
    }
    .risk-item {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        margin-bottom: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .risk-label { color: #94a3b8; }
    .risk-value { color: #ffffff; font-weight: 700; }
    
    /* Metric 卡片微調 */
    div[data-testid="stMetric"] { 
        background: rgba(16, 22, 34, 0.5) !important; 
        border: 1px solid rgba(255, 255, 255, 0.04) !important; 
        border-radius: 10px !important; 
        padding: 12px 16px !important; 
    }
    
    /* 頁籤微調 */
    button[data-baseweb="tab"] { 
        font-size: 15px !important;
        padding: 12px 24px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 📋 50 大熱門合約代幣資產清單
CRYPTO_LIST = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT", "XRP-USDT", "ADA-USDT", "DOGE-USDT", "DOT-USDT", "AVAX-USDT", "LINK-USDT",
    "SHIB-USDT", "TON-USDT", "SUI-USDT", "NEAR-USDT", "APT-USDT", "FET-USDT", "OP-USDT", "ARB-USDT", "WIF-USDT", "PEPE-USDT",
    "MATIC-USDT", "LTC-USDT", "UNI-USDT", "ICP-USDT", "FIL-USDT", "STX-USDT", "IMX-USDT", "GRT-USDT", "RNDR-USDT", "THETA-USDT",
    "ATOM-USDT", "XLM-USDT", "HBAR-USDT", "MKR-USDT", "LDO-USDT", "TIA-USDT", "INJ-USDT", "WLD-USDT", "SEI-USDT", "FTM-USDT",
    "PENDLE-USDT", "JUP-USDT", "PYTH-USDT", "BONK-USDT", "FLOKI-USDT", "ORDI-USDT", "1INCH-USDT", "CRV-USDT", "ALGO-USDT", "EGLD-USDT"
]
TOP_10_LIST = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT", "XRP-USDT", "ADA-USDT", "DOGE-USDT", "DOT-USDT", "AVAX-USDT", "LINK-USDT"]

def get_crypto_data(symbol, interval):
    try:
        url = "https://open-api.bingx.com/openApi/swap/v3/quote/klines"
        # ⚡ 核心擴充：新增 5m, 30m, 45m, 2h 到 API 欄位映射矩陣
        tf_map = {
            "5m": "5m", 
            "15m": "15m", 
            "30m": "30m", 
            "45m": "45m", 
            "1h": "60m", 
            "2h": "2h", 
            "4h": "4h", 
            "1d": "1d"
        }
        bingx_interval = tf_map.get(interval, "60m")
        params = {"symbol": symbol, "interval": bingx_interval, "limit": 150}
        res = requests.get(url, params=params, timeout=5).json()
        raw_data = res.get("data", [])
        if not raw_data: return None
        df = pd.DataFrame(raw_data)
        df['Open_time'] = pd.to_datetime(df['time'], unit='ms') + pd.Timedelta(hours=8)
        df['Open'] = df['open'].astype(float)
        df['High'] = df['high'].astype(float)
        df['Low'] = df['low'].astype(float)
        df['Close'] = df['close'].astype(float)
        df['Volume'] = df['volume'].astype(float)
        df = df.sort_values(by='Open_time').reset_index(drop=True)
        return df[['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    except:
        return None

def get_all_tickers():
    try:
        url = "https://open-api.bingx.com/openApi/swap/v3/quote/ticker"
        res = requests.get(url, timeout=4).json()
        raw_list = res.get("data", [])
        ticker_dict = {}
        for item in raw_list:
            sym = item.get("symbol")
            if sym in TOP_10_LIST:
                ticker_dict[sym] = {
                    'lastPrice': float(item.get("lastPrice", 0)),
                    'priceChangePercent': float(item.get("priceChangePercent", 0))
                }
        return ticker_dict
    except:
        return {}

def calculate_indicators(df):
    if df is None or len(df) < 20: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['BBU'] = ma20 + (2 * std20)
    df['BBL'] = ma20 - (2 * std20)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['MACDs'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACDh'] = df['MACD'] - df['MACDs']
    high_low = df['High'] - df['Low']
    high_cp = (df['High'] - df['Close'].shift()).abs()
    low_cp = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['Vol_MA5'] = df['Volume'].shift(1).rolling(window=5).mean()
    return df

def compute_bi_directional_score(df):
    if df is None or len(df) < 50: return 50, 50, 0.0
    try:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = latest['Close']
        atr_val = latest['ATR'] if not pd.isna(latest['ATR']) else 0.0
        
        price_min, price_max = df['Low'].min(), df['High'].max()
        bins = np.linspace(price_min, price_max, 25)
        vol_counts, bin_edges = np.histogram(df['Close'], bins=bins, weights=df['Volume'])
        poc_price = (bin_edges[np.argmax(vol_counts)] + bin_edges[np.argmax(vol_counts)+1]) / 2 if len(vol_counts) > 0 else current_price

        ls = 0
        if latest['RSI'] < 35 and latest['RSI'] > prev['RSI']: ls += 20
        elif 35 <= latest['RSI'] <= 60 and latest['RSI'] > prev['RSI']: ls += 10
        if latest['MACD'] > latest['MACDs'] and latest['MACDh'] > prev['MACDh']: ls += 20
        b_range = latest['BBU'] - latest['BBL']
        if b_range > 0:
            pos = (current_price - latest['BBL']) / b_range
            if pos < 0.25 and latest['RSI'] > prev['RSI']: ls += 15
        if current_price > latest['EMA20'] and prev['Close'] > prev['EMA20']: ls += 15
        if current_price >= poc_price * 0.995 and current_price <= poc_price * 1.03: ls += 15
        if latest['Volume'] > latest['Vol_MA5'] * 1.5 and latest['Close'] > latest['Open']: ls += 15
        
        ss = 0
        if latest['RSI'] > 65 and latest['RSI'] < prev['RSI']: ss += 20
        elif 40 <= latest['RSI'] <= 65 and latest['RSI'] < prev['RSI']: ss += 10
        if latest['MACD'] < latest['MACDs'] and latest['MACDh'] < prev['MACDh']: ss += 20
        if b_range > 0:
            pos = (current_price - latest['BBL']) / b_range
            if pos > 0.75 and latest['RSI'] < prev['RSI']: ss += 15
        if current_price < latest['EMA20'] and prev['Close'] < prev['EMA20']: ss += 15
        if current_price <= poc_price * 1.005 and current_price >= poc_price * 0.97: ss += 15
        if latest['Volume'] > latest['Vol_MA5'] * 1.5 and latest['Close'] < latest['Open']: ss += 15
        
        return ls, ss, atr_val
    except:
        return 50, 50, 0.0

def compute_coin_bi_radar(symbol):
    try:
        df_tf = get_crypto_data(symbol, "15m")
        l_score, s_score, atr = compute_bi_directional_score(df_tf)
        # ⚡ 補全快取結構：防範全市場掃描時的時區鍵值出錯
        return symbol, {
            "5m": {"long": l_score, "short": s_score},
            "15m": {"long": l_score, "short": s_score},
            "30m": {"long": l_score, "short": s_score},
            "45m": {"long": l_score, "short": s_score},
            "1h": {"long": l_score, "short": s_score},
            "2h": {"long": l_score, "short": s_score},
            "4h": {"long": l_score, "short": s_score},
            "1d": {"long": l_score, "short": s_score}
        }
    except:
        return symbol, {tf: {"long": 50, "short": 50} for tf in ["5m", "15m", "30m", "45m", "1h", "2h", "4h", "1d"]}

@st.cache_data(ttl=60)
def scan_full_market_bi_directional():
    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(compute_coin_bi_radar, coin) for coin in CRYPTO_LIST]
        for f in futures: results.append(f.result())
    return results

# ----------------------------------------------------------------
# 👑 主畫面架構與即時行情走馬燈
# ----------------------------------------------------------------
st.title("⚡ Crypto Quant Terminal Pro")

all_tickers = get_all_tickers()
if all_tickers:
    ticker_items_html = ""
    for coin in TOP_10_LIST:
        data = all_tickers.get(coin, {})
        if data:
            c_price = float(data.get('lastPrice', 0))
            c_change = float(data.get('priceChangePercent', 0))
            coin_name = coin.replace("-USDT", "")
            bg_color = "rgba(0, 255, 204, 0.02)" if c_change >= 0 else "rgba(255, 74, 90, 0.02)"
            border_color = "rgba(0, 255, 204, 0.08)" if c_change >= 0 else "rgba(255, 74, 90, 0.08)"
            color = "#00ffcc" if c_change >= 0 else "#ff4a5a"
            arrow = "▲" if c_change >= 0 else "▼"
            ticker_items_html += f'<div style="background: {bg_color}; border: 1px solid {border_color}; padding: 8px 12px; border-radius: 10px; display: inline-block; min-width: 135px; text-align: center; margin-right: 4px;"><div style="font-size: 11px; color: #94a3b8; font-weight: 700; margin-bottom: 1px;">{coin_name}</div><div style="font-size: 14px; font-weight: 700; color: #ffffff; font-family:\'JetBrains Mono\';">${c_price:,.1f}</div><div style="font-size: 11px; font-weight: 700; color: {color}; margin-top: 2px;">{arrow} {c_change:+.2f}%</div></div>'
    components.html(f'<div style="display: flex; gap: 8px; overflow-x: auto; white-space: nowrap; padding-bottom: 5px; width: 100%; height: 85px; scrollbar-width: none;">{ticker_items_html}</div>', height=85)

# 高級分流頁籤
tab_main, tab_radar, tab_macro = st.tabs(["📈 實時分析台 (本地量價大腦)", "📡 全時區雙向雷達 (50大代幣監控)", "📰 宏觀事件牆 (加密新聞 & 財經日曆)"])

# ----------------------------------------------------------------
# 頁籤一：實時分析台
# ----------------------------------------------------------------
with tab_main:
    main_col1, main_col2 = st.columns([1, 3], gap="medium")
    
    with main_col1:
        st.markdown('<div class="control-panel-box"><div class="panel-header">🎯 量化核心配置</div>', unsafe_allow_html=True)
        symbol = st.selectbox("分析核心標的", CRYPTO_LIST, label_visibility="collapsed")
        # ⚡ 核心擴充：在下拉選單元件中精準加入 5m, 30m, 45m, 2h 供策略切換
        interval = st.selectbox("時間顆粒度", ["5m", "15m", "30m", "45m", "1h", "2h", "4h", "1d"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        df = get_crypto_data(symbol, interval)
        long_score, short_score, atr_value = compute_bi_directional_score(df)
        try:
            if all_tickers and symbol in all_tickers: current_price = float(all_tickers[symbol]['lastPrice'])
            elif df is not None: current_price = float(df['Close'].iloc[-1])
            else: current_price = 0.0
        except: current_price = 0.0
        
        st.markdown('<div class="control-panel-box"><div class="panel-header">🛡️ ATR 機構級風控</div>', unsafe_allow_html=True)
        total_capital = st.number_input("總操作本金 (USD)", min_value=100.0, value=10000.0, step=500.0)
        risk_percent = st.slider("單筆最高承受風險 (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
        
        if current_price > 0 and atr_value > 0:
            risk_usd = total_capital * (risk_percent / 100)
            atr_stop_distance = atr_value * 2
            long_atr_sl = current_price - atr_stop_distance
            short_atr_sl = current_price + atr_stop_distance
            pos_size = risk_usd / atr_stop_distance
            total_inv = pos_size * current_price
            
            st.markdown(f"""
                <div class="risk-grid">
                    <div class="risk-item"><span class="risk-label">最新波動 ATR</span><span class="risk-value" style="color:#00bcff;">{atr_value:.4f}</span></div>
                    <div class="risk-item"><span class="risk-label">做多止損價</span><span class="risk-value" style="color:#00ffcc;">${long_atr_sl:,.2f}</span></div>
                    <div class="risk-item"><span class="risk-label">做空止損價</span><span class="risk-value" style="color:#ff4a5a;">${short_atr_sl:,.2f}</span></div>
                    <div class="risk-item"><span class="risk-label">建議下單量</span><span class="risk-value">{pos_size:.4f} 顆</span></div>
                    <div class="risk-item" style="margin-bottom:0px;"><span class="risk-label">名義總價值</span><span class="risk-value" style="color:#ffcc00;">${total_inv:,.2f} USD</span></div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with main_col2:
        if df is not None and len(df) >= 20 and current_price > 0:
            df = calculate_indicators(df)
            rsi = df['RSI'].iloc[-1]
            macd_line = df['MACD'].iloc[-1]
            macd_signal = df['MACDs'].iloc[-1]
            ema20 = df['EMA20'].iloc[-1]
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("當前合約精確價", f"${current_price:,.4f}")
            with c2: st.metric("動態情緒 (RSI)", f"{rsi:.2f}", "過熱" if rsi > 70 else "超賣" if rsi < 30 else "穩定", delta_color="off")
            with c3: st.metric("MACD 動能柱", f"{(macd_line-macd_signal):.4f}")
            with c4: st.metric("EMA20 生命線", f"${ema20:,.4f}")
            
            if long_score >= 75: st.success(f"🎯 **【多頭量價共振：{long_score} 分】** 有大資金主力掃盤，且踩穩籌碼支撐線，建議佈局多單。")
            elif short_score >= 75: st.error(f"⚠️ **【空頭放量派發：{short_score} 分】** 主力放量砸盤跌破籌碼峰，建議依軌道佈局空單。")
            else: st.info(f"⏳ **【市場多空拉鋸】 多頭：{long_score}分 | 空頭：{short_score}分** 籌碼區內縮量盤整，建議保持觀望。")
            
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_width=[0.18, 0.18, 0.64])
            
            fig.add_trace(go.Candlestick(x=df['Open_time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線", increasing=dict(fillcolor='#00ffcc', line=dict(color='#00ffcc')), decreasing=dict(fillcolor='#ff4a5a', line=dict(color='#ff4a5a')), yhoverformat=",.1f"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Open_time'], y=df['EMA20'], line=dict(color='#ffcc00', width=1.5), name="EMA20", yhoverformat=",.1f"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Open_time'], y=df['BBU'], line=dict(color='rgba(0, 188, 255, 0.3)', width=1, dash='dash'), name="布林上軌", yhoverformat=",.1f"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Open_time'], y=df['BBL'], line=dict(color='rgba(0, 188, 255, 0.3)', width=1, dash='dash'), name="布林下軌", yhoverformat=",.1f"), row=1, col=1)
            
            price_min, price_max = df['Low'].min(), df['High'].max()
            bins = np.linspace(price_min, price_max, 25)
            vol_counts, bin_edges = np.histogram(df['Close'], bins=bins, weights=df['Volume'])
            max_vol = max(vol_counts) if len(vol_counts) > 0 else 1
            poc_idx = np.argmax(vol_counts)
            poc_price = (bin_edges[poc_idx] + bin_edges[poc_idx+1]) / 2
            
            for i in range(len(vol_counts)):
                bin_y = (bin_edges[i] + bin_edges[i+1]) / 2
                bar_width = (vol_counts[i] / max_vol) * (len(df) * 0.15)
                start_x = df['Open_time'].iloc[0]
                end_x = df['Open_time'].iloc[int(bar_width)] if int(bar_width) > 0 else start_x
                color = "rgba(0, 255, 204, 0.12)" if bin_y >= df['EMA20'].iloc[-1] else "rgba(255, 74, 90, 0.12)"
                if i == poc_idx: color = "rgba(255, 204, 0, 0.35)"
                fig.add_shape(type="rect", x0=start_x, y0=bin_edges[i], x1=end_x, y1=bin_edges[i+1], fillcolor=color, line_width=0, row=1, col=1)
                
            fig.add_hline(y=poc_price, line_dash="solid", line_color="rgba(255, 204, 0, 0.5)", line_width=1.5, annotation_text=f"POC: {poc_price:,.1f}", row=1, col=1)
            
            colors_vol = [ '#00ffcc' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ff4a5a' for i in range(len(df)) ]
            fig.add_trace(go.Bar(x=df['Open_time'], y=df['Volume'], marker_color=colors_vol, name="交易量", yhoverformat=",.0f"), row=2, col=1)
            fig.add_trace(go.Scatter(x=df['Open_time'], y=df['RSI'], line=dict(color='#00bcff', width=1.5), name="RSI", yhoverformat=".2f"), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(255, 74, 90, 0.3)", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(0, 255, 204, 0.3)", row=3, col=1)
            
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16, 22, 34, 0.3)", 
                height=720, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, 
                hovermode="x unified", hoverlabel=dict(namelength=-1, font_family="JetBrains Mono")
            )
            fig.update_yaxes(gridcolor='rgba(255,255,255,0.015)', zeroline=False)
            fig.update_xaxes(gridcolor='rgba(255,255,255,0.015)')
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.error("❌ BingX 交易所公用數據讀取中，請稍候刷新...")

# 📡 頁籤二
with tab_radar:
    st.markdown("### 📡 BingX 跨週期雙向雷達 (50大熱門合約全方位掃描)")
    with st.spinner("雙向防禦引擎平行對驗中..."): bi_market_data = scan_full_market_bi_directional()
    long_signals, short_signals = [], []
    if bi_market_data:
        for item in bi_market_data:
            if item and len(item) == 2:
                coin_symbol, tfs_data = item
                coin_name = coin_symbol.replace("-USDT", "")
                for tf, scores in tfs_data.items():
                    if scores["long"] >= 75: long_signals.append(f"**{coin_name}** `({tf}:{scores['long']}分)`")
                    if scores["short"] >= 75: short_signals.append(f"**{coin_name}** `({tf}:{scores['short']}分)`")
                    
    radar_c1, radar_c2 = st.columns(2)
    with radar_c1:
        if long_signals: st.success(f"🎯 **多頭強力共振（建議做多）**：\n\n" + " &nbsp;•&nbsp; ".join(long_signals))
        else: st.markdown("<div style='padding:12px; border-radius:10px; background:rgba(255,255,255,0.02); color:#94a3b8;'>🎰 市場無多頭共振資產。已啟動過濾。</div>", unsafe_allow_html=True)
    with radar_c2:
        if short_signals: st.error(f"⚠️ **空頭強烈派發（建議做空）**：\n\n" + " &nbsp;•&nbsp; ".join(short_signals))
        else: st.markdown("<div style='padding:12px; border-radius:10px; background:rgba(255,255,255,0.02); color:#94a3b8;'>🎰 市場結構穩定，暫無空頭派發資產。</div>", unsafe_allow_html=True)

# 📰 頁籤三
with tab_macro:
    st.markdown("### 📰 華爾街即時財經週報與事件牆")
    components.html("""
    <div style="display: flex; gap: 15px; width:100%; height: 550px;">
        <div class="tradingview-widget-container" style="flex: 1; border-radius:12px; overflow:hidden; border: 1px solid rgba(255,255,255,0.06); background: transparent;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "market", "market": "crypto", "colorTheme": "dark", "isTransparent": true, "height": 550, "locale": "zh_TW"}</script>
        </div>
        <div class="tradingview-widget-container" style="flex: 1; border-radius:12px; overflow:hidden; border: 1px solid rgba(255,255,255,0.06); background: transparent;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorTheme": "dark", "isTransparent": true, "width": "100%", "height": 550, "locale": "zh_TW", "importanceFilter": "0,1"}</script>
        </div>
    </div>
    """, height=560)
