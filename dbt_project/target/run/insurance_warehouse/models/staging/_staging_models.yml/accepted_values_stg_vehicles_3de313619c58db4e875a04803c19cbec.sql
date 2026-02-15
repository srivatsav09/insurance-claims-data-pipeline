
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        fuel_type as value_field,
        count(*) as n_records

    from "insurance_warehouse"."public_staging"."stg_vehicles"
    group by fuel_type

)

select *
from all_values
where value_field not in (
    'Gasoline','Diesel','Hybrid','Electric'
)



  
  
      
    ) dbt_internal_test