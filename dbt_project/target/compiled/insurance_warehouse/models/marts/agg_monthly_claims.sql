with claims as (
    select * from "insurance_warehouse"."public_intermediate"."int_claims_enriched"
)

select
    claim_month_start as month,
    count(*) as total_claims,
    round(avg(claim_amount), 2) as avg_claim_amount,
    round(avg(total_claim_value), 2) as avg_total_claim_value,
    sum(claim_amount) as total_claim_amount,
    round(
        count(*) filter (where claim_status = 'Approved')::numeric / nullif(count(*), 0) * 100, 2
    ) as approval_rate_pct,
    round(
        count(*) filter (where claim_status = 'Denied')::numeric / nullif(count(*), 0) * 100, 2
    ) as denial_rate_pct,
    round(
        count(*) filter (where fraud_flag = true)::numeric / nullif(count(*), 0) * 100, 2
    ) as fraud_rate_pct,
    count(*) filter (where claim_type = 'Collision') as collision_claims,
    count(*) filter (where claim_type = 'Theft') as theft_claims,
    count(*) filter (where claim_type = 'Liability') as liability_claims,
    count(*) filter (where claim_type = 'Comprehensive') as comprehensive_claims,
    count(distinct policy_id) as unique_policies
from claims
group by claim_month_start
order by claim_month_start