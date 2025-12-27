# Prometheus Monitoring & Metrics Setup Guide

This document explains the Prometheus monitoring that has been integrated into the Meeting Insight Generator.

## ✅ Implementation Summary

### What Has Been Implemented

#### Core Metrics Infrastructure
- **`backend/src/utils/metrics.py`**: Graceful handling if `prometheus-client` is not installed; application continues to work without Prometheus; comprehensive metrics definitions
- **`/metrics` endpoint** in `backend/main.py`: Returns Prometheus-formatted metrics; works even without Prometheus installed; accessible at `http://localhost:3000/metrics`
- **Automatic HTTP middleware**: Tracks all HTTP requests (method, endpoint, status code); measures request duration; only active if Prometheus available
- **Agent & Processing metrics** in orchestrator: Tracks agent execution times and success/error rates; monitors meeting processing duration; optional and non-breaking
- **Dependencies**: `prometheus-client==0.19.0` added to `requirements.txt` (optional library)

### Safety Features
- ✅ Application works perfectly fine **without Prometheus**
- ✅ No errors if `prometheus-client` is not installed
- ✅ Metrics collection is completely optional
- ✅ All metric calls wrapped to handle missing library
- ✅ All existing functionality preserved
- ✅ No changes to existing API endpoints
- ✅ Metrics are additive only
- ✅ Minimal performance impact (microseconds per request)

---

## Overview

The application now includes Prometheus metrics collection that tracks:
- HTTP request counts and durations
- Meeting processing metrics (success/error rates, processing times)
- Agent execution metrics (per-agent performance)
- Vector store operations
- Database query metrics

## Installation

The monitoring is **optional** and the application will work fine without it. To enable metrics:

```bash
pip install prometheus-client
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

## Metrics Endpoint

Once the application is running, metrics are available at:

```
GET http://localhost:3000/metrics
```

This endpoint returns Prometheus-formatted metrics that can be scraped by Prometheus.

## Available Metrics

### HTTP Metrics
- `http_requests_total` - Total HTTP requests by method, endpoint, and status code
- `http_request_duration_seconds` - HTTP request duration histogram

### Meeting Processing Metrics
- `meeting_processing_total` - Total meetings processed (by status: success, error)
- `meeting_processing_duration_seconds` - Processing duration by stage (transcription, agents, total)

### Agent Metrics
- `agent_executions_total` - Agent executions by agent name and status
- `agent_execution_duration_seconds` - Agent execution duration by agent name

### Vector Store Metrics
- `vector_store_size` - Current number of vectors in store
- `vector_search_requests_total` - Total search requests
- `vector_search_duration_seconds` - Search operation duration

### Database Metrics
- `db_queries_total` - Database queries by operation and status
- `db_query_duration_seconds` - Query duration by operation

## Testing Metrics

1. **Start the application:**
   ```bash
   cd backend
   python main.py
   ```

2. **Access metrics endpoint:**
   ```bash
   curl http://localhost:3000/metrics
   ```

3. **Make some API calls** (upload a meeting, search, etc.) and check metrics again to see them update.

## Integration with Prometheus

### Basic Prometheus Setup

1. **Install Prometheus:**
   ```bash
   # Download from https://prometheus.io/download/
   # Or use Docker:
   docker run -d -p 9090:9090 prom/prometheus
   ```

2. **Configure Prometheus** (`prometheus.yml`):
   ```yaml
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'meeting-insight-api'
       static_configs:
         - targets: ['localhost:3000']
       metrics_path: '/metrics'
   ```

3. **Start Prometheus:**
   ```bash
   prometheus --config.file=prometheus.yml
   ```

4. **Access Prometheus UI:**
   Open http://localhost:9090

## Example Queries

Once Prometheus is scraping metrics, you can query:

- **Request rate:**
  ```
  rate(http_requests_total[5m])
  ```

- **Average request duration:**
  ```
  rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
  ```

- **Agent success rate:**
  ```
  rate(agent_executions_total{status="success"}[5m]) / rate(agent_executions_total[5m])
  ```

- **Meeting processing time (95th percentile):**
  ```
  histogram_quantile(0.95, rate(meeting_processing_duration_seconds_bucket[5m]))
  ```

## Graceful Degradation

The monitoring system is designed to **not break** if `prometheus-client` is not installed:

- If the library is missing, metrics collection is disabled
- The application continues to work normally
- The `/metrics` endpoint returns a simple message indicating metrics are not available
- No errors are raised
- All metrics are optional and can be disabled by not installing `prometheus-client`

---

## Verification

The implementation has been verified to:
- ✅ Not break existing functionality
- ✅ Work without Prometheus installed
- ✅ Collect metrics when Prometheus is available
- ✅ Handle errors gracefully
- ✅ Pass linting checks
- ✅ Include comprehensive tests

---

## Next Steps (Optional)

To fully utilize monitoring:
1. Set up Prometheus server (see Integration with Prometheus section above)
2. Configure Prometheus to scrape `/metrics` endpoint
3. Optionally set up Grafana for visualization
4. Add more custom metrics as needed

---

## Summary

**Status**: ✅ **Complete and Safe**

The Prometheus monitoring is fully implemented and **will not affect** your current project. The application:
- Works exactly as before if Prometheus is not installed
- Automatically collects metrics if Prometheus is available
- Provides `/metrics` endpoint for monitoring tools
- Tracks key operations without performance impact

**You can safely use this in production** — it's designed to be completely optional and non-intrusive.