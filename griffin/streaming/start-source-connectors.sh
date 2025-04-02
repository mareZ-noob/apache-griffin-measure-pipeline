curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d '{
       "name": "postgres-connector",
       "config": {
         "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
         "database.hostname": "postgres",
         "database.port": "5432",
         "database.user": "griffin",
         "database.password": "123456",
         "database.dbname": "quartz",
         "database.server.name": "source",
         "schema.include.list": "public",
         "table.include.list": "public.source",
         "plugin.name": "pgoutput",
         "topic.prefix": "source"
       }
     }'

