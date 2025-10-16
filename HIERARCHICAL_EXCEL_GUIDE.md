# 계층형 엑셀 데이터 처리 가이드

## 구현 완료 사항

✅ **기존 Qdrant 스키마 유지** - 모든 기존 필드가 그대로 보존됩니다
✅ **계층형 컬럼 추가** - lvl1~lvl4 필드가 추가되었습니다
✅ **엑셀 파싱 규칙** - 병합 셀 및 빈 셀 forward fill 로직 구현
✅ **FAQ 챗봇 연계** - 계층형 검색 API 구현

## 데이터 구조

### 엑셀 컬럼 매핑
- **구분1** → `lvl1` (대분류)
- **구분2** → `lvl2` (중분류) 
- **구분3** → `lvl3` (소분류)
- **세부 내용 + 비고** → `lvl4` (상세 내용)

### JSON 출력 형식
```json
{
  "file_id": "uuid",
  "file_name": "파일명.xlsx",
  "file_type": ".xlsx",
  "upload_time": "YYYY-MM-DDTHH:MM:SSZ",
  "chunk_index": 0,
  "original_text": "원문 내용",
  "text_length": 0,
  "search_text": "검색용 텍스트",
  "context_text": "문맥용 텍스트",
  "sheet_name": "시트명",
  "cell_address": "A1",
  "col_header": "컬럼명",
  "is_numeric": false,
  "row": 0,
  "col": "A",
  "lvl1": "구분1",
  "lvl2": "구분2", 
  "lvl3": "구분3",
  "lvl4": "세부 내용 + 비고"
}
```

## API 엔드포인트

### 1. 대분류 조회
```
GET /hierarchy/lvl1
```
**응답:**
```json
{
  "status": "success",
  "lvl1_categories": ["휴가", "복리후생", "근무"],
  "count": 3
}
```

### 2. 중분류 조회
```
GET /hierarchy/lvl2/{lvl1}
```
**예시:** `GET /hierarchy/lvl2/휴가`

**응답:**
```json
{
  "status": "success",
  "lvl1": "휴가",
  "lvl2_categories": ["연차", "특별휴가"],
  "count": 2
}
```

### 3. 소분류 조회
```
GET /hierarchy/lvl3/{lvl1}/{lvl2}
```
**예시:** `GET /hierarchy/lvl3/휴가/연차`

**응답:**
```json
{
  "status": "success",
  "lvl1": "휴가",
  "lvl2": "연차", 
  "lvl3_categories": ["① 발생", "② 사용", "③ 신청"],
  "count": 3
}
```

### 4. 상세 내용 조회
```
GET /hierarchy/lvl4/{lvl1}/{lvl2}/{lvl3}
```
**예시:** `GET /hierarchy/lvl4/휴가/연차/① 발생`

**응답:**
```json
{
  "status": "success",
  "hierarchy": {
    "lvl1": "휴가",
    "lvl2": "연차",
    "lvl3": "① 발생"
  },
  "contents": [
    {
      "content": "1년 이상 근속하며 근로일수 80% 이상 개근자에게 15일 유급휴가 부여 | 매년 1월 1일 기점",
      "context_text": "분류 체계: 대분류: 휴가 > 중분류: 연차 > 소분류: ① 발생 | 구분1: 휴가 | 상세 내용: 1년 이상 근속하며 근로일수 80% 이상 개근자에게 15일 유급휴가 부여 | 매년 1월 1일 기점",
      "source": "test_hierarchical_data.xlsx",
      "sheet_name": "인사규정",
      "cell_address": "인사규정!A2"
    }
  ],
  "count": 1
}
```

## FAQ 챗봇 구현 방식

### 1. 대분류 버튼 생성
```javascript
// lvl1 API 호출하여 버튼 생성
fetch('/hierarchy/lvl1')
  .then(response => response.json())
  .then(data => {
    data.lvl1_categories.forEach(category => {
      // 버튼 생성
      createButton(category, 'lvl1');
    });
  });
```

### 2. 중분류 버튼 생성
```javascript
// lvl1 선택 시 lvl2 API 호출
function onLvl1Selected(lvl1) {
  fetch(`/hierarchy/lvl2/${lvl1}`)
    .then(response => response.json())
    .then(data => {
      data.lvl2_categories.forEach(category => {
        createButton(category, 'lvl2');
      });
    });
}
```

### 3. 최종 답변 출력
```javascript
// lvl3 선택 시 lvl4 API 호출하여 답변 표시
function onLvl3Selected(lvl1, lvl2, lvl3) {
  fetch(`/hierarchy/lvl4/${lvl1}/${lvl2}/${lvl3}`)
    .then(response => response.json())
    .then(data => {
      // 답변 표시
      displayAnswer(data.contents[0].content);
    });
}
```

## 엑셀 파일 형식 요구사항

### 필수 컬럼 구조
| 구분1 | 구분2 | 구분3 | 세부 내용 | 비고 |
|-------|-------|-------|-----------|------|
| 휴가  | 연차  | ① 발생 | 1년 이상 근속하며... | 매년 1월 1일 기점 |

### Forward Fill 규칙
- **병합 셀** 또는 **빈 셀**은 상위 행의 값을 상속
- lvl1~lvl3은 구분1~3에서 자동으로 채워짐
- lvl4는 세부 내용과 비고를 " | "로 연결

## 검색 기능 개선

### 계층형 정보 포함 검색
- **search_text**: `휴가 > 연차 > ① 발생 | 구분1: 휴가`
- **context_text**: 풍부한 계층형 컨텍스트 포함

### 향상된 검색 정확도
- 계층형 구조 정보가 검색 텍스트에 포함되어 더 정확한 매칭
- LLM 컨텍스트에 분류 체계 정보 제공으로 더 나은 답변 생성

## 테스트 파일

### 생성된 테스트 파일
- `test_hierarchical_data.xlsx`: 계층형 구조를 가진 샘플 엑셀 파일
- `test_hierarchical_excel.py`: 테스트 파일 생성 스크립트
- `test_hierarchical_implementation.py`: 구현 검증 테스트

### 테스트 실행
```bash
# 테스트 엑셀 파일 생성
python test_hierarchical_excel.py

# 구현 검증 테스트
python test_hierarchical_implementation.py
```

## 주의사항

1. **엑셀 파일 형식**: 구분1~3, 세부 내용, 비고 컬럼이 순서대로 있어야 함
2. **데이터 정합성**: 빈 셀이나 병합 셀은 자동으로 상위 값으로 채워짐
3. **API 호출**: 계층형 검색 API는 Qdrant 클라이언트에 의존
4. **성능**: 대용량 데이터의 경우 scroll API 사용으로 성능 고려 필요

## 다음 단계

1. **프론트엔드 UI 구현**: 계층형 버튼 인터페이스
2. **캐싱 최적화**: 자주 사용되는 계층 정보 캐싱
3. **검색 개선**: 계층형 필터링을 통한 고급 검색
4. **통계 기능**: 계층별 데이터 통계 및 분석
