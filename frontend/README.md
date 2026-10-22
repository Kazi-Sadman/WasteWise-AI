# WasteWise AI – Streamlit frontend (v2)

```bash
# terminal 1 – backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
# terminal 2 – frontend
cd frontend && pip install -r requirements.txt && streamlit run app.py
```
Open http://localhost:8501. Other backend URL: `WASTEWISE_API_URL=http://host:8000 streamlit run app.py`
or Detect → "Detection settings" → Backend URL. Needs Streamlit >= 1.40.

## Pages
Home · Detect · History (this session) · Model (metrics + limits). Day/Night switch is the toggle in the top bar.

## Files
| File | Job |
|---|---|
| `app.py` | Navbar, theme toggle, the four pages |
| `components.py` | Pure HTML builders (cards, tables, pills, hero) |
| `theme.py` | Colour tokens for dark/light + all CSS. Change `accent` here to re-brand |
| `api_client.py` | Backend calls + readable errors |
| `content.py` | Class icons/colours/tips, loads `../reports/evaluation.json` |
