vectorstore:
	conda run -n starbucks-ai python scripts/setup_vectorstore.py

run:
	conda run -n starbucks-ai uvicorn backend.main:app --reload --port 8000

slack:
	conda run -n starbucks-ai python slack_bot/app.py

test:
	conda run -n starbucks-ai pytest tests/ -v

seed:
	conda run -n starbucks-ai python scripts/seed_data.py
