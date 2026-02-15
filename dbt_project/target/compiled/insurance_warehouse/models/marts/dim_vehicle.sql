with vehicles as (
    select * from "insurance_warehouse"."public_staging"."stg_vehicles"
)

select
    md5(cast(coalesce(cast(vehicle_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as vehicle_key,
    vehicle_id,
    policy_id,
    make,
    model,
    vehicle_year,
    vehicle_age,
    vehicle_age_bucket,
    fuel_type,
    annual_mileage,
    mileage_category
from vehicles