
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    policy_id as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."dim_policyholder"
where policy_id is not null
group by policy_id
having count(*) > 1



  
  
      
    ) dbt_internal_test