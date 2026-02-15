
    
    

select
    policyholder_key as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."dim_policyholder"
where policyholder_key is not null
group by policyholder_key
having count(*) > 1


