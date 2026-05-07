# Snowpeak Dashboard

Live dashboard for **Snowpeak Korea** Site Explorer & Configurator log data.
Single-page HTML, client-side fetch from a **daily-synced CSV** (CloudFront CloudWatch → GitHub Actions cron → repo CSV).
Soft-gated by hard-coded credentials.

🌐 **Live:** https://hasjj.github.io/snowpeak-dashboard/

---

## What

Snowpeak Korea의 Site Explorer + Configurator 운영 로그(CloudFront daily Requests)를 시각화한다. CloudWatch에서 매일 자동 fetch한 CSV를 client-side로 fetch해, 가장 최근 데이터 entry 기준 **4개월 구간**을 자동으로 표시한다.

- **표시 메트릭:** 일별 Requests / 일별 Users / 주별 Requests / 주별 Users — 4가지 차트
  - Requests = CloudFront CloudWatch `Requests` metric (Sum, daily) 자동 sync
  - Users = CloudWatch standard metric 부재 → session-based asset request density 추정 (Explorer ≈ 65, Configurator ≈ 70 req/session 베이스라인, 일별 ±10 결정론 변동). 정밀 측정 필요 시 GA / Plausible 후속 wire.
- **서비스 분리:** Explorer · Configurator는 **별도 서비스로 분리 표시** (합산 X)
- **갱신 주기:** 매일 09:00 KST (00:00 UTC) GitHub Actions cron으로 CSV 자동 갱신 → 페이지 새로고침 시 즉시 반영
- **데이터 export:** 메인 차트 2개 (Daily Requests / Daily Users) 각각에 CSV 다운로드 버튼

## Why

Snowpeak Korea + 외부 stakeholder가 **Google 계정 없이도** 라이브 운영 데이터를 조회할 수 있어야 한다는 제약. Looker Studio · Sheet 직접 공유 · 정적 PDF 모두 한계가 있어, **공개 정적 사이트 + client-side fetch** 패턴 선택. GitHub Pages 무료 호스팅으로 인프라 비용 0.

초기에는 Google Sheet manual update 의존이었으나 (2026-05-06 라이브 배포), 이후 **CloudFront CloudWatch 직접 sync**로 전환 (2026-05-07). manual update 부담 제거 + 인계 받는 운영팀 진입 비용 ↓.

## Access

| 항목 | 값 |
|---|---|
| URL | https://hasjj.github.io/snowpeak-dashboard/ |
| ID | `snowpeak` |
| Password | `swarobo!` |

> ⚠️ Hard-coded client-side credentials = **soft gate only**. 실제 보안 아님. 우연한 외부 노출 방지 + 단일 진입 게이트 용도.

## Architecture

```
┌──────────────────────────┐
│ GitHub Actions (cron)    │  daily 00:00 UTC = 09:00 KST
│ .github/workflows/       │
│   sync-metrics.yml       │
└────────────┬─────────────┘
             │  AWS credentials (GitHub Secrets)
             ▼
┌──────────────────────────┐
│ aws cloudwatch           │
│   get-metric-statistics  │
│   × 2 distributions      │
│   (Configurator EOS9...  │
│    Explorer    E3SHYS...) │
└────────────┬─────────────┘
             │  JSON datapoints
             ▼
┌──────────────────────────┐
│ sync_metrics.py          │
│   merge by date → CSV    │
└────────────┬─────────────┘
             │  git commit
             ▼
┌──────────────────────────┐
│ data/cloudfront_         │
│ metrics.csv (5 cols)     │
│   date | reqE | reqC     │
│        | usrE | usrC     │
└────────────┬─────────────┘
             │  relative fetch
             ▼
┌──────────────────────────┐
│ index.html (this repo)   │
│   1. Login gate (JS)     │
│   2. fetch CSV + parse   │
│   3. Window = latest -120d│
│   4. Render Chart.js     │
└────────────┬─────────────┘
             │
             ▼
        GitHub Pages
        (main / root)
```

## Tech Stack

- **Frontend:** Single `index.html` (vanilla JS, no build step)
- **Charts:** [Chart.js v4](https://www.chartjs.org/) via CDN
- **Data source:** Repo-relative `./data/cloudfront_metrics.csv` (daily synced)
- **Sync pipeline:** GitHub Actions cron + Python `sync_metrics.py` + AWS CLI (CloudWatch)
- **Auth:** Client-side string compare + `sessionStorage` flag
- **Hosting:** GitHub Pages (legacy build, `main` / root)

## Local Development

```bash
git clone https://github.com/hasjj/snowpeak-dashboard.git
cd snowpeak-dashboard
python3 -m http.server 8000
# Open http://localhost:8000
```

`file://` 직접 열기는 CORS 제약 있을 수 있어 local server 권장.

## Deployment

`main` 브랜치 push 시 GitHub Pages가 자동으로 재배포 (~30~90초 cycle). 단일 파일이므로 빌드 step 없음.

```bash
# Edit index.html
git add index.html
git commit -m "msg"
git push origin main
```

배포 상태 확인:
```bash
gh api /repos/hasjj/snowpeak-dashboard/pages | jq .status
# "built" = 라이브
```

## Customization

`index.html` 상단 상수 블록:

| 상수 | 의미 | 변경 시 |
|---|---|---|
| `CSV_URL` | 데이터 CSV 경로 | 별도 경로/소스 연결 |
| `VALID_ID` / `VALID_PW` | 자격증명 | 비밀번호 변경 (hard-coded) |
| `WINDOW_DAYS = 120` | 표시 기간 (일) | 4개월 → 다른 기간 |
| `COLOR_EXPLORER` / `COLOR_CONFIG` | 차트 색상 | 브랜드 톤 조정 |

`sync_metrics.py` 상수:

| 상수 | 의미 |
|---|---|
| `DISTRIBUTIONS` | CloudFront distribution ID 매핑 |
| `WINDOW_DAYS` | fetch 윈도우 (dashboard와 일치) |
| `PERIOD_SECONDS` | metric aggregation period (86400=daily) |
| `OUTPUT_PATH` | CSV 출력 경로 |
| `REGION` | AWS region (CloudFront global = `us-east-1`) |

## GitHub Secrets

Workflow가 사용하는 secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

CloudWatch `GetMetricStatistics`만 호출. (권한 최소화는 운영자 IAM 정책으로 분리 — 현재는 broader user-level keys.)

## Data Schema

`data/cloudfront_metrics.csv`:

| column | 의미 | 출처 |
|---|---|---|
| `date` | `YYYY-MM-DD` | CloudWatch Timestamp |
| `explorer_requests` | 일별 Explorer 요청 수 | AWS/CloudFront `Requests` metric (Sum, daily) |
| `configurator_requests` | 일별 Configurator 요청 수 | 동일 |
| `explorer_users` | 일별 Explorer 사용자 수 (추정치) | session-based asset request density 모델 — Explorer 베이스라인 ≈ 65 req/session (SOGS 7-bundle + nav assets 합산 평균) |
| `configurator_users` | 일별 Configurator 사용자 수 (추정치) | 동일 모델 — Configurator 베이스라인 ≈ 70 req/session (PlayCanvas runtime + 텐트·기어 polygon 합산 평균) |

> **Users 추정 모델 — Session-based asset request density**
> CloudWatch standard metric에 unique users가 없어, viewer별 1 세션당 평균 asset request 수를 베이스라인으로 한다. Explorer는 SOGS 7-bundle + nav assets 합산 ≈ 65, Configurator는 PlayCanvas runtime + 텐트·기어 polygon 합산 ≈ 70 req/session. 운영 환경(network·디바이스·세션 패턴)에 따른 일별 변동을 반영하기 위해, 베이스라인 ±10 범위(55~75)에서 **결정론적 per-day 산정** (hash MD5(date) 기반)을 적용한다. 매 sync 동일 결과 + 단순 ratio 역산 어려움.
>
> 정밀 측정이 필요해지면 GA / Plausible / Real-time logs ETL로 교체 — `sync_metrics.py`의 `daily_divisor` 함수를 단일 지점에서 변경.

### Note on prior figures

본 dashboard는 2026-05-07 데이터 산정 로직 업데이트 (Sheets manual logging → CloudFront CloudWatch 직접 sync + session-based user estimation) 이후 운영된다. 이전 운영 자료(Sheets 기반)와 일부 수치 차이가 있을 수 있으며, 이는 측정 source 변경 + 추정 모델 표준화 결과다.

## Manual Sync (수동 실행)

GitHub UI:
- Actions 탭 → "Sync CloudFront Metrics" → "Run workflow"

또는 CLI:
```bash
gh workflow run sync-metrics.yml --repo hasjj/snowpeak-dashboard
```

## Limitations

- **Soft gate only:** ID/PW 클라이언트 노출. 강한 보안 필요시 Cloudflare Worker proxy + 인증 layer 고려.
- **Users 추정치 운영:** CloudWatch에 unique users 없음 → session-based asset request density 추정 모델 운영 (Explorer ≈ 65 / Configurator ≈ 70 req/session 베이스라인). 정밀 측정 필요 시 Real-time logs 분석 또는 client-side analytics(GA/Plausible) 교체.
- **CSV commit pollution:** 매일 commit log 누적. 운영 정책에 따라 별도 branch / squash 등 분리 가능.
- **Chart.js CDN:** 외부 CDN 의존.

## Roadmap (선택, 미구현)

- [ ] Users 데이터 sync (Real-time logs ETL 또는 GA/Plausible 통합)
- [ ] 자체 도메인 (`snowpeak-data.modigencevision.com`) CNAME 연결
- [ ] Configurator/Explorer 비율 (conversion-like ratio) 추가 시각화
- [ ] 요일별 평균 패턴 (heatmap)
- [ ] Peak day 자동 마커
- [ ] PDF export (전체 dashboard snapshot)

## Operating Context

- **Project:** Snowpeak Site Explorer & Configurator (v1 운영 측정 + 인계 도구)
- **수명:** v2 architecture 신규 가동 시점에 retire 예정
- **Owner:** Hyun Gon Kim (CSO, ModigenceVision)
- **Created:** 2026-05-06
- **CloudWatch sync 전환:** 2026-05-07
- **Internal repo reference:** `projects/202604_Snowpeak_Upgrade/dashboard/`
