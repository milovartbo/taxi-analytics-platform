USE taxi;

CREATE TABLE IF NOT EXISTS fact_trips
(
    trip_id          UUID,
    started_at       DateTime,
    driver_id        UInt32,
    city_id          UInt8,
    pickup_zone_id   UInt16,
    dropoff_zone_id  UInt16,
    service_type_id  UInt8,
    status_id        UInt8,
    distance_km      Float32,
    duration_min     Float32,
    surge            Float32,
    fare             Float32,
    tip              Float32,
    trip_rating      UInt8,
    is_anomaly       UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(started_at)
ORDER BY (started_at, city_id, driver_id, trip_id);