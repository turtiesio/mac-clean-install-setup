.PHONY: format run

format:
	pipx run isort --profile black .
	pipx run black .

run:
	python3 setup-mac.py
