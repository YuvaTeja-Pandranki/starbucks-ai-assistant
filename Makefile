build-StarbucksAIFunction:
	pip install \
		-r requirements-lambda-slim.txt \
		--target "$(ARTIFACTS_DIR)" \
		--platform manylinux2014_x86_64 \
		--implementation cp \
		--python-version 3.11 \
		--only-binary=:all: \
		--upgrade --quiet
	cp -r backend "$(ARTIFACTS_DIR)/"
	cp -r data "$(ARTIFACTS_DIR)/"
	cp lambda_handler.py "$(ARTIFACTS_DIR)/"

vectorstore:
	conda run -n starbucks-ai python scripts/setup_vectorstore.py

run:
	conda run -n starbucks-ai uvicorn backend.main:app --reload --port 8000

slack:
	PYTHONPATH='/Users/yuvatejapandranki/Desktop/starbucks project' conda run -n starbucks-ai python slack_bot/app.py

test:
	conda run -n starbucks-ai pytest tests/ -v

seed:
	conda run -n starbucks-ai python scripts/seed_data.py
