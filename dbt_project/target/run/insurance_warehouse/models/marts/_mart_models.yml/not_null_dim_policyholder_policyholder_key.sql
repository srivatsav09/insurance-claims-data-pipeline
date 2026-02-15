
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select policyholder_key
from "insurance_warehouse"."public_marts"."dim_policyholder"
where policyholder_key is null



  
  
      
    ) dbt_internal_test