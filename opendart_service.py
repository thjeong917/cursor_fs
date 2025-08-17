#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenDart API 서비스 클래스
재무제표 데이터를 가져오는 기능을 제공합니다.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class OpenDartService:
    def __init__(self, api_key: str = None):
        """
        OpenDart 서비스 초기화
        
        Args:
            api_key (str): OpenDart API 인증키 (40자리)
        """
        self.api_key = api_key or self._load_api_key()
        self.base_url = "https://opendart.fss.or.kr/api"
        
        if not self.api_key:
            raise ValueError("OpenDart API 키가 필요합니다. .env 파일에 API_KEY를 설정해주세요.")
    
    def _load_api_key(self) -> Optional[str]:
        """환경 변수에서 API 키를 로드합니다."""
        # .env 파일에서 로드
        if os.path.exists('.env'):
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('API_KEY='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                print(f"⚠️ .env 파일 로드 중 오류: {e}")
        
        # 환경 변수에서 로드
        return os.getenv('API_KEY')
    
    def get_financial_statement(self, corp_code: str, year: str, report_code: str = "11011") -> Dict:
        """
        단일회사 주요계정 재무제표 데이터를 가져옵니다.
        
        Args:
            corp_code (str): 회사 고유번호 (8자리)
            year (str): 사업연도 (4자리, 2015년 이후)
            report_code (str): 보고서 코드
                - 11013: 1분기보고서
                - 11012: 반기보고서  
                - 11014: 3분기보고서
                - 11011: 사업보고서 (기본값)
        
        Returns:
            Dict: 재무제표 데이터
        """
        url = f"{self.base_url}/fnlttSinglAcnt.json"
        
        params = {
            'crtfc_key': self.api_key,
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': report_code
        }
        
        try:
            print(f"🔍 재무제표 데이터 요청 중...")
            print(f"   회사코드: {corp_code}")
            print(f"   연도: {year}")
            print(f"   보고서: {report_code}")
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == '000':
                    print(f"✅ 재무제표 데이터 로드 성공!")
                    return data
                else:
                    error_msg = data.get('message', '알 수 없는 오류')
                    print(f"❌ API 오류: {error_msg}")
                    return {'error': error_msg}
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                return {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"❌ 요청 중 오류 발생: {e}")
            return {'error': str(e)}
    
    def get_available_years(self) -> List[str]:
        """사용 가능한 연도 목록을 반환합니다 (2015년 이후)."""
        current_year = datetime.now().year
        return [str(year) for year in range(2015, current_year + 1)]
    
    def get_report_types(self) -> Dict[str, str]:
        """보고서 유형과 코드를 반환합니다."""
        return {
            "11013": "1분기보고서",
            "11012": "반기보고서", 
            "11014": "3분기보고서",
            "11011": "사업보고서"
        }
    
    def format_financial_data(self, raw_data: Dict) -> Dict:
        """
        원시 재무제표 데이터를 시각화에 적합한 형태로 포맷팅합니다.
        
        Args:
            raw_data (Dict): OpenDart API에서 받은 원시 데이터
            
        Returns:
            Dict: 포맷팅된 데이터
        """
        if 'error' in raw_data:
            return raw_data
        
        formatted_data = {
            'company_info': {},
            'financial_statements': {
                'balance_sheet': [],      # 재무상태표
                'income_statement': [],   # 손익계산서
                'cash_flow': []          # 현금흐름표
            },
            'summary': {}
        }
        
        try:
            # 회사 정보 추출
            if 'list' in raw_data and raw_data['list']:
                first_item = raw_data['list'][0]
                formatted_data['company_info'] = {
                    'stock_code': first_item.get('stock_code', ''),
                    'report_date': first_item.get('thstrm_dt', ''),
                    'report_type': first_item.get('reprt_code', '')
                }
            
            # 재무제표 데이터 분류
            if 'list' in raw_data:
                for item in raw_data['list']:
                    account_name = item.get('account_nm', '')
                    fs_div = item.get('fs_div', '')  # OFS:재무제표, CFS:연결재무제표
                    sj_div = item.get('sj_div', '')  # BS:재무상태표, IS:손익계산서
                    
                    # 계정과목 데이터
                    account_data = {
                        'account_name': account_name,
                        'fs_type': fs_div,
                        'statement_type': sj_div,
                        'current_amount': self._parse_amount(item.get('thstrm_amount', '0')),
                        'current_accumulated': self._parse_amount(item.get('thstrm_add_amount', '0')),
                        'previous_amount': self._parse_amount(item.get('frmtrm_amount', '0')),
                        'previous_accumulated': self._parse_amount(item.get('frmtrm_add_amount', '0')),
                        'currency': item.get('currency', 'KRW')
                    }
                    
                    # 재무제표 유형별로 분류
                    if sj_div == 'BS':  # 재무상태표
                        formatted_data['financial_statements']['balance_sheet'].append(account_data)
                    elif sj_div == 'IS':  # 손익계산서
                        formatted_data['financial_statements']['income_statement'].append(account_data)
                    else:  # 기타 (현금흐름표 등)
                        formatted_data['financial_statements']['cash_flow'].append(account_data)
            
            # 요약 정보 생성
            formatted_data['summary'] = self._create_summary(formatted_data['financial_statements'])
            
        except Exception as e:
            print(f"⚠️ 데이터 포맷팅 중 오류: {e}")
            formatted_data['error'] = f"데이터 포맷팅 오류: {e}"
        
        return formatted_data
    
    def _parse_amount(self, amount_str: str) -> float:
        """금액 문자열을 숫자로 변환합니다."""
        if not amount_str or amount_str == '':
            return 0.0
        
        try:
            # 쉼표 제거 후 숫자로 변환
            cleaned = amount_str.replace(',', '')
            return float(cleaned)
        except:
            return 0.0
    
    def _create_summary(self, financial_data: Dict) -> Dict:
        """재무제표 요약 정보를 생성합니다."""
        summary = {
            'total_assets': 0,
            'total_liabilities': 0,
            'total_equity': 0,
            'revenue': 0,
            'net_income': 0
        }
        
        try:
            # 재무상태표에서 주요 지표 추출
            for item in financial_data['balance_sheet']:
                account_name = item['account_name']
                current_amount = item['current_amount']
                
                if '자산총계' in account_name or 'Total Assets' in account_name:
                    summary['total_assets'] = current_amount
                elif '부채총계' in account_name or 'Total Liabilities' in account_name:
                    summary['total_liabilities'] = current_amount
                elif '자본총계' in account_name or 'Total Equity' in account_name:
                    summary['total_equity'] = current_amount
            
            # 손익계산서에서 주요 지표 추출
            for item in financial_data['income_statement']:
                account_name = item['account_name']
                current_amount = item['current_amount']
                
                if '매출액' in account_name or 'Revenue' in account_name:
                    summary['revenue'] = current_amount
                elif '당기순손익' in account_name or 'Net Income' in account_name:
                    summary['net_income'] = current_amount
                    
        except Exception as e:
            print(f"⚠️ 요약 정보 생성 중 오류: {e}")
        
        return summary


def test_service():
    """서비스 테스트 함수"""
    try:
        service = OpenDartService()
        print("✅ OpenDart 서비스 초기화 성공!")
        
        # 사용 가능한 연도 확인
        years = service.get_available_years()
        print(f"📅 사용 가능한 연도: {years[-5:]}")  # 최근 5년
        
        # 보고서 유형 확인
        report_types = service.get_report_types()
        print("📋 보고서 유형:")
        for code, name in report_types.items():
            print(f"   {code}: {name}")
            
    except Exception as e:
        print(f"❌ 서비스 초기화 실패: {e}")


if __name__ == "__main__":
    test_service()
