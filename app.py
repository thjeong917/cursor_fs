#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
재무제표 시각화 웹 애플리케이션
Flask 기반의 메인 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
from opendart_service import OpenDartService
from gemini_service import GeminiService
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 실제 운영시에는 환경변수로 설정

# OpenDart 서비스 초기화
try:
    dart_service = OpenDartService()
    print("✅ OpenDart 서비스 초기화 성공!")
except Exception as e:
    print(f"❌ OpenDart 서비스 초기화 실패: {e}")
    dart_service = None

# Gemini 서비스 초기화
try:
    gemini_service = GeminiService()
    print("✅ Gemini 서비스 초기화 성공!")
except Exception as e:
    print(f"❌ Gemini 서비스 초기화 실패: {e}")
    gemini_service = None

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    conn = sqlite3.connect('corpcode.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/search_company')
def search_company():
    """회사 검색 API"""
    company_name = request.args.get('q', '').strip()
    
    if not company_name:
        return jsonify({'error': '회사명을 입력해주세요.'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 회사명으로 검색 (부분 일치)
        cursor.execute('''
            SELECT corp_name, corp_code, stock_code, corp_eng_name 
            FROM companies 
            WHERE corp_name LIKE ? 
            ORDER BY 
                CASE WHEN corp_name = ? THEN 1 ELSE 0 END DESC,  -- 정확한 일치 우선
                CASE WHEN stock_code != '' THEN 1 ELSE 0 END DESC,  -- 상장회사 우선
                corp_name
            LIMIT 20
        ''', (f'%{company_name}%', company_name))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'corp_name': row['corp_name'],
                'corp_code': row['corp_code'],
                'stock_code': row['stock_code'],
                'corp_eng_name': row['corp_eng_name']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'검색 중 오류가 발생했습니다: {str(e)}'})

@app.route('/api/financial_data')
def get_financial_data():
    """재무제표 데이터 조회 API"""
    corp_code = request.args.get('corp_code')
    year = request.args.get('year')
    report_code = request.args.get('report_code', '11011')
    
    if not all([corp_code, year]):
        return jsonify({'error': '회사코드와 연도를 입력해주세요.'})
    
    if not dart_service:
        return jsonify({'error': 'OpenDart 서비스를 사용할 수 없습니다.'})
    
    try:
        # 재무제표 데이터 가져오기
        raw_data = dart_service.get_financial_statement(corp_code, year, report_code)
        
        if 'error' in raw_data:
            return jsonify({'error': raw_data['error']})
        
        # 데이터 포맷팅
        formatted_data = dart_service.format_financial_data(raw_data)
        
        return jsonify({
            'success': True,
            'data': formatted_data
        })
        
    except Exception as e:
        return jsonify({'error': f'재무제표 데이터 조회 중 오류가 발생했습니다: {str(e)}'})

@app.route('/api/available_years')
def get_available_years():
    """사용 가능한 연도 목록 API"""
    if not dart_service:
        return jsonify({'error': 'OpenDart 서비스를 사용할 수 없습니다.'})
    
    try:
        years = dart_service.get_available_years()
        return jsonify({
            'success': True,
            'years': years
        })
    except Exception as e:
        return jsonify({'error': f'연도 목록 조회 중 오류가 발생했습니다: {str(e)}'})

@app.route('/api/report_types')
def get_report_types():
    """보고서 유형 목록 API"""
    if not dart_service:
        return jsonify({'error': 'OpenDart 서비스를 사용할 수 없습니다.'})
    
    try:
        report_types = dart_service.get_report_types()
        return jsonify({
            'success': True,
            'report_types': report_types
        })
    except Exception as e:
        return jsonify({'error': f'보고서 유형 조회 중 오류가 발생했습니다: {str(e)}'})

@app.route('/company/<corp_code>')
def company_detail(corp_code):
    """회사 상세 페이지"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 회사 정보 조회
        cursor.execute('''
            SELECT corp_name, corp_code, stock_code, corp_eng_name 
            FROM companies 
            WHERE corp_code = ?
        ''', (corp_code,))
        
        company = cursor.fetchone()
        conn.close()
        
        if not company:
            return "회사를 찾을 수 없습니다.", 404
        
        return render_template('company_detail.html', company=company)
        
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500

@app.route('/api/ai_analysis')
def ai_analysis():
    """AI 재무제표 분석 API"""
    corp_code = request.args.get('corp_code', '').strip()
    corp_name = request.args.get('corp_name', '').strip()
    year = request.args.get('year', '').strip()
    report_code = request.args.get('report_code', '11011').strip()
    
    if not corp_code or not corp_name:
        return jsonify({'error': '회사 코드와 회사명이 필요합니다.'})
    
    if not year:
        return jsonify({'error': '분석할 연도를 선택해주세요.'})
    
    if not dart_service:
        return jsonify({'error': 'OpenDart 서비스를 사용할 수 없습니다.'})
    
    if not gemini_service:
        return jsonify({'error': 'AI 분석 서비스를 사용할 수 없습니다. Gemini API 키를 확인해주세요.'})
    
    try:
        print(f"🤖 AI 분석 요청: {corp_name} ({year}년)")
        
        # 재무제표 데이터 가져오기
        raw_data = dart_service.get_financial_statement(corp_code, year, report_code)
        
        if 'error' in raw_data:
            return jsonify({'error': f'재무제표 데이터를 가져올 수 없습니다: {raw_data["error"]}'})
        
        # 데이터 포맷팅
        formatted_data = dart_service.format_financial_data(raw_data)
        
        # AI 분석 실행
        analysis_result = gemini_service.analyze_financial_data(corp_name, formatted_data)
        
        if analysis_result['success']:
            print("✅ AI 분석 완료!")
            return jsonify({
                'success': True,
                'analysis': analysis_result['analysis'],
                'company_name': corp_name,
                'year': year,
                'key_metrics': analysis_result.get('key_metrics', {})
            })
        else:
            return jsonify({'error': analysis_result['error']})
    
    except Exception as e:
        print(f"❌ AI 분석 중 오류 발생: {e}")
        return jsonify({'error': f'AI 분석 중 오류가 발생했습니다: {str(e)}'})

@app.errorhandler(404)
def not_found(error):
    return "페이지를 찾을 수 없습니다.", 404

@app.errorhandler(500)
def internal_error(error):
    return "내부 서버 오류가 발생했습니다.", 500

if __name__ == '__main__':
    print("🚀 재무제표 시각화 웹 애플리케이션을 시작합니다...")
    
    # 데이터베이스 파일 확인 및 생성
    if not os.path.exists('corpcode.db'):
        print("📊 데이터베이스가 없습니다. 생성 중...")
        try:
            import subprocess
            result = subprocess.run(['python', 'create_database.py'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("✅ 데이터베이스 생성 완료!")
            else:
                print(f"❌ 데이터베이스 생성 실패: {result.stderr}")
        except Exception as e:
            print(f"❌ 데이터베이스 생성 중 오류: {e}")
    
    # OpenDart 서비스 상태 확인
    if dart_service:
        print("✅ OpenDart 서비스가 준비되었습니다.")
    else:
        print("⚠️ OpenDart 서비스를 사용할 수 없습니다. API_KEY 환경변수를 설정해주세요.")
    
    # Gemini 서비스 상태 확인
    if gemini_service:
        print("✅ AI 분석 서비스가 준비되었습니다.")
    else:
        print("⚠️ AI 분석 서비스를 사용할 수 없습니다. GEMINI_API_KEY 환경변수를 설정해주세요.")
    
    print("🌐 웹 서버를 시작합니다...")
    
    # 프로덕션 환경에서는 포트를 환경변수에서 가져옴
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
