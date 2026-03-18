# Janet Job MVP (Part 1)

## Setup
1) Create `.env` from `.env.example`
2) Install deps:
   - `pip install -r requirements.txt`

## Run headless (recommended first)
`python run_cli.py --resume inputs/resume.txt --jd inputs/jd.txt`

## Run UI
`streamlit run app.py`

## Outputs
Artifacts and prompts are saved to: `runs/<run_id>/`