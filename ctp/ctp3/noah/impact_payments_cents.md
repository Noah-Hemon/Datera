# Impact note: `payments.amount` switching from euros to cents

1. **What breaks:** `stg_payments` → `fct_orders` (`refunded_eur`, `net_revenue_eur` 100× wrong) → `dim_customers` (`lifetime_net_revenue_eur`) → all 3 exposures: Sales dashboard, Finance monthly revenue report, churn-prediction model.
2. **Owners to warn:** Sara Martin (Sales dashboard), Paul Girard (Finance monthly report), Data Science team (churn model); steward Karim Benali must update `stg_payments` (divide by 100) and the column description.
3. **Test to add:** reconciliation test on `fct_orders`: sum of captured payments per order = `total_amount_eur` (± 0.01). Any ×100 drift fails the build before it reaches a dashboard. Today no downstream test checks amounts.
4. **Who approves:** Paul Girard (Head of Finance), the owner of `payments`, after Sara Martin confirms the Sales dashboard is ready. No go-live without both approvals.
5. **Rollout:** announce the date ≥ 1 week ahead, ship the dbt fix and the test in the same release as the source change, then check the first day's revenue against the previous day.
