# OpenDart 회사코드 다운로더

OpenDart API를 사용하여 회사코드 파일을 다운로드하는 Python 프로그램입니다.

## 기능

- OpenDart API를 통한 회사코드 파일 다운로드
- ZIP 파일 형태로 회사코드 저장
- 에러 코드별 상세 설명 제공
- 파일명에 날짜 자동 추가

## 설치 및 실행

### 1. Python 설치 확인
Python 3.6 이상이 설치되어 있어야 합니다.

### 2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 프로그램 실행
```bash
python opendart_downloader.py
```

## 사용 방법

1. 프로그램을 실행하면 OpenDart API 키를 입력하라는 메시지가 나타납니다.
2. 40자리 API 키를 입력하고 Enter를 누릅니다.
3. 자동으로 회사코드 파일이 다운로드됩니다.
4. 다운로드된 파일은 `corpCode_YYYYMMDD.zip` 형태로 저장됩니다.

## API 정보

- **요청 URL**: `https://opendart.fss.or.kr/api/corpCode.xml`
- **메서드**: GET
- **필수 파라미터**: `crtfc_key` (API 인증키)
- **출력 형식**: ZIP 파일 (binary)

## 에러 코드

- `000`: 정상
- `010`: 등록되지 않은 키
- `011`: 사용할 수 없는 키
- `012`: 접근할 수 없는 IP
- `013`: 조회된 데이터 없음
- `014`: 파일이 존재하지 않음
- `020`: 요청 제한 초과
- `021`: 조회 가능한 회사 개수 초과
- `800`: 시스템 점검 중
- `900`: 정의되지 않은 오류
- `901`: 개인정보 보유기간 만료

## 주의사항

⚠️ **중요**: 
- API 키는 민감한 정보이므로 안전하게 보관하세요
- Chrome이나 Edge에서는 파일 확장자를 .zip으로 변경해야 할 수 있습니다
- 다운로드된 ZIP 파일에는 회사코드 정보가 XML 형태로 포함되어 있습니다

## 파일 구조

```
├── opendart_downloader.py    # 메인 프로그램
├── requirements.txt          # 필요한 패키지 목록
└── README.md                # 사용법 설명
```
