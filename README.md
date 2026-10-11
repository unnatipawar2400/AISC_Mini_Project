# Smart Building Energy Optimizer — Browser App

## Run it
1. Install Python packages: `python -m pip install -r requirements.txt`
2. Run `python main.py` from this folder.
3. Streamlit starts the local app and opens a browser page.
4. Enter room values in the sidebar and click **Analyze room**.
5. Stop it with Ctrl+C in the terminal.

## Files
- `main.py`: launcher; run this file.
- `app.py`: browser dashboard.
- `config.json`: energy-model assumptions and thresholds.
- `energy_scenarios.csv`: created/updated after each analysis.
- `requirements.txt`: required Python packages.

The existing Jupyter notebooks can be kept for showing the AI experiment code, but the dashboard app does not require you to run them.

## Limitations
This is an educational prototype. Estimated energy is calculated from assumed loads and is not a real meter reading. The app provides recommendations only; it does not control physical appliances.
