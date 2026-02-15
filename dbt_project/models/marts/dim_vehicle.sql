with vehicles as (
    select * from {{ ref('stg_vehicles') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['vehicle_id']) }} as vehicle_key,
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
