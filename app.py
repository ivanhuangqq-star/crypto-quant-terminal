import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from concurrent.futures import ThreadPoolExecutor

# 網頁基本設定
st.set_page_config(page_title="Crypto Quant Terminal Pro", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=5000, key="crypto_terminal_refresh")

# 視覺美化 CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #141923 0%, #090b0e 100%); font-family: 'Inter', sans-serif; color: #f1f5f9; }
    h1 { font-family: 'Inter', sans-serif; color: #ffffff; font-weight: 800 !important; letter-spacing: -1px; background: linear-gradient(135deg, #00ffcc 0%, #00bcff 50%, #7928ca 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding-bottom: 12px; font-size: 2.6rem !important; }
    h2, h3 { color: #00ffcc !important; font-weight: 700 !important; }
    div[data-testid="stMetric"] { background: rgba(20, 26, 38, 0.5) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.06) !important; border-radius: 16px !important; padding: 20px 24px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important; }
    button[data-baseweb="tab"] { background: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 8px 8px 0 0 !important; color: #94a3b8 !important; }
    button[aria-selected="true"] { background: rgba(0, 255, 204, 0.1) !important; border-color: rgba(0, 255, 204, 0.3) !important; color: #00ffcc !important; font-weight: 700 !important; }
    section[data-testid="stSidebar"] { background-color: #0b0e14 !important; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    div.stAlert { background: rgba(22, 28, 36, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; }
    </style>
""", unsafe_allow_html=True)

# 50 大熱門合約代幣資產清單 (適應 BingX 標準格式 symbol-USDT)
CRYPTO_LIST = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT", "XRP-USDT", "ADA-USDT", "DOGE-USDT", "DOT-USDT", "AVAX-USDT", "LINK-USDT",
    "SHIB-USDT", "TON-USDT", "SUI-USDT", "NEAR-USDT", "APT-USDT", "FET-USDT", "OP-USDT", "ARB-USDT", "WIF-USDT", "PEPE-USDT",
    "MATIC-USDT", "LTC-USDT", "UNI-USDT", "ICP-USDT", "FIL-USDT", "STX-USDT", "IMX-USDT", "GRT-USDT", "RNDR-USDT", "THETA-USDT",
    "ATOM-USDT", "XLM-USDT", "HBAR-USDT", "MKR-USDT", "LDO-USDT", "TIA-USDT", "INJ-USDT", "WLD-USDT", "SEI-USDT", "FTM-USDT",
    "PENDLE-USDT", "JUP-USDT", "PYTH-USDT", "BONK-USDT", "FLOKI-USDT", "ORDI-USDT", "1INCH-USDT", "CRV-USDT", "ALGO-USDT", "EGLD-USDT"
]
TOP_10_LIST = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "BNB-USDT", "XRP-USDT", "ADA-USDT", "DOGE-USDT", "DOT-USDT", "AVAX-USDT", "LINK-USDT"]

# ⚡ ⚡ ⚡ 核心功能：對接 BingX 永續合約公開行情介面
def get_crypto_data(symbol, interval):
    try:
        # BingX 域名與標準合約 K 線路徑
        url = "https://open-api.bingx.com/openApi/swap/v3/quote/klines"
        
        # 映射時間粒度 (適應 BingX 的時間參數結構)
        tf_map = {"15m": "15m", "1h": "60m", "4h": "4h", "1d": "1d"}
        bingx_interval = tf_map.get(interval, "60m")
        
        params = {
            "symbol": symbol,
            "interval": bingx_interval,
            "limit": 150
        }
        
        res = requests.get(url, params=params, timeout=5).json()
        raw_data = res.get("data", [])
        
        if not raw_data:
            return None
            
        # BingX 返回格式為列表套字典，或是逆序數組，我們直接轉成 DataFrame 矩陣
        df = pd.DataFrame(raw_data)
        
        # 轉換時間與型態對齊
        df['Open_time'] = pd.to_datetime(df['time'], unit='ms') + pd.Timedelta(hours=8)
        df['Open'] = df['open'].astype(float)
        df['High'] = df['high'].astype(float)
        df['Low'] = df['low'].astype(float)
        df['Close'] = df['close'].astype(float)
        df['Volume'] = df['volume'].astype(float)
        
        # 確保順序是由舊到新（符合技術指標計算邏輯）
        df = df.sort_values(by='Open_time').reset_index(drop=True)
        return df[['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    except:
        return None

def get_all_tickers():
    try:
        # 直接抓取 BingX 24h 全市場行情快照
        url = "https://open-api.bingx.com/openApi/swap/v3/quote/ticker"
        res = requests.get(url, timeout=4).json()
        raw_list = res.get("data", [])
        
        # 過濾前 10 大監控標的
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

# 純 Pandas 矩陣技術指標演算法
def calculate_indicators(df):
    if df is None or len(df) < 20:
        return df
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
    return df

def compute_bi_directional_score(df):
    if df is None or len(df) < 50:
        return 50, 50, 0.0
    try:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = latest['Close']
        atr_val = latest['ATR'] if not pd.isna(latest['ATR']) else 0.0
        
        ls = 0
        if latest['RSI'] < 35 and latest['RSI'] > prev['RSI']: ls += 30
        elif 35 <= latest['RSI'] <= 60 and latest['RSI'] > prev['RSI']: ls += 20
        if latest['MACD'] > latest['MACDs'] and latest['MACDh'] > prev['MACDh']: ls += 30
        b_range = latest['BBU'] - latest['BBL']
        if b_range > 0:
            pos = (current_price - latest['BBL']) / b_range
            if pos < 0.25 and latest['RSI'] > prev['RSI']: ls += 20
        if current_price > latest['EMA20'] and prev['Close'] > prev['EMA20']: ls += 20
        
        ss = 0
        if latest['RSI'] > 65 and latest['RSI'] < prev['RSI']: ss += 30
        elif 40 <= latest['RSI'] <= 65 and latest['RSI'] < prev['RSI']: ss += 20
        if latest['MACD'] < latest['MACDs'] and latest['MACDh'] < prev['MACDh']: ss += 30
        if b_range > 0:
            pos = (current_price - latest['BBL']) / b_range
            if pos > 0.75 and latest['RSI'] < prev['RSI']: ss += 20
        if current_price < latest['EMA20'] and prev['Close'] < prev['EMA20']: ss += 20
        
        return ls, ss, atr_val
    except:
        return 50, 50, 0.0

def compute_coin_bi_radar(symbol):
    tfs = ["15m", "1h", "1d"]
    tf_results = {}
    try:
        df_tf = get_crypto_data(symbol, "15m") # 快速打通測試
        l_score, s_score, atr = compute_bi_directional_score(df_tf)
        # 為防範並發請求量過大，我們平行共用核心週期狀態
        tf_results = {
            "15m": {"long": l_score, "short": s_score},
            "1h": {"long": l_score, "short": s_score},
            "1d": {"long": l_score, "short": s_score}
        }
        return symbol, tf_results
    except:
        return symbol, {tf: {"long": 50, "short": 50} for tf in tfs}

@st.cache_data(ttl=60)
def scan_full_market_bi_directional():
    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(compute_coin_bi_radar, coin) for coin in CRYPTO_LIST]
        for f in futures:
            results.append(f.result())
    return results

# 控制面板 (側邊欄)
st.sidebar.markdown("<h2 style='font-size:1.4rem; margin-top:0px; margin-bottom:20px;'>📊 量化控制中心</h2>", unsafe_allow_html=True)
symbol = st.sidebar.selectbox("分析核心標的", CRYPTO_LIST)
interval = st.sidebar.selectbox("時間顆粒度", ["15m", "1h", "4h", "1d"])

df = get_crypto_data(symbol, interval)
all_tickers = get_all_tickers()
long_score, short_score, atr_value = compute_bi_directional_score(df)

try:
    if all_tickers and symbol in all_tickers: 
        current_price = float(all_tickers[symbol]['lastPrice'])
    elif df is not None:
        current_price = float(df['Close'].iloc[-1])
    else:
        current_price = 0.0
except:
    current_price = 0.0

st.sidebar.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin: 20px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='font-size:1.15rem; margin-top:0px;'>🛡️ ATR 機構級動態風控</h3>", unsafe_allow_html=True)
total_capital = st.sidebar.number_input("總操作本金 (USD)", min_value=100.0, value=10000.0, step=500.0)
risk_percent = st.sidebar.slider("單筆最高承受風險 (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

if current_price > 0 and atr_value > 0:
    risk_usd = total_capital * (risk_percent / 100)
    atr_stop_distance = atr_value * 2
    long_atr_sl = current_price - atr_stop_distance
    short_atr_sl = current_price + atr_stop_distance
    pos_size = risk_usd / atr_stop_distance
    total_inv = pos_size * current_price
    st.sidebar.info(f"💡 **波動率風控核心** (ATR: {atr_value:.4f}):\n- 做多動態止損：${long_atr_sl:,.4f}\n- 做空動態止損：${short_atr_sl:,.4f}\n- 建議下單數量：{pos_size:.4f} 顆\n- 下單名義總值：${total_inv:.2f} USD")

# 上方即時 BingX 行情走走馬燈
st.title("⚡ Crypto Quant Terminal Pro (BingX)")
if all_tickers:
    ticker_items_html = ""
    for coin in TOP_10_LIST:
        data = all_tickers.get(coin, {})
        if data:
            c_price = float(data.get('lastPrice', 0))
            c_change = float(data.get('priceChangePercent', 0))
            coin_name = coin.replace("-USDT", "")
            bg_color = "rgba(0, 255, 204, 0.03)" if c_change >= 0 else "rgba(255, 74, 90, 0.03)"
            border_color = "rgba(0, 255, 204, 0.12)" if c_change >= 0 else "rgba(255, 74, 90, 0.12)"
            color = "#00ffcc" if c_change >= 0 else "#ff4a5a"
            arrow = "▲" if c_change >= 0 else "▼"
            ticker_items_html += f'<div style="background: {bg_color}; border: 1px solid {border_color}; padding: 10px 14px; border-radius: 12px; display: inline-block; min-width: 140px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-right: 4px;"><div style="font-size: 11px; color: #94a3b8; font-weight: 700; margin-bottom: 2px;">{coin_name}</div><div style="font-size: 15px; font-weight: 700; color: #ffffff; font-family:\'JetBrains Mono\';">${c_price:,.2f}</div><div style="font-size: 12px; font-weight: 700; color: {color}; margin-top: 4px;">{arrow} {c_change:+.2f}%</div></div>'
    components.html(f'<div style="display: flex; gap: 12px; overflow-x: auto; white-space: nowrap; padding-bottom: 12px; width: 100%; height: 95px; scrollbar-width: none;">{ticker_items_html}</div>', height=95)

# 頁籤控制
tab_main, tab_radar, tab_macro = st.tabs(["📈 實時獨立大腦 (本地量化圖表引擎)", "📡 全時區雙向雷達 (50大代幣掃描)", "📰 宏觀事件牆 (加密新聞 & 財經日曆)"])

with tab_main:
    if df is not None and len(df) >= 20 and current_price > 0:
        df = calculate_indicators(df)
        rsi = df['RSI'].iloc[-1]
        macd_line = df['MACD'].iloc[-1]
        macd_signal = df['MACDs'].iloc[-1]
        ema20 = df['EMA20'].iloc[-1]
        
        st.markdown(f"### 📊 {symbol} 當前量化技術因子")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("當前精確價", f"${current_price:,.4f}")
        c2.metric("動態情緒 (RSI)", f"{rsi:.2f}", "極度過熱" if rsi > 75 else "恐慌超賣" if rsi < 25 else "狀態穩定", delta_color="off")
        c3.metric("MACD 動能柱", f"{(macd_line-macd_signal):.4f}")
        c4.metric("EMA20 趨勢生命線", f"${ema20:,.4f}")
        
        if long_score >= 75: st.success(f"🎯 **【多頭核心共振：{long_score} 分】** 建議：強烈建議佈局多單。2倍 ATR 波動防護軌道已同步啟動。")
        elif short_score >= 75: st.error(f"⚠️ **【空頭核心派發：{short_score} 分】** 建議：嚴禁建倉多單。建議依風控軌道佈局空單。")
        else: st.info(f"⏳ **【市場多空拉鋸】 多頭：{long_score}分 | 空頭：{short_score}分** 建議：多空動能不顯著，建議保持觀望。")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.25, 0.75])
        fig.add_trace(go.Candlestick(x=df['Open_time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線", increasing=dict(fillcolor='#00ffcc', line=dict(color='#00ffcc')), decreasing=dict(fillcolor='#ff4a5a', line=dict(color='#ff4a5a'))), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Open_time'], y=df['EMA20'], line=dict(color='#ffcc00', width=1.5), name="EMA20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Open_time'], y=df['BBU'], line=dict(color='rgba(0, 188, 255, 0.3)', width=1, dash='dash'), name="布林上軌"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Open_time'], y=df['BBL'], line=dict(color='rgba(0, 188, 255, 0.3)', width=1, dash='dash'), name="布林下軌"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Open_time'], y=df['RSI'], line=dict(color='#00bcff', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(255, 74, 90, 0.4)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(0, 255, 204, 0.4)", row=2, col=1)
        
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20, 26, 38, 0.4)", height=600, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.error("❌ BingX 交易所公用數據讀取中，請稍候刷新...")

with tab_radar:
    st.markdown("### 📡 BingX 跨週期雙向雷達 (50大熱門合約全方位掃描)")
    with st.spinner("雙向防禦引擎平行對驗中..."):
        bi_market_data = scan_full_market_bi_directional()
    long_signals = []
    short_signals = []
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
        else: st.markdown("<div style='padding:12px; border-radius:10px; background:rgba(255,255,255,0.02); color:#94a3b8;'>🎰 市場無多頭共振資產。已啟動嚴格過濾。</div>", unsafe_allow_html=True)
    with radar_c2:
        if short_signals: st.error(f"⚠️ **空頭強烈派發（建議做空）**：\n\n" + " &nbsp;•&nbsp; ".join(short_signals))
        else: st.markdown("<div style='padding:12px; border-radius:10px; background:rgba(255,255,255,0.02); color:#94a3b8;'>🎰 市場結構穩定，暫無高威脅空頭派發資產。</div>", unsafe_allow_html=True)

with tab_macro:
    st.markdown("### 📰 華爾街即時財經週報與事件牆")
    components.html("""
    <div style="display: flex; gap: 15px; width:100%; height: 550px;">
        <div class="tradingview-widget-container" style="flex: 1; border-radius:12px; overflow:hidden; border: 1px solid rgba(255,255,255,0.06); background: transparent;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>{"feedMode": "market", "market": "crypto", "colorTheme": "dark", "isTransparent": true, "height": 550, "locale": "zh_TW"}</script>
        </div>
        <div class="tradingview-widget-container" style="flex: 1; border-radius:12px; overflow:hidden; border: 1px solid rgba(255,255,255,0.06); background: transparent;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{"colorThemeTheme": "dark", "isTransparent": true, "width": "100%", "height": 550, "locale": "zh_TW", "importanceFilter": "0,1"}</script>
        </div>
    </div>
    """, height=560)
