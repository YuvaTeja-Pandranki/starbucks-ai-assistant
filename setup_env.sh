#!/bin/bash
conda activate starbucks-ai
pip install -r requirements.txt
python -m spacy download en_core_web_sm
