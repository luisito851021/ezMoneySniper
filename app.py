import os
import re
import requests
import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime

IS_CLOUD = os.getenv("IS_CLOUD", "false").lower() == "true"

# ── DB 連線 ───────────────────────────────────────
@st.cache_resource
def get_engine():
    if IS_CLOUD:
        from sqlalchemy import create_engine
        return create_engine(os.environ["SUPABASE_URL"], pool_pre_ping=True)
    else:
        import sqlite3
        from sqlalchemy import create_engine
        db_path = os.getenv("SQLITE_PATH", r"C:\ActiveFundRadar\etf.db")
        return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

def query(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)

FUND_NAMES = {
    "00988A": "統一全球創新",
    "00981A": "統一台股增長",
    "00992A": "群益台灣科技創新",
}

ACTION_COLOR = {
    "建倉": "🟢",
    "清倉": "🔴",
    "加碼": "📈",
    "減碼": "📉",
}

FLAG_MAP = {
    "US": "🇺🇸",
    "JP": "🇯🇵",
    "KS": "🇰🇷",
    "GY": "🇩🇪",
    "HK": "🇭🇰",
    "FP": "🇫🇷",
    "LN": "🇬🇧",
}

def get_flag(ticker: str) -> str:
    suffix = ticker.strip().split()[-1].upper()
    return FLAG_MAP.get(suffix, "")

def get_available_dates(fund_id: str) -> list[str]:
    df = query(f"""
        SELECT DISTINCT date FROM daily_changes
        WHERE fund_id = '{fund_id}'
        ORDER BY date DESC
    """)
    return df["date"].tolist()

def get_changes(fund_id: str, target_date: str) -> pd.DataFrame:
    return query(f"""
        SELECT
            ticker                               AS 代號,
            name                                 AS 名稱,
            action                               AS 動作,
            ROUND(CAST(weight_today * 100 AS NUMERIC), 2)         AS 今日權重,
            ROUND(CAST(weight_yest  * 100 AS NUMERIC), 2)         AS 昨日權重,
            ROUND(CAST(delta        * 100 AS NUMERIC), 2)         AS 權重變化,
            delta_shares                         AS 股數變化,
            shares_yest                          AS 昨日股數,
            shares_today                         AS 今日股數
        FROM daily_changes
        WHERE fund_id = '{fund_id}' AND date = '{target_date}'
        ORDER BY
            CASE action
                WHEN '建倉' THEN 1
                WHEN '清倉' THEN 2
                WHEN '加碼' THEN 3
                WHEN '減碼' THEN 4
            END,
            ABS(delta_shares) DESC,
            weight_today DESC
    """)

def get_history(fund_id: str, ticker: str) -> pd.DataFrame:
    return query(f"""
        SELECT
            date                                 AS 日期,
            action                               AS 動作,
            ROUND(CAST(weight_yest  * 100 AS NUMERIC), 2)         AS 昨日權重,
            ROUND(CAST(weight_today * 100 AS NUMERIC), 2)         AS 今日權重,
            ROUND(CAST(delta        * 100 AS NUMERIC), 2)         AS 權重變化,
            delta_shares                         AS 股數變化
        FROM daily_changes
        WHERE fund_id = '{fund_id}' AND ticker = '{ticker}'
        ORDER BY date DESC
    """)

def get_all_history(fund_id: str, n_days: int = 30) -> pd.DataFrame:
    return query(f"""
        SELECT
            date                                 AS 日期,
            ticker                               AS 代號,
            name                                 AS 名稱,
            action                               AS 動作,
            ROUND(CAST(weight_today * 100 AS NUMERIC), 2)         AS 今日權重,
            ROUND(CAST(delta        * 100 AS NUMERIC), 2)         AS 權重變化,
            delta_shares                         AS 股數變化
        FROM daily_changes
        WHERE fund_id = '{fund_id}'
        ORDER BY date DESC, ABS(delta) DESC
        LIMIT {n_days * 30}
    """)

def get_holdings_snapshot(fund_id: str, target_date: str) -> pd.DataFrame:
    return query(f"""
        SELECT
            ticker                               AS 代號,
            name                                 AS 名稱,
            ROUND(CAST(weight * 100 AS NUMERIC), 2)               AS 權重,
            shares                               AS 股數
        FROM holdings
        WHERE fund_id = '{fund_id}' AND date = '{target_date}'
        ORDER BY weight DESC
    """)

# ── HTML 表格渲染 ──────────────────────────────────
TABLE_STYLE = """
<style>
.etf-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    font-family: inherit;
}
.etf-table th {
    text-align: left;
    padding: 6px 12px;
    border-bottom: 2px solid #444;
    color: #aaa;
    font-weight: 500;
    white-space: nowrap;
}
.etf-table td {
    padding: 6px 12px;
    border-bottom: 1px solid #2a2a2a;
    white-space: nowrap;
}
.etf-table tr:hover td { background: #1e1e1e; }
.pos { color: #26a641; font-weight: 600; }
.neg { color: #f85149; font-weight: 600; }
</style>
"""

def render_changes_html(display: pd.DataFrame, delta_raw: pd.Series, fund_id: str) -> str:
    is_tw = fund_id in ("00981A", "00992A")
    unit = "張" if is_tw else "股"
    rows = ""
    for i, row in display.iterrows():
        flag = get_flag(row["代號"]) if fund_id == "00988A" else ""
        flag_str = f"{flag} " if flag else ""
        d = delta_raw.iloc[i]
        cls = "pos" if d > 0 else ("neg" if d < 0 else "")
        raw_delta_s = int(row["股數變化"])
        raw_today_s = int(row["今日股數"])
        delta_s = raw_delta_s // 1000 if is_tw else raw_delta_s
        today_s = raw_today_s // 1000 if is_tw else raw_today_s
        rows += (
            f"<tr>"
            f"<td>{row['代號']}</td>"
            f"<td>{flag_str}{row['名稱']}</td>"
            f"<td class='{cls}'>{delta_s:+,}</td>"
            f"<td>{today_s:,}</td>"
            f"<td class='{cls}'>{d:+.2f}%</td>"
            f"<td>{row['今日權重']:.2f}%</td>"
            f"</tr>"
        )
    return (
        TABLE_STYLE
        + "<table class='etf-table'>"
        + "<thead><tr>"
        + f"<th>代號</th><th>名稱</th><th>股數變化({unit})</th>"
        + f"<th>目前股數({unit})</th><th>權重變化</th><th>目前權重</th>"
        + "</tr></thead>"
        + f"<tbody>{rows}</tbody></table>"
    )

def render_snapshot_html(df: pd.DataFrame, fund_id: str) -> str:
    rows = ""
    for _, row in df.iterrows():
        flag = get_flag(row["代號"]) if fund_id == "00988A" else ""
        flag_str = f"{flag} " if flag else ""
        rows += (
            f"<tr>"
            f"<td>{row['代號']}</td>"
            f"<td>{flag_str}{row['名稱']}</td>"
            f"<td>{row['權重']:.2f}%</td>"
            f"<td>{int(row['股數']):,}</td>"
            f"</tr>"
        )
    return (
        TABLE_STYLE
        + "<table class='etf-table'>"
        + "<thead><tr><th>代號</th><th>名稱</th><th>權重</th><th>股數</th></tr></thead>"
        + f"<tbody>{rows}</tbody></table>"
    )

def render_history_html(df: pd.DataFrame, fund_id: str) -> str:
    rows = ""
    for _, row in df.iterrows():
        flag = get_flag(row["代號"]) if fund_id == "00988A" else ""
        flag_str = f"{flag} " if flag else ""
        d = row["權重變化"]
        cls = "pos" if d > 0 else ("neg" if d < 0 else "")
        rows += (
            f"<tr>"
            f"<td>{row['日期']}</td>"
            f"<td>{row['代號']}</td>"
            f"<td>{flag_str}{row['名稱']}</td>"
            f"<td>{row['動作']}</td>"
            f"<td>{row['今日權重']:.2f}%</td>"
            f"<td class='{cls}'>{d:+.2f}%</td>"
            f"<td>{int(row['股數變化']):,}</td>"
            f"</tr>"
        )
    return (
        TABLE_STYLE
        + "<table class='etf-table'>"
        + "<thead><tr>"
        + "<th>日期</th><th>代號</th><th>名稱</th><th>動作</th>"
        + "<th>今日權重</th><th>權重變化</th><th>股數變化</th>"
        + "</tr></thead>"
        + f"<tbody>{rows}</tbody></table>"
    )

# ── 市場資料：收盤價 + 淨值 + 折溢價 ────────────────
# ezmoney fund code（統一投信旗下，00992A 為群益，另行處理）
_EZMONEY_CODE = {"00988A": "61YTW", "00981A": "49YTW"}

@st.cache_data(ttl=1800)
def get_etf_market_data(fund_id: str, date_str: str) -> dict:
    """
    收盤價：FinMind TaiwanStockPrice（指定日期）
    淨值  ：ezmoney 頁面初始 HTML（最新公布值）
    折溢價：兩者相除計算
    回傳 dict，缺資料的欄位不存在，不回傳 None。
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    result = {}
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    kw = {"headers": {"User-Agent": ua}, "timeout": 10, "verify": False}

    # 1. 收盤價：FinMind（往前找最近 7 天取最新交易日，date_str 固定為今日）
    try:
        from datetime import timedelta
        query_start = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        r = requests.get(
            f"https://api.finmindtrade.com/api/v4/data"
            f"?dataset=TaiwanStockPrice&data_id={fund_id}"
            f"&start_date={query_start}&end_date={date_str}",
            **kw,
        )
        if r.ok:
            rows = r.json().get("data", [])
            if rows:
                latest = max(rows, key=lambda x: x["date"])
                result["price"] = float(latest["close"])
    except Exception:
        pass

    # 2. 淨值：ezmoney 初始 HTML（00988A / 00981A）
    fund_code = _EZMONEY_CODE.get(fund_id)
    if fund_code:
        try:
            r2 = requests.get(
                f"https://www.ezmoney.com.tw/ETF/Fund/Info?fundCode={fund_code}",
                **kw,
            )
            if r2.ok:
                r2.encoding = "utf-8"
                pat = (
                    rf'class="time"[^>]*>(\d{{2}}/\d{{2}})</td>'
                    rf'\s+<td[^>]*>.*?fundCode={fund_code}.*?</td>'
                    rf'\s+<td class="num_ETF">([\d.]+)</td>'
                )
                m = re.search(pat, r2.text, re.DOTALL)
                if m:
                    result["nav"] = float(m.group(2))
                    result["nav_date"] = m.group(1)   # e.g. "04/28"
        except Exception:
            pass

    # 2b. 淨值：群益 capitalfund.com.tw（00992A 專用，Angular SSR）
    elif fund_id == "00992A":
        try:
            r3 = requests.get(
                "https://www.capitalfund.com.tw/etf/product/detail/500/basic",
                **kw,
            )
            if r3.ok:
                r3.encoding = "utf-8"
                # 第一個 main-info-item-value 為最新預估淨值
                m_val = re.search(r'class="main-info-item-value">([\d.]+)<', r3.text)
                if m_val:
                    result["nav"] = float(m_val.group(1))
                    # 日期緊接在值後面，格式 2026/04/28
                    m_date = re.search(
                        r'class="main-info-item-value">[\d.]+.*?(\d{4}/\d{2}/\d{2})',
                        r3.text,
                        re.DOTALL,
                    )
                    if m_date:
                        result["nav_date"] = m_date.group(1)[5:]  # "MM/DD"
        except Exception:
            pass

    # 3. 折溢價
    if "price" in result and "nav" in result and result["nav"] > 0:
        result["premium"] = round((result["price"] / result["nav"] - 1) * 100, 2)

    return result


# ── 頁面設定 ──────────────────────────────────────
st.set_page_config(
    page_title="ezMoneySniper",
    page_icon="💰",
    layout="wide",
)

st.title("💰 ezMoneySniper")
st.caption("主動型 ETF 持倉監控系統")

# ── 側欄 ──────────────────────────────────────────
with st.sidebar:
    st.header("🔧 篩選條件")
    fund_id = st.selectbox(
        "選擇基金",
        options=["00981A", "00988A", "00992A"],
        format_func=lambda x: f"{x} {FUND_NAMES[x]}",
    )

    available_dates = get_available_dates(fund_id)
    if not available_dates:
        st.warning("此基金尚無異動資料")
        st.stop()

    selected_date = st.selectbox("選擇日期", options=available_dates)
    st.divider()
    st.caption("資料來源：Supabase" if IS_CLOUD else f"資料庫：{os.getenv('SQLITE_PATH', r'C:\ActiveFundRadar\etf.db')}")

# ── 收盤價 / 淨值 / 折溢價（永遠顯示最新行情，不跟 selected_date）────────
mkt = get_etf_market_data(fund_id, datetime.now().strftime("%Y-%m-%d"))
c1, c2, c3 = st.columns(3)
c1.metric("收盤價", f"NT$ {mkt['price']:.2f}" if "price" in mkt else "－")
if "nav" in mkt:
    nav_label = f"淨值 (NAV)　{mkt.get('nav_date', '')}"
    c2.metric(nav_label, f"NT$ {mkt['nav']:.2f}")
else:
    c2.metric("淨值 (NAV)", "－")
if "premium" in mkt:
    prem = mkt["premium"]
    c3.metric(
        "折溢價",
        f"{prem:+.2f}%",
        delta="溢價" if prem > 0 else ("折價" if prem < 0 else "平價"),
        delta_color="normal" if prem > 0 else ("inverse" if prem < 0 else "off"),
    )
else:
    c3.metric("折溢價", "－")

# ── Tab 佈局 ──────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 當日異動", "🏆 前十大持股", "📋 完整持倉", "📈 歷史紀錄"])

# ════════════════════════════════════════════════
# Tab 1：當日異動
# ════════════════════════════════════════════════
with tab1:
    st.subheader(f"{selected_date}　{fund_id} {FUND_NAMES[fund_id]}　持倉異動")

    df_changes = get_changes(fund_id, selected_date)

    if df_changes.empty:
        st.info("此日期無異動資料")
    else:
        col1, col2, col3, col4 = st.columns(4)
        for action, col, color in [
            ("建倉", col1, "🟢"),
            ("清倉", col2, "🔴"),
            ("加碼", col3, "📈"),
            ("減碼", col4, "📉"),
        ]:
            cnt = len(df_changes[df_changes["動作"] == action])
            col.metric(f"{color} {action}", f"{cnt} 檔")

        st.divider()

        for action in ["建倉", "清倉", "加碼", "減碼"]:
            subset = df_changes[df_changes["動作"] == action].reset_index(drop=True)
            if subset.empty:
                continue

            st.markdown(f"#### {ACTION_COLOR[action]} {action}")
            display = subset.drop(columns=["動作"])
            delta_raw = display["權重變化"].copy()
            st.markdown(
                render_changes_html(display, delta_raw, fund_id),
                unsafe_allow_html=True,
            )

        # 點選個股查歷史
        st.divider()
        st.markdown("#### 🔍 查詢個股歷史異動")
        tickers = df_changes["代號"].tolist()
        names   = df_changes["名稱"].tolist()
        options = [f"{t} {n}" for t, n in zip(tickers, names)]
        chosen  = st.selectbox("選擇個股", options=["— 請選擇 —"] + options)

        if chosen != "— 請選擇 —":
            chosen_ticker = chosen.split(" ")[0]
            hist = get_history(fund_id, chosen_ticker)
            if not hist.empty:
                st.dataframe(hist, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════
# Tab 2：前十大持股
# ════════════════════════════════════════════════
with tab2:
    st.subheader(f"{selected_date}　{fund_id} {FUND_NAMES[fund_id]}　前十大持股")

    snap_date_df2 = query(f"""
        SELECT DISTINCT date FROM holdings
        WHERE fund_id = '{fund_id}' AND date <= '{selected_date}'
        ORDER BY date DESC LIMIT 1
    """)

    if snap_date_df2.empty:
        st.info("此日期前無持倉快照資料")
    else:
        snap_date2 = snap_date_df2.iloc[0]["date"]
        if snap_date2 != selected_date:
            st.caption(f"（holdings 最近資料為 {snap_date2}）")

        df_all = get_holdings_snapshot(fund_id, snap_date2)
        df_top10 = df_all.head(10).reset_index(drop=True)
        top10_weight = df_top10["權重"].sum()
        total_weight = df_all["權重"].sum()
        concentration = (top10_weight / total_weight * 100) if total_weight > 0 else 0

        col_t1, col_t2 = st.columns(2)
        col_t1.metric("前十大權重合計", f"{top10_weight:.2f}%")
        col_t2.metric("佔基金總權重", f"{concentration:.1f}%")

        st.markdown(render_snapshot_html(df_top10, fund_id), unsafe_allow_html=True)

# ════════════════════════════════════════════════
# Tab 3：完整持倉快照
# ════════════════════════════════════════════════
with tab3:
    st.subheader(f"{selected_date}　{fund_id} {FUND_NAMES[fund_id]}　完整持倉")

    snap_date_df = query(f"""
        SELECT DISTINCT date FROM holdings
        WHERE fund_id = '{fund_id}' AND date <= '{selected_date}'
        ORDER BY date DESC LIMIT 1
    """)

    if snap_date_df.empty:
        st.info("此日期前無持倉快照資料")
    else:
        snap_date = snap_date_df.iloc[0]["date"]
        if snap_date != selected_date:
            st.caption(f"（holdings 最近資料為 {snap_date}）")

        df_snap = get_holdings_snapshot(fund_id, snap_date)

        col_s1, col_s2 = st.columns(2)
        col_s1.metric("持股總數", f"{len(df_snap)} 檔")
        col_s2.metric("權重加總", f"{df_snap['權重'].sum():.2f}%")

        st.markdown(
            render_snapshot_html(df_snap, fund_id),
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════
# Tab 4：歷史紀錄
# ════════════════════════════════════════════════
with tab4:
    st.subheader(f"{fund_id} {FUND_NAMES[fund_id]}　歷史異動紀錄")

    col_left, col_right = st.columns([1, 3])

    with col_left:
        action_filter = st.multiselect(
            "動作篩選",
            options=["建倉", "清倉", "加碼", "減碼"],
            default=["建倉", "清倉", "加碼", "減碼"],
        )
        keyword = st.text_input("代號 / 名稱搜尋")

    df_hist = get_all_history(fund_id)

    if not df_hist.empty:
        if action_filter:
            df_hist = df_hist[df_hist["動作"].isin(action_filter)]
        if keyword:
            mask = (
                df_hist["代號"].str.contains(keyword, case=False, na=False) |
                df_hist["名稱"].str.contains(keyword, case=False, na=False)
            )
            df_hist = df_hist[mask]

        df_hist = df_hist.reset_index(drop=True)

        with col_right:
            st.caption(f"共 {len(df_hist)} 筆")

        st.markdown(
            render_history_html(df_hist, fund_id),
            unsafe_allow_html=True,
        )
    else:
        st.info("尚無歷史資料")
