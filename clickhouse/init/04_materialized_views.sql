USE taxi;

-- 1. mv_trips_per_minute
-- минута, город, тип сервиса -> trips, completed, fare_sum, distance_sum
CREATE TABLE IF NOT EXISTS mv_trips_per_minute
(
    minute          DateTime,
    city_id         UInt8,
    service_type_id UInt8,
    trips_count     UInt32,
    completed_count UInt32,
    fare_sum        Float64,
    distance_km_sum Float64
)
    ENGINE = SummingMergeTree
        ORDER BY (minute, city_id, service_type_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trips_per_minute_mv
    TO mv_trips_per_minute
AS
SELECT toStartOfMinute(started_at) AS minute,
       city_id,
       service_type_id,
       count()                     AS trips_count,
       countIf(status_id = 1)      AS completed_count, -- 1 = completed
       sum(fare)                   AS fare_sum,
       sum(distance_km)            AS distance_km_sum
FROM fact_trips
GROUP BY minute, city_id, service_type_id;

-- 2. mv_city_hourly
-- час, город -> trips, completed, cancelled, fare_sum, anomaly_count
CREATE TABLE IF NOT EXISTS mv_city_hourly
(
    hour            DateTime,
    city_id         UInt8,
    trips_count     UInt32,
    completed_count UInt32,
    cancelled_count UInt32,
    fare_sum        Float64,
    anomaly_count   UInt32
)
    ENGINE = SummingMergeTree
        ORDER BY (hour, city_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_hourly_mv
    TO mv_city_hourly
AS
SELECT toStartOfHour(started_at) AS hour,
       city_id,
       count()                   AS trips_count,
       countIf(status_id = 1)    AS completed_count,
       countIf(status_id = 2)    AS cancelled_count, -- 2 = cancelled
       sum(fare)                 AS fare_sum,
       sum(is_anomaly)           AS anomaly_count
FROM fact_trips
GROUP BY hour, city_id;

-- 3. mv_driver_daily
-- день, водитель -> trips, completed, fare_sum, tip_sum
CREATE TABLE IF NOT EXISTS mv_driver_daily
(
    day             Date,
    driver_id       UInt32,
    trips_count     UInt32,
    completed_count UInt32,
    fare_sum        Float64,
    tip_sum         Float64
)
    ENGINE = SummingMergeTree
        ORDER BY (day, driver_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_driver_daily_mv
    TO mv_driver_daily
AS
SELECT toDate(started_at)     AS day,
       driver_id,
       count()                AS trips_count,
       countIf(status_id = 1) AS completed_count,
       sum(fare)              AS fare_sum,
       sum(tip)               AS tip_sum
FROM fact_trips
GROUP BY day, driver_id;


-- 4. mv_zone_flows
-- час, район откуда, район куда -> trips_count
CREATE TABLE IF NOT EXISTS mv_zone_flows
(
    hour            DateTime,
    pickup_zone_id  UInt16,
    dropoff_zone_id UInt16,
    trips_count     UInt32
)
    ENGINE = SummingMergeTree
        ORDER BY (hour, pickup_zone_id, dropoff_zone_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_zone_flows_mv
    TO mv_zone_flows
AS
SELECT toStartOfHour(started_at) AS hour,
       pickup_zone_id,
       dropoff_zone_id,
       count()                   AS trips_count
FROM fact_trips
GROUP BY hour, pickup_zone_id, dropoff_zone_id;