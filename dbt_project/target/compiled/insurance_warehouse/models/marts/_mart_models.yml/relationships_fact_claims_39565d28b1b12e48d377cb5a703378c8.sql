
    
    

with child as (
    select vehicle_key as from_field
    from "insurance_warehouse"."public_marts"."fact_claims"
    where vehicle_key is not null
),

parent as (
    select vehicle_key as to_field
    from "insurance_warehouse"."public_marts"."dim_vehicle"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


