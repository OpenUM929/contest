# 문화공공데이터광장 이미지 URL 반환 API 후보 보고서

## 1. 진행 상황 요약

### 완료한 작업
- 문화공공데이터광장(culture.go.kr) API 상세 페이지에서 이미지 관련 출력 필드를 파싱하여 7개 API 확인
- 각 API의 엔드포인트, 이미지 필드명, 설명을 문서로 추출
- 실제 API 호출 테스트를 시도했으나, 6개 API는 401 Unauthorized, 1개(API_CCA_169)는 200 OK를 반환하나 이미지가 아닌 웹페이지 URL만 포함
- 프로젝트 .env 파일의 KCISA_API_KEY가 비어있으며, 재발급이 필요한 상태로 확인

### 테스트 결과
| API 코드 | 엔드포인트 | 상태 | 비고 |
|---------|-----------|------|------|
| API_CCA_169 | https://api.kcisa.kr/openapi/API_CCA_169/request | 200 OK | URL 필드가 웹페이지 링크(이미지 아님) |
| API_CNV_048 | https://api.kcisa.kr/API_CNV_048/request | 401 | 인증 필요 |
| API_CNV_049 | https://api.kcisa.kr/API_CNV_049/request | 401 | 인증 필요 |
| API_CHA_084 | https://api.kcisa.kr/openapi/API_CHA_084/request | 401 | 인증 필요 |
| API_CHA_088 | https://api.kcisa.kr/openapi/API_CHA_088/request | 401 | 인증 필요 |
| API_LIB_049 | https://api.kcisa.kr/openapi/API_LIB_049/request | 401 | 인증 필요 |
| API_CCA_145 | https://api.kcisa.kr/openapi/API_CCA_145/request | 401 | 인증 필요 |
| API_LIB_048 | https://api.kcisa.kr/openapi/API_LIB_048/request | 401 | 인증 필요 |
| API_CIA_092 | https://api.kcisa.kr/openapi/API_CIA_092/request | 401 | 인증 필요 (public_data.py에 이미 구현됨) |

---

## 2. 추천 후보 API (3~5개)

문서 기반으로 이미지 관련 출력 필드가 확인된 API 중, 기관 신뢰도 및 데이터 유형을 고려하여 5개를 우선 추천합니다.

### 후보 1: 국립중앙박물관 외_유물정보(주요유물)
- **API ID**: 551 (Category: B)
- **API 코드**: API_CNV_048
- **엔드포인트**: `https://api.kcisa.kr/API_CNV_048/request`
- **이미지 필드**: `imageObject` (이미지(썸네일))
- **설명**: 국립중앙박물관 등 주요 박물관의 유물 정보. `imageObject` 필드에 썸네일 이미지 URL이 포함될 것으로 문서상 확인됨.

### 후보 2: 국립청주박물관_소장품
- **API ID**: 642 (Category: B)
- **API 코드**: API_CHA_084
- **엔드포인트**: `https://api.kcisa.kr/openapi/API_CHA_084/request`
- **이미지 필드**: `IMAGE_OBJECT` (이미지주소)
- **설명**: 국립청주박물관 소장품 목록. `IMAGE_OBJECT` 필드에 이미지 주소가 포함될 것으로 문서상 확인됨.

### 후보 3: 국립광주박물관_소장품_리스트
- **API ID**: 654 (Category: B)
- **API 코드**: API_CHA_088
- **엔드포인트**: `https://api.kcisa.kr/openapi/API_CHA_088/request`
- **이미지 필드**: `IMAGE_OBJECT` (이미지)
- **설명**: 국립광주박물관 소장품 리스트. `IMAGE_OBJECT` 필드에 이미지가 포함될 것으로 문서상 확인됨.

### 후보 4: 한국문화정보원 외_전시정보(통합)
- **API ID**: 598 (Category: I)
- **API 코드**: API_CCA_145
- **엔드포인트**: `https://api.kcisa.kr/openapi/API_CCA_145/request`
- **이미지 필드**: `IMAGE_OBJECT` (이미지주소)
- **설명**: 통합 전시 정보. 전시 포스터/썸네일 이미지 URL이 `IMAGE_OBJECT`에 포함될 것으로 문서상 확인됨.

### 후보 5: 국립어린이청소년도서관_세계의 도서관
- **API ID**: 631 (Category: F)
- **API 코드**: API_LIB_049
- **엔드포인트**: `https://api.kcisa.kr/openapi/API_LIB_049/request`
- **이미지 필드**: `IMAGE_OBJECT` (썸네일주소)
- **설명**: 세계의 도서관 정보. `IMAGE_OBJECT` 필드에 썸네일 주소가 포함될 것으로 문서상 확인됨. 추가로 `VIDEO_OBJECT` (동영상주소) 필드도 있음.

---

## 3. 추가 후보

### 후보 6: 국립어린이청소년도서관_다국어동화구연 전체동화
- **API ID**: 625 (Category: D)
- **API 코드**: API_LIB_048
- **엔드포인트**: `https://api.kcisa.kr/openapi/API_LIB_048/request`
- **이미지 필드**: `image_object` (이미지주소)
- **설명**: 동화 관련 이미지. 소문자 필드명 `image_object` 사용.

### 후보 7: 국립민속박물관 민속아카이브 사진자료 (이미 프로젝트에 구현됨)
- **API 코드**: API_CIA_092
- **엔드포인트**: `https://api.kcisa.kr/openapi/API_CIA_092/request`
- **이미지 필드**: `IMAGE_OBJECT` (이미지주소)
- **설명**: `ium/backend/app/services/public_data.py`에 이미 `fetch_folk_museum()`로 구현되어 있음. 동일한 인증 문제로 현재 401 반환.

---

## 4. 현재 차단 사항

- **KCISA API 키 부재**: `C:\dev\contest\ium\backend\.env`에 `KCISA_API_KEY=`가 비어 있으며, 주석에 "2026-06-09 테스트: 401 Unauthorized, 재발급 필요"라고 기록되어 있음.
- **테스트 불가**: 위 7개 후보 API 모두 유효한 serviceKey 없이는 401 Unauthorized를 반환. 따라서 실제 응답에 이미지 URL이 포함되는지 런타임 검증은 불가능한 상태.
- **API_CCA_169**: 현재 보유 중인 키(`77f571ea-321d-464f-bbf0-f49597b5edb9`)는 이 API에만 유효하며, 이 API는 `URL` 필드에 웹페이지 링크만 제공하고 이미지는 제공하지 않음.

---

## 5. 다음 단계 제안

1. **KCISA API 키 발급/재발급**: `https://www.culture.go.kr` 에서 위 후보 API에 대한 이용 신청 및 serviceKey 발급
2. **키 발급 후 우선 테스트 대상**: `API_CIA_092` (이미 프로젝트에 통합됨) → `API_CNV_048` → `API_CHA_084` 순으로 테스트
3. **실제 이미지 URL 검증**: API 호출 후 `IMAGE_OBJECT`/`imageObject` 값이 실제로 `http(s)://.../.jpg` 등 이미지 확장자로 끝나는지, HEAD 요청으로 접근 가능한지 확인
4. **대안 탐색**: KCISA 키 발급이 지연될 경우, `data.go.kr` (공공데이터포털)에서 국가기록원 등의 이미지 제공 API를 추가로 검색

---

*보고서 생성일: 2026-06-09*
