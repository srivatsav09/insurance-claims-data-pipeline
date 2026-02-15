
    
    

with all_values as (

    select
        claim_type as value_field,
        count(*) as n_records

    from "insurance_warehouse"."public_staging"."stg_claims"
    group by claim_type

)

select *
from all_values
where value_field not in (
    'Collision','Theft','Liability','Comprehensive'
)


