# ezMoneySniper — 專案說明

## 專案概述
主動型 ETF 持倉監控網頁介面。**本專案只負責展示**，資料由 ActiveFundRadar 排程寫入 Supabase / SQLite。
部署於 Streamlit Community Cloud，支援手機瀏覽。

## 監控標的
| ETF 代號 | 名稱 | 備註 |
|----------|------|------|
| 00981A | 統一台股增長 | 台灣上市，持股單位張（1張=1000股） |
| 00988A | 統一全球創新 | 全球股票（美、日、韓、德），代號後綴顯示國旗 |
| 00992A | 群益台灣科技創新 | 台灣上市，持股單位張 |

## 唯一檔案
`app.py`：全部邏輯集中在一個檔案，包含 DB 連線、資料查詢、HTML 渲染、頁面佈局。

## Tab 佈局順序
1. **📊 當日異動** — 建倉／清倉／加碼／減碼明細，含個股跨日歷史查詢
2. **🏆 前十大持股** — 當日持倉前 10 名
3. **📋 完整持倉** — 全部持倉快照（含持股總數、權重加總）
4. **📈 歷史紀錄** — 跨日異動紀錄，支援動作篩選與關鍵字搜尋

## 側欄下拉選單順序
`00981A → 00988A → 00992A`（進入頁面預設顯示 00981A）

## DB 連線邏輯
透過環境變數 `IS_CLOUD` 切換：
- `IS_CLOUD=true`：連 Supabase（`SUPABASE_URL`），Streamlit Cloud 使用
- 未設定或 `false`：讀本機 SQLite（`SQLITE_PATH`，預設 `C:\ActiveFundRadar\etf.db`）

## 環境變數
```
IS_CLOUD=true                  # Streamlit Cloud Secrets 設定
SUPABASE_URL=postgresql://...  # Supabase 連線字串
SQLITE_PATH=C:\ActiveFundRadar\etf.db  # 本機覆蓋用（選填）
```

## SQL 相容性注意
Supabase（PostgreSQL）與 SQLite 的 `ROUND()` 型別轉換不同，查詢中統一用：
```sql
ROUND(CAST(weight * 100 AS NUMERIC), 2)
```
勿改回 SQLite 語法 `ROUND(weight * 100, 2)`，否則 Supabase 端會出錯。

## 開發原則
- 修改要**最小化**：只改必要的地方
- 本機驗證後再推送（Streamlit Cloud 會自動重新部署）
- 所有權重在 DB 存小數（0.05），顯示時乘以 100（已在 SQL 層處理）
- 繁體中文回應

## 常用指令
```bash
# 本機啟動
python -m streamlit run app.py

# 推送（觸發 Streamlit Cloud 自動重部署）
git add app.py && git commit -m "..." && git push
```
