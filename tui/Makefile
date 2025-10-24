
.PHONY: venv run clean

venv:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
	. .venv/bin/activate && python -m rrtui.app

clean:
	rm -rf .venv __pycache__ .pytest_cache
