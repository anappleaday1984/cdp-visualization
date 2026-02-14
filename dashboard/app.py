#!/usr/bin/env python3
import streamlit as st
import json, os
st.set_page_config(page_title="CDP", layout="wide")
st.title("📊 CDP Digital Twin")

# Load data
data = []
with open("/Users/the_mini_bot/.openclaw/workspace/digital_twin/monitoring/data/behavior_twin_monthly.jsonl") as f:
    for line in f:
        data.append(json.loads(line))

if data:
    latest = data[-1]
    brand = latest.get('brand_distribution', {})
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("7-Eleven", f"{brand.get('7-11', 0)*100:.1f}%")
    c2.metric("全家", f"{brand.get('FamilyMart', 0)*100:.1f}%")
    c3.metric("滿意度", f"{latest.get('avg_satisfaction', 0)*100:.0f}%")
    c4.metric("數位採用", f"{latest.get('digital_adoption_rate', 0)*100:.1f}%")
    
    st.bar_chart({"7-Eleven": [brand.get('7-11', 0)*100], "全家": [brand.get('FamilyMart', 0)*100]})
    st.success(f"✅ Loaded {len(data)} records")
