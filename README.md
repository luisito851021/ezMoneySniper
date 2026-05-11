# ezMoneySniper 💰

主動型 ETF 持倉監控網頁介面，提供每日異動查詢、持倉快照（含即時漲幅）與歷史紀錄瀏覽。

資料由 [ActiveFundRadar](https://github.com/luisito851021/ActiveFundRadar) 排程寫入，本專案僅負責展示。

🔗 **線上體驗：[ezmoneysniper.streamlit.app](https://ezmoneysniper.streamlit.app/)**

## 監控標的

| ETF 代號 | 名稱 | 市場 | 單位 |
|---|---|---|---|
| 00981A | 統一台股增長 | 台灣 | 張 |
| 00988A | 統一全球創新 | 全球（美、日、韓、德等） | 股 |
| 00403A | 統一台股升級50 | 台灣 | 張 |
| 00992A | 群益台灣科技創新 | 台灣 | 張 |

## 功能

- **當日異動**：建倉／清倉／加碼／減碼明細，支援個股跨日歷史追蹤
- **前十大持股**：即時漲幅%、集中度分析
- **完整持倉快照**：所有持股含即時漲幅%（台股基金）
- **歷史紀錄**：可按動作篩選、關鍵字搜尋
- **收盤價 / 淨值 / 折溢價**：每頁即時顯示基金行情

> 漲幅資料來源：TWSE 即時 API（mis.twse.com.tw），盤中即時更新，cache 5 分鐘

## 安裝與執行

### 1. 安裝套件

```bash
pip install streamlit pandas sqlalchemy psycopg2-binary python-dotenv
```

### 2. 設定環境變數

預設讀取 `C:\ActiveFundRadar\etf.db`，可透過 `.env` 覆蓋：

```
SQLITE_PATH=你的_etf.db_路徑
SUPABASE_URL=postgresql://...   # 雲端部署使用
IS_CLOUD=true                   # Streamlit Cloud 設定
```

### 3. 啟動

```bash
python -m streamlit run app.py
```

## Streamlit Community Cloud 部署

1. 將此專案推送至 GitHub
2. 至 [share.streamlit.io](https://share.streamlit.io) 部署
3. 在 Secrets 設定中加入：
   ```toml
   IS_CLOUD = "true"
   SUPABASE_URL = "postgresql://..."
   ```

## 注意事項

- 本專案不含資料收集邏輯，須先執行 ActiveFundRadar 寫入資料
- 00988A 為全球股票，持倉顯示國旗標示，漲幅欄不顯示（跨交易所）
- 台股基金（00981A、00403A、00992A）持股單位為張（1張＝1000股）
