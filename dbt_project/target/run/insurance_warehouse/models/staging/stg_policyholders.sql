
  create view "insurance_warehouse"."public_staging"."stg_policyholders__dbt_tmp"
    
    
  as (
    with source as (
    select * from "insurance_warehouse"."raw"."policyholders"
),

cleaned as (
    select
        policy_id,
        trim(first_name) || ' ' || trim(last_name) as full_name,
        trim(gender) as gender,
        age,
        case
            when age < 25 then '18-24'
            when age < 35 then '25-34'
            when age < 45 then '35-44'
            when age < 55 then '45-54'
            when age < 65 then '55-64'
            else '65+'
        end as age_group,
        trim(income_bracket) as income_bracket,
        trim(education) as education,
        trim(occupation) as occupation,
        trim(marital_status) as marital_status,
        policy_start_date::date as policy_start_date,
        policy_end_date::date as policy_end_date,
        (policy_end_date::date - policy_start_date::date) / 30 as policy_tenure_months,
        premium_amount,
        deductible,
        trim(region_code) as region_code,
        trim(state) as state
    from source
)

select * from cleaned
  );