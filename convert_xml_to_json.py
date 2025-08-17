#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 CORPCODE.xml 파일을 JSON으로 변환하는 스크립트
"""
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime

def convert_xml_to_json():
    """CORPCODE.xml 파일을 JSON으로 변환합니다."""
    
    xml_file = 'CORPCODE.xml'
    
    if not os.path.exists(xml_file):
        print(f"❌ {xml_file} 파일을 찾을 수 없습니다.")
        return False
    
    try:
        print(f"📖 XML 파일 파싱 중: {xml_file}")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        print("🔍 XML 구조 분석 중...")
        
        # list 태그 찾기
        items = root.findall('.//list')
        print(f"📊 발견된 회사 수: {len(items)}")
        
        if not items:
            print("❌ list 태그를 찾을 수 없습니다.")
            return False
        
        # JSON 데이터 구조 생성
        json_data = {
            "result": [],
            "list": []
        }
        
        print(f"🔄 {len(items)}개 회사 정보를 JSON으로 변환 중...")
        
        for i, item in enumerate(items):
            if i < 5:  # 처음 5개만 상세 출력
                print(f"   항목 {i+1}: {[f'{child.tag}={child.text}' for child in item]}")
            
            item_data = {}
            for child in item:
                item_data[child.tag] = child.text
            
            json_data["list"].append(item_data)
            
            # 진행상황 표시 (1000개마다)
            if (i + 1) % 1000 == 0:
                print(f"   진행률: {i + 1}/{len(items)} ({((i + 1) / len(items) * 100):.1f}%)")
        
        # JSON 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f'corpcode_{timestamp}.json'
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 변환 완료!")
        print(f"📁 파일명: {json_filename}")
        print(f"📊 총 회사 수: {len(json_data['list'])}")
        
        # 상장회사 수 확인
        listed_companies = [item for item in json_data['list'] if item.get('stock_code', '').strip()]
        print(f"📈 상장회사 수: {len(listed_companies)}")
        
        # 비상장회사 수 확인
        unlisted_companies = [item for item in json_data['list'] if not item.get('stock_code', '').strip()]
        print(f"🏢 비상장회사 수: {len(unlisted_companies)}")
        
        # 샘플 상장회사 출력
        if listed_companies:
            print(f"\n📋 상장회사 샘플 (처음 5개):")
            for i, company in enumerate(listed_companies[:5]):
                print(f"   {i+1}. {company.get('corp_name', 'N/A')} (종목코드: {company.get('stock_code', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ XML 변환 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("XML to JSON 변환기")
    print("=" * 50)
    
    if convert_xml_to_json():
        print("\n🎉 변환이 완료되었습니다!")
        print("이제 create_database.py를 실행하여 데이터베이스를 생성하세요.")
    else:
        print("❌ 변환에 실패했습니다.")



