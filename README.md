# Snowpeak Dashboard

Live dashboard for **Snowpeak Korea** Site Explorer & Configurator log data.
Single-page HTML, client-side fetch from a Google Sheet, soft-gated by hard-coded credentials.

🌐 **Live:** https://hasjj.github.io/snowpeak-dashboard/

---

## What

Snowpeak Korea의 Site Explorer + Configurator pilot 운영 로그를 시각화한다. Google Sheet에 일 단위로 누적되는 raw 데이터를 client-side로 fetch해, 가장 최근 데이터 entry 기준 **4개월 구간**을 자동으로 표시한다.

- **표시 메트릭:** 일별 Requests / 일별 Users / 주별 Requests / 주별 Users — 4가지 차트
- **서비스 분리:** Explorer · Configurator는 **별도 서비스로 분리 표시** (합산 X)
- **갱신 주기:** Sheet에 일 단위로 데이터 추가 → 페이지 새로고침 시 즉시 반영
- **데이터 export:** 메인 차트 2개 (Daily Requests / Daily Users) 각각에 CSV 다운로드 버튼

## Why

Snowpeak Korea + 외부 stakeholder가 **Google 계정 없이도** 라이브 운영 데이터를 조회할 수 있어야 한다는 제약. Looker Studio · Sheet 직접 공유 · 정적 PDF 모두 한계가 있어, **공개 정적 사이트 + client-side fetch** 패턴 선택. GitHub Pages 무료 호스팅으로 인프라 비용 0.

## Access

| 항목 | 값 |
|---|---|
| URL | https://hasjj.github.io/snowpeak-dashboard/ |
| ID | `snowpeak` |
| Password | `swarobo!` |

> ⚠️ Hard-coded client-side credentials = **soft gate only**. 실제 보안 아님. 우연한 외부 노출 방지 + 단일 진입 게이트 용도. 데이터 자체는 [Google Sheet](https://docs.google.com/spreadsheets/d/12qRY1IVJw5pdyoTjQuGxQpo-3cJfZNvTL43-NyXAdlw/edit)의 "anyone with link viewer" 공유에 의존한다.

## Architecture

```
┌──────────────────────────┐
│   Google Sheet           │  data entry (daily)
│   "Snowpeak Site         │
│    Explorer & Conf. Log" │
│                          │
│   Schema:                │
│   date | Req-Explorer    │
│        | Req-Configurator│
│        | Users-Explorer  │
│        | Users-Configur. │
└────────────┬─────────────┘
             │  gviz CSV endpoint
             │  (anyone with link)
             ▼
┌──────────────────────────┐
│   index.html (this repo) │
│                          │
│   1. Login gate (JS)     │
│   2. fetch CSV + parse   │
│   3. Window = latest -120d
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
- **Data source:** Google Sheets gviz CSV endpoint (`gviz/tq?tqx=out:csv`)
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
# 1~2분 후 라이브
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
| `SHEET_ID` | Google Sheet ID | 다른 sheet 연결 |
| `VALID_ID` / `VALID_PW` | 자격증명 | 비밀번호 변경 (hard-coded) |
| `WINDOW_DAYS = 120` | 표시 기간 (일) | 4개월 → 다른 기간 |
| `COLOR_EXPLORER` / `COLOR_CONFIG` | 차트 색상 | 브랜드 톤 조정 |

## Data Source

- **Sheet:** [Snowpeak Site Explorer & Configurator Log Data](https://docs.google.com/spreadsheets/d/12qRY1IVJw5pdyoTjQuGxQpo-3cJfZNvTL43-NyXAdlw/edit)
- **공유 권한:** "anyone with link viewer" 필수 (gviz endpoint 접근 조건)
- **Schema (5 columns):**
  - `date` — `YYYY-MM-DD`
  - `Requests-Explorer` — 일별 Explorer 요청 수
  - `Requests-Configurator` — 일별 Configurator 요청 수
  - `Users-Explorer` — 일별 Explorer 고유 사용자 수
  - `Users-Configurator` — 일별 Configurator 고유 사용자 수
- **숫자 포맷:** comma-separated 허용 (`1,070` 등) — JS 측에서 parsing 처리

## Limitations

- **Soft gate only:** ID/PW 클라이언트 노출. 강한 보안 필요시 Cloudflare Worker proxy + Sheet 비공개 조합 고려.
- **Sheet 공유 의존:** "anyone with link viewer" 해제되면 dashboard 빈 화면.
- **CORS:** gviz endpoint은 CORS 허용 (Google 측 정책). 정책 변경 시 fallback 필요.
- **Chart.js CDN:** 외부 CDN 의존. CDN 장애 시 차트 미렌더 (드물지만 가능).

## Roadmap (선택 항목, 미구현)

- [ ] 자체 도메인 (`snowpeak-data.modigencevision.com`) CNAME 연결
- [ ] Configurator/Explorer 비율 (conversion-like ratio) 추가 시각화
- [ ] 요일별 평균 패턴 (heatmap)
- [ ] Peak day 자동 마커
- [ ] PDF export (전체 dashboard snapshot)

## Operating Context

- **Project:** Snowpeak Site Explorer & Configurator v2 Upgrade (Phase 2)
- **Owner:** Hyun Gon Kim (CSO, ModigenceVision)
- **Created:** 2026-05-06
- **Internal repo reference:** `projects/202604_Snowpeak_Upgrade/dashboard/`
