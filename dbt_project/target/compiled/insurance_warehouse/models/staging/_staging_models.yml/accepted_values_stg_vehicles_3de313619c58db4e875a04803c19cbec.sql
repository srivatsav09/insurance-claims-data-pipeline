
    
    

with all_values as (

    select
        fuel_type as value_field,
        count(*) as n_records

    from "insurance_warehouse"."public_staging"."stg_vehicles"
    group by fuel_type

)

select *
from all_values
where value_field not in (
    'Gasoline','Diesel','Hybrid','Electric'
)


