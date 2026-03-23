#!/bin/bash

uvicorn main:app --host 0.0.0.0 --port 10000 &
streamlit run app.py --server.port 10001 --server.address 0.0.0.0