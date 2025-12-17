#!/bin/bash
# Complete cleanup of all Celery tasks and queues

echo "🛑 Step 1: Stop the Invenio instance if running"
echo "   Press Ctrl+C in the terminal running 'uv run invenio-cli run'"
echo "   Waiting for you to confirm..."
read -p "   Press Enter when instance is stopped..."
echo ""

echo "🧹 Step 2: Cleaning up..."
echo ""

# Remove celerybeat schedule
echo "📅 Removing celerybeat schedule..."
rm -f celerybeat-schedule.db
echo "   ✅ Done"
echo ""

# Purge all RabbitMQ queues
echo "🐰 Purging RabbitMQ queues..."
docker exec invenio-dev-latest-mq-1 rabbitmqctl list_queues name -q | while read queue; do
    if [ ! -z "$queue" ]; then
        echo "   Purging queue: $queue"
        docker exec invenio-dev-latest-mq-1 rabbitmqctl purge_queue "$queue" 2>/dev/null || true
    fi
done
echo "   ✅ All RabbitMQ queues purged"
echo ""

# Stop all queues
echo "🛑 Stopping all RabbitMQ queues..."
docker exec invenio-dev-latest-mq-1 rabbitmqctl stop_app
docker exec invenio-dev-latest-mq-1 rabbitmqctl reset
docker exec invenio-dev-latest-mq-1 rabbitmqctl start_app
echo "   ✅ RabbitMQ reset"
echo ""

# Flush Redis cache
echo "💾 Flushing Redis cache..."
docker exec invenio-dev-latest-cache-1 redis-cli FLUSHALL
echo "   ✅ Cache flushed"
echo ""

# # Clean OpenSearch job logs
# echo "🔍 Cleaning OpenSearch job logs..."
# docker exec invenio-dev-latest-search-1 curl -X DELETE "localhost:9200/job-logs*" -s
# echo ""
# echo "   ✅ Job logs deleted"
# echo ""

# Clean database
# echo "🗄️  Cleaning database tables..."
# docker exec invenio-dev-latest-db-1 psql -U invenio -d invenio -c "TRUNCATE TABLE jobs_run CASCADE;" 2>/dev/null
# docker exec invenio-dev-latest-db-1 psql -U invenio -d invenio -c "TRUNCATE TABLE jobs_job CASCADE;" 2>/dev/null
# echo "   ✅ Database cleaned"
# echo ""

echo "✨ Complete cleanup finished!"
echo ""
echo "🚀 Now start your instance:"
echo "   source .venv/bin/activate && uv run invenio-cli run"
