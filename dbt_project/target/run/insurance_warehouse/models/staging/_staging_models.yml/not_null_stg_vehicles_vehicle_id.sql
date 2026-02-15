
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select vehicle_id
from "insurance_warehouse"."public_staging"."stg_vehicles"
where vehicle_id is null



  
  
      
    ) dbt_internal_test