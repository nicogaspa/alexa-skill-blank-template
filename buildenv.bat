python -m virtualenv --no-site-packages .venv
python -m pip install -U pip
.venv\Scripts\pip install -r requirements/base.txt
.venv\Scripts\pip install -r requirements/skill.txt -t .venv/skill_env
pause
