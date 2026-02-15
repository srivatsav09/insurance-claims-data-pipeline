
    
    

select
    month as unique_field,
    count(*) as n_records

from "insurance_warehouse"."public_marts"."agg_monthly_claims"
where month is not null
group by month
having count(*) > 1


