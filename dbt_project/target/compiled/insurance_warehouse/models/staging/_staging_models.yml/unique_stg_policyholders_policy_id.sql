
    
    

select
    policy_id as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_staging"."stg_policyholders"
where policy_id is not null
group by policy_id
having count(*) > 1


