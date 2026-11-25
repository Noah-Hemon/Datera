"""CTP 2 - Exercise 4 STARTER: replay the 'cents' incident.
A naive suite (not null / unique / allowed values) PASSES on payments_batch_2.csv although every amount is 100x too big.
Only value-range and distribution expectations catch it.
"""
import pandas as pd
import great_expectations as gx

KIT = "../shopfast-kit/data/"
files = {"payments (history)": KIT + "payments.csv", "payments_batch_2 (new)": "payments_batch_2.csv"}

# Look at the amounts BEFORE choosing thresholds (history vs new batch), then adjust the numbers in "smart"
for label, path in files.items():
    print(f"\n{label}: amount\n", pd.to_numeric(pd.read_csv(path, dtype=str)["amount"]).describe())
    print(pd.read_csv(path, dtype=str)["amount"].head(5).tolist())

context = gx.get_context(mode="file")
source = context.data_sources.add_or_update_pandas("shopfast_payments")
asset = source.add_dataframe_asset(name="payments")
batch_def = asset.add_batch_definition_whole_dataframe("whole")
E = gx.expectations

naive = [E.ExpectColumnValuesToNotBeNull(column="payment_id"), E.ExpectColumnValuesToBeUnique(column="payment_id"),
         E.ExpectColumnValuesToNotBeNull(column="amount"), E.ExpectColumnValuesToBeInSet(column="currency", value_set=["EUR"]),
         E.ExpectColumnValuesToBeInSet(column="method", value_set=["card", "paypal", "apple_pay", "bank_transfer"])]
smart = naive + [
    # TODO: add 2 to 4 expectations that would have caught the cents incident.
    # Ideas: a range on each amount, a range on the mean or median, a regex on the text value (column "amount_txt").

    # 1. range on each amount: strictly positive, and below a sensible maximum for ONE payment (ADJUST: a bit above the history max)
    E.ExpectColumnValuesToBeBetween(column="amount", min_value=0, strict_min=True, max_value=2000),
    # 2. median in the normal euro range (ADJUST around the history median): in cents it is ~100x higher
    E.ExpectColumnMedianToBeBetween(column="amount", min_value=10, max_value=300),
    # 3. mean in the normal euro range (ADJUST around the history mean): an average is robust to a few outliers going unnoticed one by one
    E.ExpectColumnMeanToBeBetween(column="amount", min_value=10, max_value=400),
    # 4. decimals: euros are written like 12.34, cents are whole numbers like 1234 (CHECK the printed samples above first)
    E.ExpectColumnValuesToMatchRegex(column="amount_txt", regex=r"^\d+\.\d{1,2}$"),
]

def run(name, expectations, df):
    suite = context.suites.add_or_update(gx.ExpectationSuite(name=name))
    for e in expectations: suite.add_expectation(e.copy() if hasattr(e, "copy") else e)
    suite.save()
    return batch_def.get_batch(batch_parameters={"dataframe": df}).validate(suite)

for label, path in files.items():
    df = pd.read_csv(path, dtype=str); df["amount_txt"] = df["amount"]; df["amount"] = pd.to_numeric(df["amount"])
    for suite_name, exps in [("naive_payments", naive), ("smart_payments", smart)]:
        res = run(suite_name, exps, df)
        failed = [r.expectation_config.type for r in res.results if not r.success]
        print(f"{label:<24} {suite_name:<15} success={res.success}  failed={failed}")