
    
    

select
    vehicle_key as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."dim_vehicle"
where vehicle_key is not null
group by vehicle_key
having count(*) > 1


