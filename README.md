# 📈 Stock Alert Engine

This project provides a modular Python framework for generating and managing stock alerts based on custom conditions and market data.

It includes a flexible alert engine, ticker data models, condition evaluators, and integration utilities for caching and databases.

### Create and activate a virtual environment

```sh
python -m venv venv
source venv/bin/activate      # On macOS/Linux
venv\Scripts\activate         # On Windows
```

### Install dependencies

```sh
pip install -r requirements.txt
```

### Run Alert background process

- Check [ALERT_README.md](ALERT_README.md) for More

```sh
python alerts_test.py
```

### Run the api project

```sh
uvicorn main:app --reload --port 8000
```
