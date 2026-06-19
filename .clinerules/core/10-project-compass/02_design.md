# 02 — 문서 트리 설계 패턴

## 기본 원칙

1. **1:1 미러링**: 실제 폴더 구조 → `_guide/` 구조 완전 대응
2. **GUIDE.md 네이밍**: 모든 문서는 `GUIDE.md` (일관성)
3. **단방향 참조**: 상위→하위만 참조, 역방향 없음
4. **단일 책임**: 하나의 GUIDE.md는 하나의 폴더/주제만 담당

## 설계 흐름

### Phase 1: 폴더 목록 → 문서 경로 매핑

```
실제 폴더              →    _guide 경로
/                          _guide/MAIN_GUIDE.md
src/                       _guide/src/GUIDE.md
src/api/                   _guide/src/api/GUIDE.md
src/api/routes/            _guide/src/api/routes/GUIDE.md
src/components/            _guide/src/components/GUIDE.md
src/lib/                   _guide/src/lib/GUIDE.md
tests/                     _guide/tests/GUIDE.md
infra/                     _guide/infra/GUIDE.md
```

### Phase 2: 깊이별 문서 유형 결정

| 깊이 | 기준 | 문서 유형 |
|------|------|----------|
| 0 (루트) | 항상 | 나침반 |
| 1단계 (src, tests) | 항상 | 나침반 |
| 2단계 | 하위 폴더 2개↑ | 나침반 |
| 2단계 | 파일만 존재 | 상세 |
| 3단계↓ | 대부분 | 상세 |

### Phase 3: 예상 줄 수 계산

파일 수 × 3줄(테이블 행) + 헤더 20줄 = 예상 줄 수

예상 > 80줄 → 나침반으로 설계
예상 ≤ 80줄 → 상세로 설계

## 패턴별 설계 예시

### 패턴 A: Feature-based 구조 (Next.js, NestJS)

```
실제 구조:
src/
  features/
    auth/
    dashboard/
    settings/
  shared/
    components/
    hooks/
    utils/

_guide 구조:
_guide/src/GUIDE.md                        [나침반]
_guide/src/features/GUIDE.md               [나침반]
_guide/src/features/auth/GUIDE.md          [상세]
_guide/src/features/dashboard/GUIDE.md     [상세]
_guide/src/features/settings/GUIDE.md      [상세]
_guide/src/shared/GUIDE.md                 [나침반]
_guide/src/shared/components/GUIDE.md      [상세]
_guide/src/shared/hooks/GUIDE.md           [상세]
_guide/src/shared/utils/GUIDE.md           [상세]
```

### 패턴 B: Layered 구조 (FastAPI, Django)

```
실제 구조:
app/
  routers/
  services/
  models/
  schemas/
  core/

_guide 구조:
_guide/app/GUIDE.md           [나침반]
_guide/app/routers/GUIDE.md   [상세 — 엔드포인트 목록]
_guide/app/services/GUIDE.md  [상세 — 비즈니스 로직]
_guide/app/models/GUIDE.md    [상세 — DB 모델]
_guide/app/schemas/GUIDE.md   [상세 — Pydantic 스키마]
_guide/app/core/GUIDE.md      [상세 — 설정/의존성]
```

### 패턴 C: 단순 구조 (소규모 프로젝트)

```
실제 구조:
src/
  index.ts
  utils.ts
  types.ts
  config.ts

_guide 구조:
_guide/MAIN_GUIDE.md        [나침반]
_guide/src/GUIDE.md         [상세 — 파일 전체 기술]
```

## 특수 케이스 처리

### 파일이 많은 폴더 (20개↑)
→ 파일을 성격별로 그룹핑 후 그룹별 섹션으로 분리
→ 80줄 초과 시 그룹별로 별도 파일 생성

```
components/GUIDE.md (나침반)
components/ui/GUIDE.md     (버튼, 인풋 등 기본 UI)
components/layout/GUIDE.md (헤더, 사이드바 등)
components/forms/GUIDE.md  (폼 관련 컴포넌트)
```

### 설정 파일이 루트에 많을 때
→ `_guide/config/GUIDE.md` 별도 생성
→ .env, tsconfig, eslint, prettier 등 통합 설명

### 스크립트/자동화 폴더
→ `_guide/scripts/GUIDE.md`에 각 스크립트 목적과 실행 방법 기술