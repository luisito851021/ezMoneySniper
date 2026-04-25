# ezMoneySniper 💰

主動型 ETF 持倉監控網頁介面，提供每日異動查詢、完整持倉快照與歷史紀錄瀏覽。

資料由 [ActiveFundRadar](https://github.com/luisito851021/ActiveFundRadar) 排程寫入，本專案僅負責展示。

## 監控標的

| ETF 代號 | 名稱 |
|---|---|
| 00988A | 統一全球創新 |
| 00981A | 統一台股增長 |
| 00992A | 群益台灣科技創新 |

## 功能

- 查看各基金當日建倉／清倉／加碼／減碼明細
- 完整持倉快照（含前五大持股、權重加總）
- 歷史異動紀錄（可按動作篩選、關鍵字搜尋）
- 個股跨日歷史追蹤

## 安裝與執行

### 1. 安裝套件

```bash
pip install streamlit pandas
```

### 2. 設定環境變數（選填）

預設讀取 `C:\ActiveFundRadar\etf.db`，可透過環境變數覆蓋：

```
SQLITE_PATH=你的_etf.db_路徑
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
   SQLITE_PATH = "/mount/src/..."   # 或連接 Supabase
   ```

## 注意事項

- 本專案不含資料收集邏輯，須先執行 ActiveFundRadar 寫入資料
- 00988A 為全球股票（美、日、韓、德等），顯示國旗標示
- 00981A、00992A 為台灣股票，持股單位為張（1張=1000股）
