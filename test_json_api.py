import requests
import json

def test_json_api():
    """OpenDart API에서 JSON 형식으로 직접 다운로드 테스트"""
    
    # .env 파일에서 API 키 읽기
    api_key = ""
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('API_KEY='):
                    api_key = line.split('=')[1].strip()
                    break
    except:
        print("❌ .env 파일을 읽을 수 없습니다.")
        return
    
    if not api_key:
        print("❌ API 키를 찾을 수 없습니다.")
        return
    
    print(f"✅ API 키 로드: {api_key[:8]}...")
    
    # 다양한 방법으로 JSON 요청 시도
    base_url = "https://opendart.fss.or.kr/api/corpCode"
    
    test_urls = [
        f"{base_url}.json?crtfc_key={api_key}",
        f"{base_url}.xml?crtfc_key={api_key}&format=json",
        f"{base_url}.xml?crtfc_key={api_key}&output=json",
        f"{base_url}.xml?crtfc_key={api_key}&type=json"
    ]
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 테스트 {i}: {url}")
        try:
            response = requests.get(url, headers=headers)
            print(f"   상태 코드: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                try:
                    # JSON 응답인지 확인
                    json_data = response.json()
                    print(f"   ✅ JSON 응답 성공!")
                    print(f"   데이터 크기: {len(str(json_data))} 문자")
                    if isinstance(json_data, dict) and 'list' in json_data:
                        print(f"   회사 수: {len(json_data['list'])}")
                except:
                    print(f"   ❌ JSON이 아닙니다. 응답 크기: {len(response.content)} 바이트")
            else:
                print(f"   ❌ 요청 실패")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")

if __name__ == "__main__":
    test_json_api()
