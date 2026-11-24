USE taxi;

CREATE TABLE IF NOT EXISTS dim_cities
(
    city_id UInt8,
    city_name String,
    tz_name String,
    traffic_factor Float32,
    demand_weight Float32
)
ENGINE = MergeTree
ORDER BY city_id;

CREATE TABLE IF NOT EXISTS dim_zones
(
    zone_id UInt16,
    city_id UInt8,
    zone_name String,
    zone_type String
)
ENGINE = MergeTree
ORDER BY zone_id;

CREATE TABLE IF NOT EXISTS dim_drivers
(
    driver_id      UInt32,
    full_name      String,
    home_city_id   UInt8,
    vehicle_class  String,
    driver_rating  Float32,
    registered_at  DateTime
)
ENGINE = MergeTree
ORDER BY driver_id;

CREATE TABLE IF NOT EXISTS dim_service_types
(
    service_type_id UInt8,
    service_name    String,
    category        String,  -- passenger / delivery
    base_fare       Float32,
    per_km          Float32,
    per_min         Float32
)
ENGINE = MergeTree
ORDER BY service_type_id;

CREATE TABLE IF NOT EXISTS dim_trip_statuses
(
    status_id   UInt8,
    status_name String
)
ENGINE = MergeTree
ORDER BY status_id;