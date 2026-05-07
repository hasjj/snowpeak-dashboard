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

# CloudWatch standard metrics에 unique users가 없어 추정치를 사용한다.
# 추정 모델: users = round(requests / REQUESTS_PER_USER)
# REQUESTS_PER_USER는 3D 인터랙티브 콘텐츠 운영의 1 세션당 평균 request 추정치이며
# 결정론적 단일 상수로 운영(매 sync마다 동일 결과). 값이 작을수록 추정 user 수가 많다.
REQUESTS_PER_USER = 55


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
            usr_e = max(1, round(req_e / REQUESTS_PER_USER)) if req_e > 0 else 0
            usr_c = max(1, round(req_c / REQUESTS_PER_USER)) if req_c > 0 else 0
            w.writerow([d, req_e, req_c, usr_e, usr_c])
    print(f"Wrote {len(all_dates)} rows → {OUTPUT_PATH} "
          f"(users estimated at requests/{REQUESTS_PER_USER})")


if __name__ == "__main__":
    main()
