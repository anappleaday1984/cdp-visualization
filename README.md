# CDP Digital Twin Dashboard

Interactive dashboard for CDP (Customer Data Platform) behavior analysis and what-if simulation.

## Features

- 📊 **Brand Preference Analysis**: Compare 7-Eleven vs FamilyMart preferences
- 👥 **Persona Comparison**: Fresh_Grad vs FinTech_Family behavior patterns
- 📍 **Region Comparison**: Taipei vs Tainan consumption trends
- 🔮 **What-If Simulation**: Predict outcomes based on:
  - Point multipliers
  - Electricity price adjustments
  - Promotion intensity

## Live Demo

Deploy on Streamlit Cloud: https://share.streamlit.io/

## Quick Start

### Local

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/cdp-visualization.git
cd cdp-visualization

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run streamlit_app.py
```

### Streamlit Cloud

1. Push this repository to GitHub
2. Visit https://share.streamlit.io
3. Connect your GitHub repository
4. Deploy!

## Data Source

- `digital_twin/monitoring/data/behavior_twin_monthly.jsonl`
- Real-time behavior simulation data

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Data**: JSONL files
- **Deployment**: Streamlit Cloud

## License

MIT
