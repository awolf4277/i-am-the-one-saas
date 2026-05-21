# Deployment Guide

## Local Backend

cd "X:\i-am-the-one-saas\backend"
.\.venv\Scripts\Activate.ps1
python -m flask --app wsgi:app run --host 127.0.0.1 --port 5000

## Local Frontend

cd "X:\i-am-the-one-saas\frontend"
npm run dev

## Build

cd "X:\i-am-the-one-saas"
npm run build

## Render Backend

Service: i-am-the-one-saas-api  
Start command: python -m gunicorn wsgi:app --bind 0.0.0.0:$PORT  
Health path: /api/health

## Render Frontend

Build command: npm install && npm run build  
Publish directory: dist
