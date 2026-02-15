with claims as (
    select * from {{ ref('stg_claims') }}
),

policyholders as (
    select * from {{ ref('stg_policyholders') }}
),

vehicles as (
    select * from {{ ref('stg_vehicles') }}
),

enriched as (
    select
        c.claim_id,
        c.policy_id,
        c.vehicle_id,
        c.claim_date,
        c.claim_year,
        c.claim_month,
        c.claim_month_start,
        c.claim_amount,
        c.injury_claim,
        c.property_claim,
        c.total_claim_value,
        c.claim_type,
        c.claim_status,
        c.fraud_flag,
        c.incident_city,
        c.incident_state,
        c.police_report_filed,
        c.witnesses,

        -- Policyholder fields
        p.full_name,
        p.gender,
        p.age,
        p.age_group,
        p.income_bracket,
        p.education,
        p.occupation,
        p.marital_status,
        p.premium_amount,
        p.deductible,
        p.policy_tenure_months,
        p.region_code,
        p.state as policyholder_state,

        -- Vehicle fields
        v.make,
        v.model,
        v.vehicle_year,
        v.vehicle_age,
        v.vehicle_age_bucket,
        v.fuel_type,
        v.annual_mileage,
        v.mileage_category,

        -- Derived metrics
        case
            when c.claim_amount > p.deductible then c.claim_amount - p.deductible
            else 0
        end as net_claim_after_deductible,
        case
            when p.premium_amount > 0 then round(c.claim_amount / p.premium_amount, 2)
            else null
        end as claim_to_premium_ratio

    from claims c
    left join policyholders p on c.policy_id = p.policy_id
    left join vehicles v on c.vehicle_id = v.vehicle_id
)

select * from enriched
