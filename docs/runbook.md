# Operations Runbook

## Run the Pipeline

From the repository root:

```bash
make run
```

The command loads `data/raw/orders.csv`, writes the warehouse to
`warehouse/retail_analytics.db`, and prints a sales summary.

## Interpret Results

The CLI reports one of three states:

- `completed`: the source was processed successfully;
- `skipped`: the exact source checksum previously completed;
- an error and nonzero exit: the batch-level contract or infrastructure failed.

Rejected records appear in `data/rejected/orders.csv` with a
`rejection_reason`. The run audit is queryable with:

```sql
SELECT *
FROM etl_runs
ORDER BY started_at DESC;
```

## Reprocess a File

Use `--force` when a previously loaded source must be intentionally replayed:

```bash
./scripts/run_pipeline.sh --force
```

Natural-key upserts make this safe for existing orders.

## Recover from Failure

1. Review the CLI error and the latest failed row in `etl_runs`.
2. Correct the source schema, data, configuration, or filesystem issue.
3. Run the pipeline again. Failed checksums are not treated as completed.
4. Confirm row counts and analytics views.

## Useful Queries

```sql
SELECT * FROM vw_daily_sales ORDER BY order_date;
SELECT * FROM vw_category_performance ORDER BY revenue DESC;
SELECT * FROM vw_customer_lifetime_value ORDER BY lifetime_value DESC;
```

