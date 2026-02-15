
    
    

select
    state as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."dim_region"
where state is not null
group by state
having count(*) > 1


