
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select policy_id
from "insurance_warehouse"."public_marts"."dim_policyholder"
where policy_id is null



  
  
      
    ) dbt_internal_test