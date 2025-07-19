# Ocea Chart Data API Documentation

> **🏆 Team Amadeus - Junction Hackathon Project**

## Overview

The **Ocea** Chart Data API provides structured data endpoints for creating visualizations in the frontend. These endpoints return data in a format optimized for popular charting libraries like Chart.js, D3.js, or similar.

**Ocea** is developed by **Team Amadeus** during the **Junction Hackathon** to revolutionize sustainable aquaculture through intelligent IoT monitoring.

## Authentication
All endpoints require JWT authentication via Bearer token in the Authorization header:
```bash
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Historical Chart Data
**Endpoint:** `GET /mvp/pond/{pond_id}/chart-data`

**Description:** Get historical sensor data for a specific pond, formatted for chart visualization.

**Parameters:**
- `pond_id` (path): The ID of the pond (e.g., "pond_001", "pond_002")
- `parameter` (query, optional): Sensor parameter to retrieve. Options:
  - `temperature` (default)
  - `ph`
  - `dissolved_oxygen`
  - `turbidity`
  - `ammonia`
  - `nitrites`
  - `nitrates`
- `hours` (query, optional): Number of hours of historical data (default: 24)

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/mvp/pond/pond_001/chart-data?parameter=temperature&hours=12"
```

**Response Format:**
```json
{
  "pond_id": "pond_001",
  "parameter": "temperature",
  "period_hours": 12,
  "data": {
    "labels": ["2025-07-19 08:48", "2025-07-19 08:49", ...],
    "values": [27.23, 27.31, 27.28, ...],
    "unit": "°C",
    "name": "Temperature"
  },
  "statistics": {
    "min": 27.23,
    "max": 27.43,
    "average": 27.31,
    "latest": 27.28
  },
  "thresholds": {
    "min": 20.0,
    "max": 30.0,
    "critical_min": 15.0,
    "critical_max": 35.0,
    "optimal_min": 20.0,
    "optimal_max": 30.0
  },
  "data_points": 26,
  "last_updated": "2025-07-19T09:18:49.039781"
}
```

### 2. Real-time Chart Data
**Endpoint:** `GET /mvp/pond/{pond_id}/realtime-chart`

**Description:** Get recent sensor data for real-time chart updates, optimized for live dashboards.

**Parameters:**
- `pond_id` (path): The ID of the pond
- `parameter` (query, optional): Sensor parameter (same options as above)
- `minutes` (query, optional): Number of minutes of recent data (default: 60)

**Example Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/mvp/pond/pond_002/realtime-chart?parameter=temperature&minutes=30"
```

**Response Format:**
```json
{
  "pond_id": "pond_002",
  "parameter": "temperature",
  "period_minutes": 30,
  "data": {
    "timestamps": ["2025-07-19T08:48:56.730000", ...],
    "values": [23.01, 23.17, 23.23, ...],
    "unit": "°C",
    "name": "Temperature"
  },
  "thresholds": {
    "min": 20.0,
    "max": 30.0,
    "critical_min": 15.0,
    "critical_max": 35.0,
    "optimal_min": 20.0,
    "optimal_max": 30.0
  },
  "latest_value": 21.7,
  "data_points": 150,
  "last_updated": "2025-07-19T09:18:49.039781"
}
```

## Integration Examples

### Chart.js Example
```javascript
// Fetch data
const response = await fetch('/mvp/pond/pond_001/chart-data?parameter=temperature', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const chartData = await response.json();

// Create Chart.js chart
const config = {
  type: 'line',
  data: {
    labels: chartData.data.labels,
    datasets: [{
      label: chartData.data.name,
      data: chartData.data.values,
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: false,
        min: chartData.thresholds.min,
        max: chartData.thresholds.max
      }
    }
  }
};
```

### Real-time Updates
```javascript
// For real-time charts, poll the realtime endpoint
setInterval(async () => {
  const response = await fetch('/mvp/pond/pond_001/realtime-chart?minutes=5', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  
  // Update chart with new data
  chart.data.labels = data.data.timestamps.map(ts => new Date(ts).toLocaleTimeString());
  chart.data.datasets[0].data = data.data.values;
  chart.update();
}, 10000); // Update every 10 seconds
```

## Data Types & Units

| Parameter | Unit | Typical Range | Description |
|-----------|------|---------------|-------------|
| temperature | °C | 15-35 | Water temperature |
| ph | pH | 6.5-8.5 | Acidity/alkalinity |
| dissolved_oxygen | mg/L | 5-15 | Oxygen concentration |
| turbidity | NTU | 0-100 | Water clarity |
| ammonia | mg/L | 0-2 | Ammonia concentration |
| nitrites | mg/L | 0-1 | Nitrite concentration |
| nitrates | mg/L | 0-50 | Nitrate concentration |

## Error Handling

### Common Error Responses:
- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Pond ID doesn't exist
- `422 Validation Error`: Invalid parameter values
- `500 Internal Server Error`: Database or server issues

### Error Response Format:
```json
{
  "detail": "Error description",
  "error": true
}
```

## Performance Notes

1. **Historical Data**: Use for initial chart loading and historical analysis
2. **Real-time Data**: Use for live updates and recent trends
3. **Caching**: Responses include `last_updated` timestamp for cache validation
4. **Rate Limiting**: Recommended polling interval: 10-30 seconds for real-time data
5. **Data Points**: Historical endpoint limits to reasonable data points for performance

## WebSocket Alternative

For true real-time updates, consider using the WebSocket endpoint:
```javascript
const ws = new WebSocket(`ws://localhost:8000/mvp/pond/${pondId}/ws`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update charts with real-time sensor data
};
```

## Troubleshooting

1. **No Data Returned**: Check if the pond has recent sensor readings
2. **Empty Arrays**: Verify the time range parameters (hours/minutes)
3. **Authentication Issues**: Ensure JWT token is valid and not expired
4. **CORS Errors**: Frontend should be served from localhost:3000, :5173, or :8080
