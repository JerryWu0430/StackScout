#!/bin/bash

# Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload &

# Start frontend
cd ../frontend
npm run dev
