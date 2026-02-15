with source as (
    select * from "insurance_warehouse"."raw"."vehicles"
),

cleaned as (
    select
        vehicle_id,
        policy_id,
        trim(make) as make,
        trim(model) as model,
        year as vehicle_year,
        vehicle_age,
        case
            when vehicle_age <= 2 then 'New (0-2)'
            when vehicle_age <= 5 then 'Recent (3-5)'
            when vehicle_age <= 10 then 'Mid-age (6-10)'
            else 'Old (11+)'
        end as vehicle_age_bucket,
        trim(fuel_type) as fuel_type,
        annual_mileage,
        case
            when annual_mileage < 8000 then 'Low'
            when annual_mileage < 15000 then 'Average'
            else 'High'
        end as mileage_category
    from source
)

select * from cleaned