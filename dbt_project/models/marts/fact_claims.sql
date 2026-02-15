with enriched as (
    select * from {{ ref('int_claims_enriched') }}
),

dim_policyholder as (
    select * from {{ ref('dim_policyholder') }}
),

dim_vehicle as (
    select * from {{ ref('dim_vehicle') }}
),

dim_region as (
    select * from {{ ref('dim_region') }}
),

fact as (
    select
        {{ dbt_utils.generate_surrogate_key(['e.claim_id']) }} as claim_key,
        dp.policyholder_key,
        dv.vehicle_key,
        dr.region_key,
        e.claim_id,
        e.claim_date,
        e.claim_year,
        e.claim_month,
        e.claim_month_start,
        e.claim_amount,
        e.injury_claim,
        e.property_claim,
        e.total_claim_value,
        e.net_claim_after_deductible,
        e.claim_to_premium_ratio,
        e.claim_type,
        e.claim_status,
        e.fraud_flag,
        e.police_report_filed,
        e.witnesses
    from enriched e
    left join dim_policyholder dp on e.policy_id = dp.policy_id
    left join dim_vehicle dv on e.vehicle_id = dv.vehicle_id
    left join dim_region dr on e.incident_state = dr.state
)

select * from fact
