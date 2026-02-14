#!/bin/bash
echo "🚀 啟動 CDP 儀表板並建立公開連結..."
cd /Users/the_mini_bot/.openclaw/workspace/cdp_visualization/dashboard

# Start streamlit if not running
pgrep -f "streamlit" >/dev/null || nohup streamlit run app.py --server.port 8501 > /tmp/streamlit.log 2>&1 &

# Start ngrok for dashboard
nohup ngrok http 8501 --log=stdout > /tmp/ngrok_dashboard.log 2>&1 &

echo "等待 5 秒鐘..."
sleep 5

# Get URL
URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['tunnels'][-1]['public_url'])" 2>/dev/null)

echo ""
echo "=========================================="
echo "✅ CDP 儀表板公開連結："
echo "$URL"
echo "=========================================="
echo ""
echo "手機或電腦打開上方網址即可預覽！"
