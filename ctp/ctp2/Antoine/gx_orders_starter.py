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

# Look at the data BEFORE choosing allowed values (run once, then adjust the sets below)
for col in ["status", "channel", "shipping_country"]:
    print(f"\n{col}:\n", orders[col].value_counts(dropna=False))
print("\ntotal_amount_eur:\n", orders["total_amount_eur"].describe())

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
    E.ExpectColumnValuesToNotBeNull(column="customer_id"),
    # TODO 2: customer_id must exist in customers (hint: ExpectColumnValuesToBeInSet with set(customers["customer_id"]))
    E.ExpectColumnValuesToBeInSet(column="customer_id", value_set=list(customers["customer_id"].dropna().unique())),
    # TODO 3: order_date must not be null and must look like YYYY-MM-DD (ExpectColumnValuesToMatchRegex)
    E.ExpectColumnValuesToNotBeNull(column="order_date"),
    E.ExpectColumnValuesToMatchRegex(column="order_date", regex=r"^\d{4}-\d{2}-\d{2}$"),
    # TODO 4: no order in the future (ExpectColumnValuesToBeBetween on column "order_date_dt")
    E.ExpectColumnValuesToBeBetween(column="order_date_dt", max_value=pd.Timestamp.now().to_pydatetime()),
    # TODO 5: status only in: pending, shipped, delivered, cancelled, returned
    E.ExpectColumnValuesToBeInSet(column="status", value_set=["pending", "shipped", "delivered", "cancelled", "returned"]),
    # TODO 6: channel and shipping_country only in their allowed values (look at the data first!)
    E.ExpectColumnValuesToBeInSet(column="channel", value_set=["web", "mobile", "marketplace", "store"]),
    E.ExpectColumnValuesToBeInSet(column="shipping_country", value_set=["FR", "DE", "ES", "BE"]),
    # TODO 7: total_amount_eur strictly positive and below a sensible maximum
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


# ---------------------------------------------------------------
# Add the GX results to the scorecard (one row per expectation)
# ---------------------------------------------------------------
SCORECARD = "quality_scorecard_template.csv"  
TAG = "GX orders: "                            

# (expectation type, column) -> (dimension, rule in plain words, severity, who fixes it)  -> edit freely
RULES = {
    ("expect_table_row_count_to_be_between", ""):        ("Completeness", "orders table has between 1,000 and 100,000 rows", "high", "Custodian"),
    ("expect_column_values_to_not_be_null", "order_id"): ("Completeness", "order_id is filled", "high", "Custodian"),
    ("expect_column_values_to_be_unique", "order_id"):   ("Uniqueness", "order_id is unique", "high", "Custodian"),
    ("expect_column_values_to_not_be_null", "customer_id"): ("Completeness", "customer_id is filled", "high", "Steward"),
    ("expect_column_values_to_be_in_set", "customer_id"):   ("Consistency", "customer_id exists in customers", "high", "Steward"),
    ("expect_column_values_to_not_be_null", "order_date"):  ("Completeness", "order_date is filled", "medium", "Steward"),
    ("expect_column_values_to_match_regex", "order_date"):  ("Validity", "order_date is YYYY-MM-DD", "medium", "Custodian"),
    ("expect_column_values_to_be_between", "order_date_dt"): ("Accuracy", "no order dated in the future", "medium", "Owner"),
    ("expect_column_values_to_be_in_set", "status"):           ("Validity", "status is pending/shipped/delivered/cancelled/returned", "medium", "Steward"),
    ("expect_column_values_to_be_in_set", "channel"):          ("Validity", "channel is in the allowed list", "low", "Steward"),
    ("expect_column_values_to_be_in_set", "shipping_country"): ("Consistency", "shipping_country is FR, DE, ES or BE", "medium", "Custodian"),
    ("expect_column_values_to_be_between", "total_amount_eur"): ("Accuracy", "total_amount_eur is > 0 and below the maximum", "high", "Owner"),
}

def add_results_to_scorecard(result, total_rows, path=SCORECARD):
    """Append one row per expectation (pass or fail) to the scorecard; replaces rows added by a previous run."""
    try:
        card = pd.read_csv(path, dtype=str)
    except FileNotFoundError:
        card = pd.DataFrame()
    if "how_you_measured_it" in card.columns:  
        card = card[~card["how_you_measured_it"].fillna("").str.startswith(TAG)]

    new_rows = []
    for vr in result.run_results.values():
        for r in vr.results:
            cfg = r.expectation_config
            col = cfg.kwargs.get("column", "")
            dimension, rule, severity, owner = RULES.get((cfg.type, col), ("", cfg.type, "", ""))
            failing = r.result.get("unexpected_count")
            if failing is None:                        
                failing = 0 if r.success else total_rows
            failing = int(failing)
            new_rows.append({
                "dimension": dimension,
                "rule_in_plain_words": rule,
                "column": col,
                "how_you_measured_it": TAG + cfg.type,
                "failing_rows": failing,
                "total_rows": total_rows,
                "score_pct": round(100 * (1 - failing / total_rows), 2),
                "severity_high_medium_low": severity,
                "who_should_fix_owner_steward_custodian": owner,
            })

    card = pd.concat([card, pd.DataFrame(new_rows)], ignore_index=True)
    card.to_csv(path, index=False)
    print(f"Scorecard updated: {len(new_rows)} orders rules written to {path} ({len(card)} rows in total)")

add_results_to_scorecard(result, len(orders))