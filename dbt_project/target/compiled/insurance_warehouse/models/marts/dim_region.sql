with states as (
    select distinct
        incident_state as state
    from "insurance_warehouse"."public_staging"."stg_claims"
    where incident_state is not null
),

mapped as (
    select
        md5(cast(coalesce(cast(state as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as region_key,
        state,
        case
            when state in ('NY', 'NJ', 'PA', 'CT', 'MA', 'NH', 'VT', 'ME', 'RI') then 'Northeast'
            when state in ('TX', 'FL', 'GA', 'NC', 'VA', 'TN', 'AL', 'SC', 'LA', 'KY') then 'South'
            when state in ('IL', 'OH', 'MI', 'IN', 'WI', 'MN', 'MO', 'IA', 'KS', 'NE') then 'Midwest'
            when state in ('CA', 'WA', 'OR', 'CO', 'AZ', 'NV', 'UT', 'ID', 'NM', 'MT') then 'West'
            else 'Other'
        end as region_name
    from states
)

select * from mapped