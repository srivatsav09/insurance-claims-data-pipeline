
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    policyholder_key as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."dim_policyholder"
where policyholder_key is not null
group by policyholder_key
having count(*) > 1



  
  
      
    ) dbt_internal_test