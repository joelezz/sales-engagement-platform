#!/bin/bash

# Start monitoring stack for Sales Engagement Platform
# This script starts Prometheus, Grafana, AlertManager, and log aggregation

set -e

echo "🚀 Starting Sales Engagement Platform Monitoring Stack..."

# Create necessary directories
mkdir -p logs
mkdir -p monitoring/data/{prometheus,grafana,alertmanager,loki}

# Set permissions
chmod 777 monitoring/data/{prometheus,grafana,alertmanager,loki}

# Start monitoring services
echo "📊 Starting Prometheus, Grafana, and AlertManager..."
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus health check failed"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana health check failed"
fi

# Check AlertManager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ AlertManager is healthy"
else
    echo "❌ AlertManager health check failed"
fi

echo ""
echo "🎉 Monitoring stack started successfully!"
echo ""
echo "📊 Access URLs:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana:    http://localhost:3000 (admin/admin123)"
echo "   AlertManager: http://localhost:9093"
echo ""
echo "📈 Grafana Dashboards:"
echo "   - Sales Engagement Platform Overview"
echo "   - System Metrics"
echo "   - Error Tracking"
echo ""
echo "🔔 Alerts will be sent to:"
echo "   - Console logs"
echo "   - Email (if configured)"
echo "   - Slack (if webhook configured)"
echo ""
echo "📝 Logs are aggregated in Loki and viewable in Grafana"
echo ""
echo "To stop monitoring: docker-compose -f monitoring/docker-compose.monitoring.yml down"