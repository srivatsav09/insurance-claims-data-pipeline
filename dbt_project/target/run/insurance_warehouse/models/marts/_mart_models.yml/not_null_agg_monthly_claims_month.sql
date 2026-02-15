
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select month
from "insurance_warehouse"."public_marts"."agg_monthly_claims"
where month is null



  
  
      
    ) dbt_internal_test