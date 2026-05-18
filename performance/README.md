# TaskHive Performance Tests

Start the Docker stack first:

```powershell
docker compose --env-file .env.docker up --build
Run a smoke load test:

locust -f performance/locustfile.py --host http://127.0.0.1:8000 --headless -u 5 -r 1 -t 1m --csv performance/reports/smoke
Run a local load profile:

locust -f performance/locustfile.py --host http://127.0.0.1:8000 --headless -u 100 -r 10 -t 5m --csv performance/reports/load
Targets:

0% 5xx errors under smoke/load.
p95 list endpoint latency below 150ms in local Docker where practical.
Stable worker, Redis, Postgres, and Django metrics during the run.