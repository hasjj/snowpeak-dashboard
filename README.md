# Snowpeak Dashboard

Site Explorer & Configurator log data dashboard.

- Data source: Google Sheet (live, gviz CSV endpoint)
- Window: latest data entry 기준 4개월
- Auth: client-side soft gate (`snowpeak` / `swarobo!`)
- Stack: single-page HTML + Chart.js (CDN)

## Local

```bash
python3 -m http.server 8000
# http://localhost:8000
```

## Deploy

GitHub Pages — `main` branch / root.
