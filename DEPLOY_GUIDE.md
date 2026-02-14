# CDP 儀表板部署指南 - Streamlit Cloud

## 🚀 部署步驟

### 步驟 1：初始化 Git 倉庫

```bash
cd /Users/the_mini_bot/.openclaw/workspace/cdp_visualization

# 初始化
git init
git add .
git commit -m "feat: CDP Digital Twin Dashboard initial commit"
```

### 步驟 2：推送到 GitHub

1. 創建新倉庫：https://github.com/new
   - 名稱：`cdp-visualization`
   - 公開（Public）
   - 不要勾選 README

2. 推送代碼：

```bash
git remote add origin https://github.com/YOUR_USERNAME/cdp-visualization.git
git branch -M main
git push -u origin main
```

### 步驟 3：部署到 Streamlit Cloud

1. 打開 https://share.streamlit.io
2. 用 GitHub 登入
3. 點 "Connect your GitHub repository"
4. 選擇 `YOUR_USERNAME/cdp-visualization`
5. 設定：
   - Main file path: `streamlit_app.py`
   - Python version: 3.9
6. 點 "Deploy!"

### 步驟 4：取得公開網址

部署完成後會得到類似：
```
https://cdp-visualization.streamlit.app
```

這個網址可以在任何網路下用手機訪問！

## 📱 手機訪問

部署成功後，用手機瀏覽器打開：
```
https://你的用户名.streamlit.app
```

## 🔧 修改後更新

代碼更新後，只需：

```bash
git add .
git commit -m "feat: 更新說明"
git push
```

Streamlit Cloud 會自動重新部署。

## 📁 文件結構

```
cdp_visualization/
├── streamlit_app.py      # 主程式（部署入口）
├── requirements.txt       # 依賴列表
├── README.md            # 說明文件
├── api/                 # FastAPI 後端
├── dashboard/           # 備用儀表板
└── monitoring/          # 監控模組
```

## ⚠️ 注意事項

1. **Streamlit Cloud 限制**：
   - 最多 1GB RAM
   - 公有倉庫免費
   - 每月有限流量

2. **數據文件**：
   - 演示模式會自動生成假數據
   - 生產環境需要連接真實數據源

## 🎯 面試展示提示

展示時強調：
- ✅ 即時 What-If 模擬
- ✅ 多維度分析（群體/區域/時間）
- ✅ 商業洞察自動生成
- ✅ 雲端部署，可隨時訪問

## ❓ 問題排除

**Q: 部署失敗？**
A: 檢查 `requirements.txt` 是否正確

**Q: 數據不顯示？**
A: 演示模式會使用假數據，確保文件路徑正確

**Q: 如何修改數據源？**
A: 修改 `DATA_DIR` 指向你的 JSONL 文件位置

---

如有問題，請提問！
