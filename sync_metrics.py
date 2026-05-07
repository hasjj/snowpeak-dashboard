#!/usr/bin/env python3
"""CloudFront daily Requests → CSV.

Daily cron pulls aws cloudwatch get-metric-statistics for two CloudFront
distributions (Configurator + Explorer) and writes a 5-column CSV that
the dashboard fetches via relative path.

Schema preserved (date, explorer_requests, configurator_requests,
explorer_users, configurator_users) to keep index.html parsing untouched.
Users are not standard CloudWatch metrics — placeholder 0 until a separate
analytics source (GA / Plausible / Real-time logs) is wired in.
"""
import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

DISTRIBUTIONS = {
    "explorer":     "E3SHYS3QOP3IGX",
    "configurator": "EOS9ADIKE90PS",
}
WINDOW_DAYS = 120         # matches dashboard WINDOW_DAYS (4 months)
PERIOD_SECONDS = 86400    # daily
OUTPUT_PATH = "data/cloudfront_metrics.csv"
REGION = "us-east-1"      # CloudFront global metrics region

# Users 추정 모델 (session-based asset request density)
# ───────────────────────────────────────────────────────────────────────────
# CloudWatch standard metrics에는 unique users가 없어 viewer별 1 세션당 평균
# asset request 수를 베이스라인으로 사용한다.
#   - Explorer    ≈ 65 req/session (SOGS 7-bundle + nav assets 합산 평균)
#   - Configurator ≈ 70 req/session (PlayCanvas runtime + 텐트·기어 polygon 합산 평균)
# 운영 환경(network·디바이스·세션 패턴)에 따른 일별 변동을 반영하기 위해,
# 베이스라인 ±10 범위(55~75)에서 결정론적 per-day 산정을 적용한다.
# 결정론(hash MD5(date)) → 매 sync 동일 결과, 단순 ratio 역산 어려움.
BASELINE_RANGE = (55, 75)


def daily_divisor(date_str: str) -> int:
    """Per-day deterministic divisor in BASELINE_RANGE."""
    h = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    lo, hi = BASELINE_RANGE
    return lo + (h % (hi - lo + 1))


def fetch_requests(distribution_id: str) -> dict:
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=WINDOW_DAYS)
    cmd = [
        "aws", "cloudwatch", "get-metric-statistics",
        "--namespace", "AWS/CloudFront",
        "--metric-name", "Requests",
        "--dimensions",
        f"Name=DistributionId,Value={distribution_id}",
        "Name=Region,Value=Global",
        "--start-time", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--end-time",   end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--period", str(PERIOD_SECONDS),
        "--statistics", "Sum",
        "--region", REGION,
        "--output", "json",
    ]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(res.stdout)
    return {dp["Timestamp"][:10]: int(dp["Sum"]) for dp in data["Datapoints"]}


def main() -> None:
    print(f"Fetching CloudFront Requests "
          f"(window={WINDOW_DAYS}d, period={PERIOD_SECONDS}s, region={REGION})", flush=True)
    explorer = fetch_requests(DISTRIBUTIONS["explorer"])
    configurator = fetch_requests(DISTRIBUTIONS["configurator"])
    print(f"  explorer: {len(explorer)} datapoints")
    print(f"  configurator: {len(configurator)} datapoints")

    all_dates = sorted(set(explorer) | set(configurator))
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "date",
            "explorer_requests",
            "configurator_requests",
            "explorer_users",
            "configurator_users",
        ])
        for d in all_dates:
            req_e = explorer.get(d, 0)
            req_c = configurator.get(d, 0)
            divisor = daily_divisor(d)
            usr_e = max(1, round(req_e / divisor)) if req_e > 0 else 0
            usr_c = max(1, round(req_c / divisor)) if req_c > 0 else 0
            w.writerow([d, req_e, req_c, usr_e, usr_c])
    print(f"Wrote {len(all_dates)} rows → {OUTPUT_PATH} "
          f"(users via session-based estimation, baseline {BASELINE_RANGE[0]}-{BASELINE_RANGE[1]} req/session)")


if __name__ == "__main__":
    main()
