{% docs gross_revenue %}
**Gross revenue (EUR)** — total amount paid by the customer for an order, VAT included, shipping included, before refunds.
Owner: Head of Sales · Steward: Karim Benali · Status: approved (2026-11-10)
{% enddocs %}

{# TODO (Exercise 3): add the terms net_revenue, active_customer, churned_customer, order, customer #}

{% docs net_revenue %}
**Net revenue (EUR)**: what the customer paid for an order after refunds, **excluding VAT**, shipping fees included.
Formula: `(gross_revenue_eur - refunded_eur) / 1.20`, rounded to 2 decimals.
Example: 120.00 EUR paid incl. VAT, 24.00 EUR refunded → (120 - 24) / 1.20 = **80.00 EUR**.
Sales commissions use gross revenue minus refunds (VAT included), which must be shown under that name, never as "net revenue".
Owner: Head of Finance · Steward: Karim Benali · Status: approved (2026-11-25)
{% enddocs %}

{% docs active_customer %}
**Active customer**: a customer account with at least one **non-cancelled** order in the **last 12 months** (rolling, from the reporting date).
Example: on 2026-11-25, an account whose last non-cancelled order was on 2026-01-15 is active.
Sales' 6-month view is a separate metric, **recently active customer (6 months)**: same rules, 6-month window. It must never be labelled "active customer".
Owner: Head of Finance · Steward: Karim Benali · Status: approved (2026-11-25)
{% enddocs %}

{% docs churned_customer %}
**Churned customer**: a customer account that has ordered before but has **no non-cancelled order in the last 12 months**. It is the opposite of an active customer.
Accounts that never placed a non-cancelled order are neither active nor churned.
Owner: Head of Finance · Steward: Karim Benali · Status: approved (2026-11-25)
{% enddocs %}

{% docs customer %}
**Customer**: a customer account registered on ShopFast, identified by `customer_id`.
A customer is an account, not a person: one person may have several accounts (duplicate emails).
Owner: Head of Sales · Steward: Karim Benali · Status: approved (2026-11-25)
{% enddocs %}

{% docs order %}
**Order**: a purchase placed by a customer, identified by `order_id`, whatever its status (pending, shipped, delivered, cancelled, returned).
Cancelled orders are still orders, but they never count towards active or churned customers.
Owner: Head of Sales · Steward: Karim Benali · Status: approved (2026-11-25)
{% enddocs %}
