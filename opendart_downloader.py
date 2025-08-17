#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenDart 회사코드 다운로더 (JSON 버전)
OpenDart API를 사용하여 회사코드 파일을 다운로드하고 JSON으로 변환하는 프로그램
"""

import requests
import os
import zipfile
import json
import shutil
from datetime import datetime

class OpenDartDownloader:
    def __init__(self, api_key):
        """
        OpenDart 다운로더 초기화
        
        Args:
            api_key (str): OpenDart API 인증키 (40자리)
        """
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api/corpCode.xml"
        
    def download_corp_code(self):
        """
        회사코드 파일을 다운로드하고 JSON으로 변환합니다
        
        Returns:
            bool: 다운로드 및 변환 성공 여부
        """
        try:
            print("=== OpenDart 회사코드 다운로드 시작 ===")
            print(f"API URL: {self.base_url}")
            print(f"API 키: {self.api_key[:8]}...")
            
            # API 요청 파라미터
            params = {
                'crtfc_key': self.api_key
            }
            
            # GET 요청 보내기
            print("API 요청 중...")
            response = requests.get(self.base_url, params=params, stream=True)
            
            # 응답 상태 확인
            if response.status_code == 200:
                # 파일명 결정
                filename = self._get_filename(response)
                
                # 파일 저장
                print(f"파일 다운로드 중: {filename}")
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 파일 정보 출력
                file_size = os.path.getsize(filename)
                print(f"✅ 다운로드 완료!")
                print(f"📁 파일명: {filename}")
                print(f"📊 파일 크기: {file_size / 1024:.2f} KB")
                print(f"⏰ 다운로드 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # ZIP 파일 압축 해제 및 JSON 변환
                print("\n📦 ZIP 파일 압축 해제 중...")
                if self._extract_and_convert_to_json(filename):
                    print("✅ JSON 변환 완료!")
                    return True
                else:
                    print("❌ JSON 변환 실패!")
                    return False
                
            else:
                print(f"❌ 다운로드 실패. 상태 코드: {response.status_code}")
                self._handle_error_response(response)
                return False
                
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return False
    
    def _get_filename(self, response):
        """
        응답에서 파일명을 추출하거나 기본 파일명을 생성합니다
        
        Args:
            response: requests 응답 객체
            
        Returns:
            str: 파일명
        """
        # Content-Disposition 헤더에서 파일명 추출 시도
        content_disposition = response.headers.get('content-disposition', '')
        
        if 'filename=' in content_disposition:
            # filename="corpCode.zip" 형태에서 추출
            import re
            match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if match:
                return match.group(1)
        
        # 기본 파일명 생성 (현재 날짜 포함)
        current_date = datetime.now().strftime('%Y%m%d')
        return f"corpCode_{current_date}.zip"
    
    def _extract_and_convert_to_json(self, zip_filename):
        """
        ZIP 파일을 압축 해제하고 XML을 JSON으로 변환합니다
        
        Args:
            zip_filename (str): ZIP 파일명
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 압축 해제할 폴더명
            extract_dir = "corpcode_temp"
            
            # 기존 임시 폴더가 있다면 삭제
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
                print(f"🗑️ 기존 임시 폴더 삭제: {extract_dir}")
            
            # ZIP 파일 압축 해제
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"📁 압축 해제 완료: {extract_dir}")
            
            # XML 파일 찾기
            xml_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.xml'):
                        xml_files.append(os.path.join(root, file))
            
            if not xml_files:
                print("❌ XML 파일을 찾을 수 없습니다.")
                return False
            
            # 첫 번째 XML 파일을 JSON으로 변환
            xml_file = xml_files[0]
            print(f"📄 XML 파일 발견: {os.path.basename(xml_file)}")
            
            # XML을 JSON으로 변환
            json_data = self._xml_to_json(xml_file)
            
            if json_data:
                # JSON 파일로 저장
                json_filename = f"corpcode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 JSON 파일 저장 완료: {json_filename}")
                print(f"📊 총 회사 수: {len(json_data.get('list', []))}")
                
                # 임시 폴더 정리
                self._cleanup_temp_files(extract_dir, zip_filename)
                
                return True
            else:
                print("❌ XML을 JSON으로 변환하는데 실패했습니다.")
                return False
                
        except Exception as e:
            print(f"❌ 압축 해제 및 변환 중 오류 발생: {str(e)}")
            return False
    
    def _xml_to_json(self, xml_file):
        """
        XML 파일을 JSON으로 변환합니다
        
        Args:
            xml_file (str): XML 파일 경로
            
        Returns:
            dict: JSON 데이터
        """
        try:
            import xml.etree.ElementTree as ET
            
            # XML 파싱
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            print(f"🔍 XML 루트 태그: {root.tag}")
            
            # JSON 구조 생성
            json_data = {
                "result": {},
                "list": []
            }
            
            # 모든 자식 태그 확인
            print(f"📋 루트의 자식 태그들: {[child.tag for child in root]}")
            
            # result 태그 처리
            result_elem = root.find('result')
            if result_elem is not None:
                print(f"✅ result 태그 발견")
                for child in result_elem:
                    json_data["result"][child.tag] = child.text
                    print(f"   - {child.tag}: {child.text}")
            else:
                print(f"⚠️ result 태그를 찾을 수 없습니다")
            
            # list 태그 처리 - 수정된 로직
            list_elem = root.find('list')
            if list_elem is not None:
                print(f"✅ list 태그 발견")
                
                # list 태그 안의 개별 항목들을 찾기
                items = list_elem.findall('list')
                print(f"📊 발견된 항목 수: {len(items)}")
                
                if items:
                    # 첫 번째 항목의 구조 확인
                    first_item = items[0]
                    print(f"🔍 첫 번째 항목의 태그들: {[child.tag for child in first_item]}")
                    
                    for i, item in enumerate(items):
                        if i < 5:  # 처음 5개만 상세 출력
                            print(f"   항목 {i+1}: {[f'{child.tag}={child.text}' for child in item]}")
                        
                        item_data = {}
                        for child in item:
                            item_data[child.tag] = child.text
                        json_data["list"].append(item_data)
                        
                        # 모든 데이터 처리 (제한 제거)
                else:
                    print(f"⚠️ list 태그 안에 항목이 없습니다")
                    
                    # 다른 구조일 수 있으니 직접 찾아보기
                    all_items = root.findall('.//list')
                    print(f"🔍 전체에서 찾은 list 태그 수: {len(all_items)}")
                    
                    if all_items:
                        for i, item in enumerate(all_items):
                            if i < 5:  # 처음 5개만 상세 출력
                                print(f"   항목 {i+1}: {[f'{child.tag}={child.text}' for child in item]}")
                            
                            item_data = {}
                            for child in item:
                                item_data[child.tag] = child.text
                            json_data["list"].append(item_data)
                            
                            # 모든 데이터 처리 (제한 제거)
            else:
                print(f"⚠️ list 태그를 찾을 수 없습니다")
                
                # 다른 구조일 수 있으니 직접 찾아보기
                all_items = root.findall('.//list')
                print(f"🔍 전체에서 찾은 list 태그 수: {len(all_items)}")
                
                if all_items:
                    for i, item in enumerate(all_items):
                        if i < 5:  # 처음 5개만 상세 출력
                            print(f"   항목 {i+1}: {[f'{child.tag}={child.text}' for child in item]}")
                        
                        item_data = {}
                        for child in item:
                            item_data[child.tag] = child.text
                        json_data["list"].append(item_data)
                        
                        # 모든 데이터 처리 (제한 제거)
            
            print(f"📊 최종 JSON 데이터 구조:")
            print(f"   - result: {len(json_data['result'])} 항목")
            print(f"   - list: {len(json_data['list'])} 항목")
            
            return json_data
            
        except Exception as e:
            print(f"❌ XML 파싱 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _cleanup_temp_files(self, extract_dir, zip_filename):
        """
        임시 파일들을 정리합니다
        
        Args:
            extract_dir (str): 압축 해제된 폴더
            zip_filename (str): ZIP 파일명
        """
        try:
            # 임시 폴더 삭제
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
                print(f"🗑️ 임시 폴더 삭제: {extract_dir}")
            
            # ZIP 파일 삭제
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
                print(f"🗑️ ZIP 파일 삭제: {zip_filename}")
            
            print("🧹 임시 파일 정리 완료!")
            
        except Exception as e:
            print(f"⚠️ 임시 파일 정리 중 오류: {str(e)}")
    
    def _handle_error_response(self, response):
        """
        에러 응답을 처리하고 메시지를 출력합니다
        
        Args:
            response: requests 응답 객체
        """
        try:
            # JSON 응답인 경우 파싱 시도
            error_data = response.json()
            if 'status' in error_data:
                status = error_data['status']
                message = error_data.get('message', '알 수 없는 오류')
                print(f"에러 코드: {status}")
                print(f"에러 메시지: {message}")
                
                # 에러 코드별 상세 설명
                self._print_error_details(status)
            else:
                print(f"응답 내용: {response.text}")
                
        except:
            # JSON 파싱 실패 시 텍스트 출력
            print(f"응답 내용: {response.text}")
    
    def _print_error_details(self, status):
        """
        에러 코드별 상세 설명을 출력합니다
        
        Args:
            status (str): 에러 코드
        """
        error_messages = {
            '000': '정상',
            '010': '등록되지 않은 키입니다.',
            '011': '사용할 수 없는 키입니다. 오픈API에 등록되었으나, 일시적으로 사용 중지된 키를 통하여 검색하는 경우 발생합니다.',
            '012': '접근할 수 없는 IP입니다.',
            '013': '조회된 데이타가 없습니다.',
            '014': '파일이 존재하지 않습니다.',
            '020': '요청 제한을 초과하였습니다. (일반적으로 20,000건 이상의 요청)',
            '021': '조회 가능한 회사 개수가 초과하였습니다. (최대 100건)',
            '100': '필드의 부적절한 값입니다. 필드 설명에 없는 값을 사용한 경우에 발생하는 메시지입니다.',
            '101': '부적절한 접근입니다.',
            '800': '시스템 점검으로 인한 서비스가 중지 중입니다.',
            '900': '정의되지 않은 오류가 발생하였습니다.',
            '901': '사용자 계정의 개인정보 보유기간이 만료되어 사용할 수 없는 키입니다. 관리자 이메일(opendart@fss.or.kr)로 문의하시기 바랍니다.'
        }
        
        if status in error_messages:
            print(f"📋 상세 설명: {error_messages[status]}")
        else:
            print(f"📋 알 수 없는 에러 코드: {status}")


def load_env_file():
    """
    .env 파일에서 환경 변수를 로드합니다
    
    Returns:
        dict: 환경 변수 딕셔너리
    """
    env_vars = {}
    
    try:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            print("✅ .env 파일을 성공적으로 로드했습니다.")
        else:
            print("❌ .env 파일을 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ .env 파일 로드 중 오류 발생: {e}")
    
    return env_vars


def main():
    """메인 함수"""
    print("OpenDart 회사코드 다운로더 (JSON 버전)")
    print("=" * 60)
    
    # .env 파일에서 API 키 로드
    env_vars = load_env_file()
    api_key = env_vars.get('API_KEY', '').strip()
    
    if not api_key:
        print("❌ .env 파일에서 API_KEY를 찾을 수 없습니다.")
        print("📝 .env 파일에 API_KEY=your_api_key_here 형태로 설정해주세요.")
        return
    
    if len(api_key) != 40:
        print(f"❌ API 키 길이가 올바르지 않습니다. (현재: {len(api_key)}자, 필요: 40자)")
        return
    
    print(f"✅ API 키를 .env 파일에서 로드했습니다: {api_key[:8]}...")
    
    # 다운로더 생성 및 실행
    downloader = OpenDartDownloader(api_key)
    success = downloader.download_corp_code()
    
    if success:
        print("\n🎉 회사코드 JSON 변환이 완료되었습니다!")
        print("📁 현재 디렉토리에 JSON 파일이 저장되었습니다.")
        print("🧹 임시 파일들은 자동으로 정리되었습니다.")
    else:
        print("\n❌ 회사코드 다운로드 및 변환에 실패했습니다.")
        print("🔍 위의 오류 메시지를 확인해주세요.")


if __name__ == "__main__":
    main()
