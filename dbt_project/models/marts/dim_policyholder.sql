with policyholders as (
    select * from {{ ref('stg_policyholders') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['policy_id']) }} as policyholder_key,
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
