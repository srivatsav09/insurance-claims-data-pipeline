with policyholders as (
    select * from "insurance_warehouse"."public_staging"."stg_policyholders"
)

select
    md5(cast(coalesce(cast(policy_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as policyholder_key,
    policy_id,
    full_name,
    gender,
    age,
    age_group,
    income_bracket,
    education,
    occupation,
    marital_status,
    policy_start_date,
    policy_end_date,
    policy_tenure_months,
    premium_amount,
    deductible,
    region_code,
    state
from policyholders