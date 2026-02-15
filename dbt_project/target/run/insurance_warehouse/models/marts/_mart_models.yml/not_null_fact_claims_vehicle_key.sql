
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select vehicle_key
from "insurance_warehouse"."public_marts"."fact_claims"
where vehicle_key is null



  
  
      
    ) dbt_internal_test