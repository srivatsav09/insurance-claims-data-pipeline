
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select state
from "insurance_warehouse"."public_marts"."dim_region"
where state is null



  
  
      
    ) dbt_internal_test