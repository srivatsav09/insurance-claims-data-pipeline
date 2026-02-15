
    
    

select
    claim_key as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."fact_claims"
where claim_key is not null
group by claim_key
having count(*) > 1


