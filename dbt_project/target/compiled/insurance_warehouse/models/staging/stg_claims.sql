with source as (
    select * from "insurance_warehouse"."raw"."claims"
),

cleaned as (
    select
        claim_id,
        policy_id,
        vehicle_id,
        claim_date::date as claim_date,
        claim_amount,
        trim(claim_type) as claim_type,
        trim(status) as claim_status,
        fraud_flag,
        trim(incident_city) as incident_city,
        trim(incident_state) as incident_state,
        police_report_filed,
        witnesses,
        coalesce(injury_claim, 0) as injury_claim,
        coalesce(property_claim, 0) as property_claim,
        claim_amount + coalesce(injury_claim, 0) + coalesce(property_claim, 0) as total_claim_value,
        extract(year from claim_date::date) as claim_year,
        extract(month from claim_date::date) as claim_month,
        date_trunc('month', claim_date::date)::date as claim_month_start
    from source
)

select * from cleaned