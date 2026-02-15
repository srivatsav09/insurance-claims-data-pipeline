
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select policy_id
from "insurance_warehouse"."public_staging"."stg_policyholders"
where policy_id is null



  
  
      
    ) dbt_internal_test