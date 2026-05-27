import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go  # ⚡ 引入頂級 Plotly 獨立繪圖引擎
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from concurrent.futures import ThreadPoolExecutor

# 網頁基本設定 (設定深色主題與寬版排版)
st.set_page_config(page_title="Crypto Quant Terminal Pro", layout="wide", initial_sidebar_state="expanded")

# ⚡ 核心功能：設定網頁每 5 秒自動在背景重新整理一次 (5000 毫秒)
st_autorefresh(interval=5000, key="crypto_terminal_refresh")

# ----------------------------------------------------------------
# 👑 頂級視覺與排版優化：毛玻璃（Glassmorphism）與精準佈局
# ----------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #141923 0%, #090b0e 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #f1f5f9;
    }
    
    h1 {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
        font-weight: 800 !important;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #00ffcc 0%, #00bcff 50%, #7928ca 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 12px;
        font-size: 2.6rem !important;
        text-shadow: 0 0 40px rgba(0, 255, 204, 0.15);
    }
    
    h2, h3 {
        color: #00ffcc !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.3px;
        margin-top: 1.5rem !important;
        margin-bottom: 0.8rem !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(20, 26, 38, 0.5) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 20px 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stMetric"]:hover {
        border: 1px solid rgba(0, 255, 204, 0.4) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 255, 204, 0.1) !important;
        transform: translateY(-4px);
    }
    
    button[data-baseweb="tab"] {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
        color: #94a3b8 !important;
    }
    button[aria-selected="true"] {
        background: rgba(0, 255, 204, 0.1) !important;
        border-color: rgba(0, 255, 204, 0.3) !important;
        color: #00ffcc !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0b0e14 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    div.stAlert {
        background: rgba(22, 28, 36, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(8px);
    }
    </style>
""", unsafe_allow_html=True)

# 📋 50 大熱門代幣資產清單
CRYPTO_LIST = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
    "ADAUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT",
    "SHIBUSDT", "TONUSDT", "SUIUSDT", "NEARUSDT", "APTUSDT",
    "FETUSDT", "OPUSDT", "ARBUSDT", "WIFUSDT", "PEPEUSDT",
    "MATICUSDT", "LTCUSDT", "UNIUSDT", "ICPUSDT", "FILUSDT", 
    "STXUSDT", "IMXUSDT", "GRTUSDT", "RNDRUSDT", "THETAUSDT", 
    "ATOMUSDT", "XLMUSDT", "HBARUSDT", "MKRUSDT", "LDOUSDT", 
    "TIAUSDT", "INJUSDT", "WLDUSDT", "SEIUSDT", "FTMUSDT", 
    "PENDLEUSDT", "JUPUSDT", "PYTHUSDT", "BONKUSDT", "FLOKIUSDT", 
    "ORDIUSDT", "1INCHUSDT", "CRVUSDT", "ALGOUSDT", "EGLDUSDT"
]

TOP_10_LIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"]

def get_crypto_data(symbol, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=150"
        res = requests.get(url, timeout=5).json()
        df = pd.DataFrame(res, columns=[
            'Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'Close_time', 'Quote_asset_volume', 'Number_of_trades', 
            'Taker_buy_base', 'Taker_buy_quote', 'Ignore'
        ])
        df['Open_time'] = pd.to_datetime(df['Open_time'], unit='ms') + pd.Timedelta(hours=8)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = df[col].astype(float)
        return df
    except:
        return None

# 🛡️ 雙向評分引擎 (融入 ATR 波動因子)
def compute_bi_directional_score(df):
    if df is None or len(df) < 50:
        return 50, 50, 0.0
    try:
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        bb_df = ta.bbands(df['Close'], length=20, std=2)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        macd_line_col = [c for c in macd_df.columns if c.startswith('MACD_')][0]
        macd_signal_col = [c for c in macd_df.columns if c.startswith('MACDs_')][0]
        macd_hist_col = [c for c in macd_df.columns if c.startswith('MACDh_')][0]
        bb_upper_col = [c for c in bb_df.columns if c.startswith('BBU_')][0]
        bb_lower_col = [c for c in bb_df.columns if c.startswith('BBL_')][0]
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = latest['Close']
        atr_val = latest['ATR'] if not pd.isna(latest['ATR']) else 0.0
        
        # 多頭分數
        ls = 0
        if latest['RSI'] < 35 and latest['RSI'] > prev['RSI']: ls += 30
        elif 35 <= latest['RSI'] <= 60 and latest['RSI'] > prev['RSI']: ls += 20
        if latest[macd_line_col] > latest[macd_signal_col] and latest[macd_hist_col] > prev[macd_hist_col]: ls += 30
        b_range = latest[bb_upper_col] - latest[bb_lower_col]
        if b_range > 0:
            pos = (current_price - latest[bb_lower_col]) / b_range
            if pos < 0.25 and latest['RSI'] > prev['RSI']: ls += 20
        if current_price > latest['EMA20'] and prev['Close'] > prev['EMA20']: ls += 20
        
        # 空頭分數
        ss = 0
        if latest['RSI'] > 65 and latest['RSI'] < prev['RSI']: ss += 30
        elif 40 <= latest['RSI'] <= 65 and latest['RSI'] < prev['RSI']: ss += 20
        if latest[macd_line_col] < latest[macd_signal_col] and latest[macd_hist_col] < prev[macd_hist_col]: ss += 30
        if b_range > 0:
            pos = (current_price - latest[bb_lower_col]) / b_range
            if pos > 0.75 and latest['RSI'] < prev['RSI']: ss += 20
        if current_price < latest['EMA20'] and prev['Close'] < prev['EMA20']: ss += 20
        
        return ls, ss, atr_val
    except:
        return 50, 50, 0.0

def compute_coin_bi_radar(symbol):
    tfs = ["15m", "1h", "1d"]
    tf_results = {}
    try:
        for tf in tfs:
            df_tf = get_crypto_data(symbol, tf)
            l_score, s_score, atr = compute_bi_directional_score(df_tf)
            tf_results[tf] = {"long": l_score, "short": s_score}
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

def get_all_tickers():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=4).json()
        return {item['symbol']: item for item in res if item['symbol'] in TOP_10_LIST}
    except:
        return {}

# ----------------------------------------------------------------
# 控制面板與側邊欄
# ----------------------------------------------------------------
st.sidebar.markdown("<h2 style='font-size:1.4rem; margin-top:0px; margin-bottom:20px;'>📊 量化控制中心</h2>", unsafe_allow_html=True)
symbol = st.sidebar.selectbox("分析核心標的", CRYPTO_LIST)
interval = st.sidebar.selectbox("時間顆粒度", ["15m", "1h", "4h", "1d"])

df = get_crypto_data(symbol, interval)
all_tickers = get_all_tickers()
long_score, short_score, atr_value = compute_bi_directional_score(df)

try:
    if symbol in all_tickers: current_price = float(all_tickers[symbol]['lastPrice'])
    else:
        price_res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=2).json()
        current_price = float(price_res['price'])
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
    
    st.sidebar.info(
        f"💡 **波動率風控核心** (ATR: {atr_value:.4f}):\n"
        f"- 做多動態止損：${long_atr_sl:,.4f}\n"
        f"- 做空動態止損：${short_atr_sl:,.4f}\n"
        f"- 建議下單數量：{pos_size:.4f} 顆\n"
        f"- 下單名義總值：${total_inv:.2f} USD"
    )

# ----------------------------------------------------------------
# 主畫面 - 上方即時熱力走馬燈
# ----------------------------------------------------------------
st.title("⚡ Crypto Quant Terminal Pro")

if all_tickers:
    ticker_items_html = ""
    for coin in TOP_10_LIST:
        data = all_tickers.get(coin, {})
        if data:
            c_price = float(data['lastPrice'])
            c_change = float(data['priceChangePercent'])
            coin_name = coin.replace("USDT", "")
            bg_color = "rgba(0, 255, 204, 0.03)" if c_change >= 0 else "rgba(255, 74, 90, 0.03)"
            border_color = "rgba(0, 255, 204, 0.12)" if c_change >= 0 else "rgba(255, 74, 90, 0.12)"
            color = "#00ffcc" if c_change >= 0 else "#ff4a5a"
            arrow = "▲" if c_change >= 0 else "▼"
            
            ticker_items_html += f"""
                <div style="background: {bg_color}; border: 1px solid {border_color}; padding: 10px 14px; border-radius: 12px; display: inline-block; min-width: 140px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-right: 4px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px;">{coin_name}</div>
                    <div style="font-size: 15px; font-weight: 700; color: #ffffff; font-family: 'JetBrains Mono', monospace;">${c_price:,.2f}</div>
                    <div style="font-size: 12px; font-weight: 700; color: {color}; margin-top: 4px;">{arrow} {c_change:+.2f}%</div>
                </div>
            """
    full_ticker_html = f"""
    <div style="display: flex; gap: 12px; overflow-x: auto; white-space: nowrap; padding: 5px 2px 12px 2px; width: 100%; height: 95px; scrollbar-width: none;">
        {ticker_items_html}
    </div>
    """
    components.html(full_ticker_html, height=95)

# ----------------------------------------------------------------
# 頁籤分流控制核心
# ----------------------------------------------------------------
tab_main, tab_radar, tab_macro = st.tabs([
    "📈 實時獨立大腦 (本地量化圖表引擎)", 
    "📡 全時區雙向雷達 (50大代幣掃描)", 
    "📰 宏觀事件牆 (加密新聞 & 財經日曆)"
])

# --- 頁籤一：實時分析大腦 ---
with tab_main:
    if df is not None and len(df) >= 50 and current_price > 0:
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        bb_df = ta.bbands(df['Close'], length=20, std=2)
        df = pd.concat([df, bb_df], axis=1)
        
        macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        macd_line = macd_df.iloc[-1, 0]
        macd_signal = macd_df.iloc[-1, 1]
        
        rsi = df['RSI'].iloc[-1]
        ema20 = df['EMA20'].iloc[-1]
        
        st.markdown(f"### 📊 {symbol} 當前量化技術因子 ({interval})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("當前精確價", f"${current_price:,.4f}")
        c2.metric("動態情緒 (RSI)", f"{rsi:.2f}", "極度過熱" if rsi > 75 else "恐慌超賣" if rsi < 25 else "狀態穩定", delta_color="off")
        c3.metric("MACD 動能柱", f"{(macd_line-macd_signal):.4f}")
        c4.metric("EMA20 趨勢生命線", f"${ema20:,.4f}")
        
        st.markdown("### 🤖 量化大腦雙向決策引擎")
        if long_score >= 75: st.success(f"🎯 **【多頭核心共振：{long_score} 分】** 建議：強烈建議佈局多單。2倍 ATR 波動防護軌道已同步啟動。")
        elif short_score >= 75: st.error(f"⚠️ **【空頭核心派發：{short_score} 分】** 建議：嚴禁建倉多單。建議依風控軌道佈局空單（Short）。")
        else: st.info(f"⏳ **【市場多空拉鋸】 多頭：{long_score}分 | 空頭：{short_score}分** 建議：多空動能不顯著，建議保持觀望。")
        
        st.markdown(f"### 📈 {symbol} 獨立量化自製走勢圖")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            row_width=[0.25, 0.75])
        
        # 繪製主 K 線
        fig.add_trace(go.Candlestick(
            x=df['Open_time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="K線",
            increasing=dict(fillcolor='#00ffcc', line=dict(color='#00ffcc')),
            decreasing=dict(fillcolor='#ff4a5a', line=dict(color='#ff4a5a'))
        ), row=1, col=1)
        
        # 繪製 EMA20
        fig.add_trace(go.Scatter(
            x=df['Open_time'], y=df['EMA20'], 
            line=dict(color='#ffcc00', width=1.5), 
            name="EMA20 趨勢線"
        ), row=1, col=1)
        
        # 欄位防禦安全過濾
        bb_upper_list = [c for c in df.columns if c.startswith('BBU_')]
        bb_lower_list = [c for c in df.columns if c.startswith('BBL_')]
        
        if bb_upper_list and bb_lower_list:
            bb_upper_col = bb_upper_list[0]
            bb_lower_col = bb_lower_list[0]
            fig.add_trace(go.Scatter(x=df['Open_time'], y=df[bb_upper_col], line=dict(color='rgba(0, 188, 255, 0.3)', width=1, dash='dash'), name="布林上軌"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Open_time'], y=df[bb_lower_col], line=dict(color='rgba(0, 188, 255, 0.3)', width=1, dash='dash'), name="布林下軌"), row=1, col=1)
        
        # 繪製副圖 RSI
        fig.add_trace(go.Scatter(
            x=df['Open_time'], y=df['RSI'], 
            line=dict(color='#00bcff', width=1.5), 
            name="RSI (14)"
        ), row=2, col=1)
        
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(255, 74, 90, 0.4)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(0, 255, 204, 0.4)", row=2, col=1)
        
        # ⚡ ⚡ ⚡ 語法錯誤修復完成線
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(20, 26, 38, 0.4)",
            height=600,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.03)', zeroline=False)
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.03)')
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.error("❌ 交易所數據初始化失敗或K線資料不足")

# --- 頁籤二：全時區雙向雷達 ---
with tab_radar:
    st.markdown("### 📡 智能跨週期雙向雷達 (多頭共振 / 空頭派發全方位掃描)")
    with st.spinner("雙向防禦引擎平行對驗中..."):
        bi_market_data = scan_full_market_bi_directional()

    long_signals = []
    short_signals = []

    for coin_symbol, tfs_data in bi_market_data:
        coin_name = coin_symbol.replace("USDT", "")
        for tf, scores in tfs_data.items():
            if scores["long"] >= 75: long_signals.append(f"**{coin_name}** `({tf}:{scores['long']}分)`")
            if scores["short"] >= 75: short_signals.append(f"**{coin_name}** `({tf}:{scores['short']}分)`")

    radar_c1, radar_c2 = st.columns(2)
    with radar_c1:
        if long_signals: st.success(f"🎯 **多頭強力共振（建議做多 $\ge 75$分）**：\n\n" + " &nbsp;•&nbsp; ".join(long_signals))
        else: st.markdown("<div style='padding:12px; border-radius:10px; background:rgba(255,255,255,0.02); color:#94a3b8;'>🎰 市場無多頭共振資產。已啟動嚴格過濾。</div>", unsafe_allow_html=True)

    with radar_c2:
        if short_signals: st.error(f"⚠️ **空頭強烈派發（建議做空 $\ge 75$分）**：\n\n" + " &nbsp;•&nbsp; ".join(short_signals))
        else: st.markdown("<div style='padding:12px; border-radius:10px; background:rgba(255,255,255,0.02); color:#94a3b8;'>🎰 市場結構穩定，暫無高威脅空頭派發資產。</div>", unsafe_allow_html=True)

# --- 頁籤三：宏觀事件牆 ---
with tab_macro:
    st.markdown("### 📰 華爾街即時財經週報與事件牆")
    macro_html = """
    <div style="display: flex; gap: 15px; width:100%; height: 550px;">
        <div class="tradingview-widget-container" style="flex: 1; border-radius:12px; overflow:hidden; border: 1px solid rgba(255,255,255,0.06); background: transparent;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
          {
          "feedMode": "market",
          "market": "crypto",
          "colorTheme": "dark",
          "isTransparent": true,
          "height": 550,
          "locale": "zh_TW"
          }
          </script>
        </div>
        <div class="tradingview-widget-container" style="flex: 1; border-radius:12px; overflow:hidden; border: 1px solid rgba(255,255,255,0.06); background: transparent;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
          {
          "colorTheme": "dark",
          "isTransparent": true,
          "width": "100%",
          "height": 550,
          "locale": "zh_TW",
          "importanceFilter": "0,1"
          }
          </script>
        </div>
    </div>
    """
    components.html(macro_html, height=560)