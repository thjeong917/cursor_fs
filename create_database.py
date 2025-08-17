#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
회사코드 JSON 파일을 SQLite 데이터베이스로 변환하는 스크립트
"""

import json
import sqlite3
import os
from datetime import datetime

def create_database():
    """회사코드 데이터베이스를 생성합니다."""
    
    # JSON 파일 찾기
    json_files = [f for f in os.listdir('.') if f.startswith('corpcode_') and f.endswith('.json')]
    
    if not json_files:
        print("❌ 회사코드 JSON 파일을 찾을 수 없습니다.")
        return False
    
    # 가장 최근 파일 선택
    latest_file = max(json_files)
    print(f"📁 사용할 파일: {latest_file}")
    
    # JSON 파일 로드
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ JSON 파일 로드 실패: {e}")
        return False
    
    # 데이터베이스 생성
    conn = sqlite3.connect('corpcode.db')
    cursor = conn.cursor()
    
    # 회사코드 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corp_code TEXT UNIQUE NOT NULL,
            corp_name TEXT NOT NULL,
            corp_eng_name TEXT,
            stock_code TEXT,
            modify_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 인덱스 생성 (검색 성능 향상)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_corp_name ON companies(corp_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_code ON companies(stock_code)')
    
    # 데이터 삽입
    companies = data.get('list', [])
    print(f"📊 총 {len(companies)}개 회사 정보를 데이터베이스에 저장합니다...")
    
    success_count = 0
    for company in companies:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO companies 
                (corp_code, corp_name, corp_eng_name, stock_code, modify_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                company.get('corp_code', ''),
                company.get('corp_name', ''),
                company.get('corp_eng_name', ''),
                company.get('stock_code', '').strip(),
                company.get('modify_date', '')
            ))
            success_count += 1
        except Exception as e:
            print(f"⚠️ 회사 정보 저장 실패: {company.get('corp_name', 'Unknown')} - {e}")
    
    # 변경사항 저장
    conn.commit()
    
    # 통계 출력
    cursor.execute('SELECT COUNT(*) FROM companies')
    total_count = cursor.fetchone()[0]
    
    print(f"✅ 데이터베이스 생성 완료!")
    print(f"📊 총 회사 수: {total_count}")
    print(f"📁 데이터베이스 파일: corpcode.db")
    
    # 샘플 데이터 확인
    cursor.execute('SELECT corp_name, corp_code, stock_code FROM companies WHERE stock_code != "" LIMIT 5')
    sample_data = cursor.fetchall()
    
    print(f"\n📋 상장회사 샘플:")
    for company in sample_data:
        print(f"   - {company[0]} (코드: {company[1]}, 종목코드: {company[2]})")
    
    conn.close()
    return True

def search_company(company_name):
    """회사명으로 회사를 검색합니다."""
    conn = sqlite3.connect('corpcode.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT corp_name, corp_code, stock_code, corp_eng_name 
        FROM companies 
        WHERE corp_name LIKE ? 
        ORDER BY corp_name
        LIMIT 10
    ''', (f'%{company_name}%',))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

if __name__ == "__main__":
    print("회사코드 데이터베이스 생성기")
    print("=" * 50)
    
    if create_database():
        print("\n🎉 데이터베이스 생성이 완료되었습니다!")
        
        # 테스트 검색
        test_company = "삼성"
        print(f"\n🔍 테스트 검색: '{test_company}'")
        results = search_company(test_company)
        
        if results:
            print(f"검색 결과 ({len(results)}개):")
            for company in results:
                print(f"   - {company[0]} (코드: {company[1]}, 종목코드: {company[2]})")
        else:
            print("검색 결과가 없습니다.")
    else:
        print("❌ 데이터베이스 생성에 실패했습니다.")
