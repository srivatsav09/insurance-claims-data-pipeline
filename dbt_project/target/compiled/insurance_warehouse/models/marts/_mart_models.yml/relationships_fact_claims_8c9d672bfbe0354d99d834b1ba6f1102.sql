
    
    

with child as (
    select policyholder_key as from_field
    from "insurance_warehouse"."public_marts"."fact_claims"
    where policyholder_key is not null
),

parent as (
    select policyholder_key as to_field
    from "insurance_warehouse"."public_marts"."dim_policyholder"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


