import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = "gemini-1.5-flash"  # 최신 모델 사용
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
    
    def analyze_financial_data(self, company_name: str, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """재무제표 데이터를 분석하여 AI 리포트 생성"""
        try:
            # 재무데이터에서 주요 지표 추출
            # formatted_data 구조: {'financial_statements': {'balance_sheet': [...], 'income_statement': [...]}}
            financial_statements = financial_data.get('financial_statements', {})
            balance_sheet = financial_statements.get('balance_sheet', [])
            income_statement = financial_statements.get('income_statement', [])
            
            # 주요 계정과목 추출
            key_metrics = self._extract_key_metrics(balance_sheet, income_statement)
            
            # Gemini에게 보낼 프롬프트 생성
            prompt = self._create_analysis_prompt(company_name, key_metrics)
            
            # Gemini API 호출
            response = self._call_gemini_api(prompt)
            
            if response.get('success'):
                return {
                    'success': True,
                    'analysis': response['content'],
                    'company_name': company_name,
                    'key_metrics': key_metrics
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'AI 분석 중 오류가 발생했습니다.')
                }
                
        except Exception as e:
            print(f"❌ AI 분석 중 오류 발생: {e}")
            return {
                'success': False,
                'error': f'AI 분석 처리 중 오류가 발생했습니다: {str(e)}'
            }
    
    def _extract_key_metrics(self, balance_sheet: list, income_statement: list) -> Dict[str, Any]:
        """재무제표에서 주요 지표 추출"""
        metrics = {
            'balance_sheet': {},
            'income_statement': {},
            'ratios': {}
        }
        
        # 재무상태표 주요 항목
        for item in balance_sheet:
            account_name = item.get('account_name', '')
            current_amount = item.get('current_amount', 0)
            previous_amount = item.get('previous_amount', 0)
            
            if '자산총계' in account_name or '자산 총계' in account_name:
                metrics['balance_sheet']['total_assets'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '자본총계' in account_name or '자본 총계' in account_name:
                metrics['balance_sheet']['total_equity'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '부채총계' in account_name or '부채 총계' in account_name:
                metrics['balance_sheet']['total_liabilities'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '유동자산' in account_name:
                metrics['balance_sheet']['current_assets'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '유동부채' in account_name:
                metrics['balance_sheet']['current_liabilities'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
        
        # 손익계산서 주요 항목
        for item in income_statement:
            account_name = item.get('account_name', '')
            current_amount = item.get('current_amount', 0)
            previous_amount = item.get('previous_amount', 0)
            
            if '매출액' in account_name or '수익(매출액)' in account_name:
                metrics['income_statement']['revenue'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '영업이익' in account_name:
                metrics['income_statement']['operating_income'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '당기순이익' in account_name:
                metrics['income_statement']['net_income'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
            elif '매출총이익' in account_name:
                metrics['income_statement']['gross_profit'] = {
                    'current': current_amount,
                    'previous': previous_amount
                }
        
        # 주요 비율 계산
        metrics['ratios'] = self._calculate_ratios(metrics)
        
        return metrics
    
    def _calculate_ratios(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """주요 재무비율 계산"""
        ratios = {}
        
        try:
            bs = metrics['balance_sheet']
            is_data = metrics['income_statement']
            
            # 부채비율 = 부채총계 / 자본총계 * 100
            if 'total_liabilities' in bs and 'total_equity' in bs:
                total_liabilities = bs['total_liabilities']['current']
                total_equity = bs['total_equity']['current']
                if total_equity != 0:
                    ratios['debt_to_equity_ratio'] = round((total_liabilities / total_equity) * 100, 2)
            
            # 자기자본비율 = 자본총계 / 자산총계 * 100
            if 'total_equity' in bs and 'total_assets' in bs:
                total_equity = bs['total_equity']['current']
                total_assets = bs['total_assets']['current']
                if total_assets != 0:
                    ratios['equity_ratio'] = round((total_equity / total_assets) * 100, 2)
            
            # 유동비율 = 유동자산 / 유동부채 * 100
            if 'current_assets' in bs and 'current_liabilities' in bs:
                current_assets = bs['current_assets']['current']
                current_liabilities = bs['current_liabilities']['current']
                if current_liabilities != 0:
                    ratios['current_ratio'] = round((current_assets / current_liabilities) * 100, 2)
            
            # ROE = 당기순이익 / 자본총계 * 100
            if 'net_income' in is_data and 'total_equity' in bs:
                net_income = is_data['net_income']['current']
                total_equity = bs['total_equity']['current']
                if total_equity != 0:
                    ratios['roe'] = round((net_income / total_equity) * 100, 2)
            
            # 매출액증가율
            if 'revenue' in is_data:
                current_revenue = is_data['revenue']['current']
                previous_revenue = is_data['revenue']['previous']
                if previous_revenue != 0:
                    ratios['revenue_growth_rate'] = round(((current_revenue - previous_revenue) / previous_revenue) * 100, 2)
            
        except Exception as e:
            print(f"비율 계산 중 오류: {e}")
        
        return ratios
    
    def _create_analysis_prompt(self, company_name: str, metrics: Dict[str, Any]) -> str:
        """Gemini API용 분석 프롬프트 생성"""
        prompt = f"""
재무제표 분석 전문가로서 {company_name}의 재무제표를 분석해주세요.

주요 재무 데이터:
{json.dumps(metrics, ensure_ascii=False, indent=2)}

다음 관점에서 분석해주세요:
1. 재무 건전성 (부채비율, 자기자본비율, 유동비율)
2. 수익성 (ROE, 매출액 증가율, 영업이익률)
3. 성장성 (전년 대비 주요 지표 변화)
4. 강점과 약점
5. 투자자 관점에서의 평가
6. 주의해야 할 리스크 요인

분석 결과를 다음 형식으로 작성해주세요:
- 전체적인 평가 (한 줄 요약)
- 상세 분석 (각 항목별 3-4줄)
- 투자 의견 및 주의사항

한국어로 작성하고, 전문적이면서도 이해하기 쉽게 설명해주세요.
"""
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Gemini API 호출"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Gemini API 키가 설정되지 않았습니다.'
            }
        
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048
                }
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            print(f"🔍 Gemini API 요청 URL: {url}")
            print(f"🔍 모델: {self.model_name}")
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            print(f"🔍 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    if 'content' in result['candidates'][0]:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        return {
                            'success': True,
                            'content': content
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'AI 응답에 content가 없습니다.'
                        }
                else:
                    print(f"🔍 응답 데이터: {result}")
                    return {
                        'success': False,
                        'error': 'AI 응답에 candidates가 없습니다.'
                    }
            else:
                error_text = response.text
                print(f"❌ API 오류 응답: {error_text}")
                return {
                    'success': False,
                    'error': f'API 요청 실패: {response.status_code} - {error_text}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'AI 분석 요청 시간이 초과되었습니다. (60초)'
            }
        except Exception as e:
            print(f"❌ API 호출 중 예외 발생: {e}")
            return {
                'success': False,
                'error': f'AI 분석 중 오류가 발생했습니다: {str(e)}'
            }
