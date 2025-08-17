#!/bin/bash
echo "🚀 재무제표 시각화 애플리케이션 시작 중..."

# 데이터베이스가 없으면 생성
if [ ! -f "corpcode.db" ]; then
    echo "📊 데이터베이스 생성 중..."
    python create_database.py
fi

echo "🌐 Flask 애플리케이션 시작..."
python app.py
