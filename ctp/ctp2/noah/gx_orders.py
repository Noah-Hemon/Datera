"""CTP 2 - Exercise 3 STARTER: build an expectation suite for ShopFast orders (GX Core 1.x).
Run from the 02_CTP2 folder:  python gx_orders_starter.py
"""
import pandas as pd
import great_expectations as gx

KIT = "../shopfast-kit/data/"   # adapt if your kit is elsewhere
orders = pd.read_csv(KIT + "orders.csv", dtype=str)
customers = pd.read_csv(KIT + "customers.csv", dtype=str)
orders["total_amount_eur"] = pd.to_numeric(orders["total_amount_eur"], errors="coerce")
orders["order_date_dt"] = pd.to_datetime(orders["order_date"], format="%Y-%m-%d", errors="coerce")  # typed copy for range checks
TODAY = pd.Timestamp.today().normalize().to_pydatetime()   # upper bound for "no future orders"

context = gx.get_context(mode="file")                       # creates ./gx/ (config + Data Docs)
source = context.data_sources.add_or_update_pandas("shopfast")
asset = source.add_dataframe_asset(name="orders")
batch_def = asset.add_batch_definition_whole_dataframe("all_orders")

suite = context.suites.add_or_update(gx.ExpectationSuite(name="orders_suite"))
E = gx.expectations
for e in [
    E.ExpectTableRowCountToBeBetween(min_value=1000, max_value=100000),
    E.ExpectColumnValuesToNotBeNull(column="order_id"),
    E.ExpectColumnValuesToBeUnique(column="order_id"),
    # TODO 1: customer_id must not be null
    #   WHY: an order without a customer cannot be invoiced, shipped or counted in customer KPIs
    E.ExpectColumnValuesToNotBeNull(column="customer_id"),

    # TODO 2: customer_id must exist in customers (foreign-key / referential-integrity check)
    #   WHY: orphan orders break joins - revenue per customer/segment silently drops them (policy: HIGH, quarantine)
    #   dropna() so a blank customer row can't make NaN a "valid" key; nulls are already caught by TODO 1
    E.ExpectColumnValuesToBeInSet(column="customer_id",
                                  value_set=sorted(customers["customer_id"].dropna().unique())),

    # TODO 3: order_date must not be null and must look like YYYY-MM-DD (ExpectColumnValuesToMatchRegex)
    #   WHY: without a valid date the order cannot be placed in a reporting period (daily/monthly revenue)
    #   GX skips nulls in the regex check, so the not-null expectation is needed separately
    E.ExpectColumnValuesToNotBeNull(column="order_date"),
    E.ExpectColumnValuesToMatchRegex(column="order_date", regex=r"^\d{4}-\d{2}-\d{2}$"),

    # TODO 4: no order in the future (ExpectColumnValuesToBeBetween on column "order_date_dt")
    #   WHY: an order cannot be placed tomorrow - a future date is an entry error and inflates future periods
    E.ExpectColumnValuesToBeBetween(column="order_date_dt", max_value=TODAY),

    # TODO 5: status only in: pending, shipped, delivered, cancelled, returned
    #   WHY: these 5 states are the order lifecycle the business tracks (fulfilment and return rates);
    #   any other spelling is not counted in the right bucket (policy: MEDIUM, fix in transform)
    #   exact match on purpose: "Delivered", "SHIPPED", "delivered " and "canceled" must be flagged
    E.ExpectColumnValuesToBeInSet(column="status",
                                  value_set=["pending", "shipped", "delivered", "cancelled", "returned"]),

    # TODO 6: channel and shipping_country only in their allowed values (observed in orders.csv)
    #   WHY channel: the 3 sales channels ShopFast operates - a new value means an unknown channel to review
    #   WHY country: ShopFast only ships to FR, BE, DE, ES (same list as the customers country rule)
    E.ExpectColumnValuesToBeInSet(column="channel", value_set=["web", "mobile_app", "marketplace"]),
    E.ExpectColumnValuesToBeInSet(column="shipping_country", value_set=["FR", "BE", "DE", "ES"]),

    # TODO 7: total_amount_eur strictly positive and below a sensible maximum
    #   WHY: an order is a sale - 0 or negative is a refund/test order and distorts revenue;
    #   a huge amount usually means a unit error (e.g. x100, policy: CRITICAL)
    #   data: median ~184 EUR, p99 ~859 EUR, max ~1401 EUR -> 5000 EUR flags only clearly abnormal amounts
    E.ExpectColumnValuesToBeBetween(column="total_amount_eur", min_value=0, strict_min=True, max_value=5000),
]:
    suite.add_expectation(e)
suite.save()

vd = context.validation_definitions.add_or_update(gx.ValidationDefinition(name="orders_validation", data=batch_def, suite=suite))
checkpoint = context.checkpoints.add_or_update(gx.Checkpoint(name="orders_checkpoint", validation_definitions=[vd],
                                                             actions=[gx.checkpoint.UpdateDataDocsAction(name="docs")]))
result = checkpoint.run(batch_parameters={"dataframe": orders})

print("\nSuite passed:", result.success)
for vr in result.run_results.values():
    for r in vr.results:
        cfg = r.expectation_config
        print(f"{'PASS' if r.success else 'FAIL'}  {cfg.type:<45} {cfg.kwargs.get('column', ''):<18} unexpected={r.result.get('unexpected_count', '-')}")
print("\nOpen the report: gx/uncommitted/data_docs/local_site/index.html")
