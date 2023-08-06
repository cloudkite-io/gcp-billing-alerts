import os
from datetime import datetime, timedelta, date
from google.cloud import bigquery

from slack_notify import send_slack_message
from email_notify import send_email


def check_limits(
    source_bigquery_table_id,
    change_threshold,
    days_to_average,
    alert_metric,
):
    n_days_ago = datetime.strftime(
        datetime.utcnow() - timedelta(days=(days_to_average+1)), "%Y-%m-%d")

    # Construct a BigQuery client object.
    client = bigquery.Client()

    # Build query
    query = f"""
        SELECT DATE(usage_end_time) as usage_day, sku.id AS sku_id, sku.description AS sku_description, project.id as project, sum(CAST(cost AS NUMERIC)) as cost, max(currency) as currency 
        FROM `{source_bigquery_table_id}`
        WHERE usage_start_time >= '{n_days_ago}'
        GROUP BY usage_day, project, sku_id, sku_description ORDER BY usage_day
    """
    query_job = client.query(query)  # Make an API request.
    # Convert results into a Pandas DataFrame
    results_df = query_job.to_dataframe()

    if not results_df.empty and len(results_df) > 1:
        last_complete_day = date.today() - timedelta(1)
        currency = results_df.iloc[0].currency

        alert_msg = {
                        "title": f"GCP billing alerts for {last_complete_day}",
                        "billing_date": last_complete_day,
                        "slack_body": "",
                        "body_title": f"Below are the Project-SKUs that exceeded {days_to_average}-day {'average/max' if alert_metric == 'all' else alert_metric} on {last_complete_day}:"
                    }

        changes_list = []
        for group_id, sku_project_df in results_df.groupby(["sku_id", "project"]):
            sku_id = group_id[0]
            project_id = group_id[1]
            sku_project_df.reset_index(inplace=True)
            last_complete_day_df = sku_project_df[sku_project_df.usage_day == last_complete_day]
            if len(last_complete_day_df):
                last_complete_day_cost = sku_project_df[sku_project_df.usage_day == last_complete_day].cost.item()
                metric_df = sku_project_df[sku_project_df.usage_day < last_complete_day]
                if len(metric_df):
                    sku_description = metric_df.iloc[0].sku_description
                    if alert_metric in ["all", "mean"]:
                        average_cost = metric_df.cost.mean()
                        if last_complete_day_cost > average_cost:
                            change = last_complete_day_cost - average_cost
                            if average_cost:
                                perc_change = round(((change/average_cost)*100), 2)
                            else:
                                perc_change = "inf"
                            if change >= change_threshold:
                                changes_list.append({
                                    "project_id": project_id,
                                    "sku_id": sku_id,
                                    "sku_description": sku_description,
                                    "spend": round(last_complete_day_cost, 2),
                                    "change_type": "average",
                                    "change": round(change, 2),
                                    "perc_change": perc_change,
                                })
                    if alert_metric in ["all", "max"]:
                        max_cost = metric_df.cost.max()
                        if last_complete_day_cost > max_cost:
                            change = last_complete_day_cost - max_cost
                            if max_cost:
                                perc_change = round(((change/max_cost)*100), 2)
                            else:
                                perc_change = "inf"
                            if change >= change_threshold:
                                changes_list.append({
                                    "project_id": project_id,
                                    "sku_id": sku_id,
                                    "sku_description": sku_description,
                                    "spend": round(last_complete_day_cost, 2),
                                    "change_type": "max",
                                    "change": round(change, 2),
                                    "perc_change": perc_change,
                                })
        changes_list = sorted(changes_list, key=lambda d: d['change'])

        if (len(results_df.usage_day.unique()) - 2) < days_to_average:
            alert_msg["pretext"] = f"Only {len(results_df.usage_day.unique() - 2)}/{days_to_average} days of data is available in BigQuery."
        
        if len(changes_list):
            for change in changes_list:
                alert_msg["slack_body"] += (f"- '{change['sku_description']}' exceeded the last *{days_to_average}-day*" + 
                    f" {change['change_type']} in *{change['project_id']}* by *{change['perc_change']}%* ({currency} {change['change']} more)\n")
            
            send_slack_message(alert_msg)
            send_email(changes_list, days_to_average, currency, alert_msg)
        else:
            print(f"No billing limits have been exceeded on {last_complete_day}.")
    else:
        print("The results returned by your Query parameters aren't sufficient for analysis!")


def main():
    source_bigquery_table_id = os.environ['SOURCE_BIGQUERY_TABLE_ID']
    days_to_average = os.getenv('DAYS_TO_AVERAGE', 30)
    change_threshold = os.getenv('CHANGE_THRESHOLD', 0)
    alert_metric = os.getenv('ALERT_METRIC', "all")
    print(f"Checking GCP billing limits:\n\
            source_bigquery_table_id: {source_bigquery_table_id}\n\
            days_to_average: {days_to_average}\n\
            change_threshold: {change_threshold}\n\
            alert_metric: {alert_metric}\n\
            ")
    check_limits(
        source_bigquery_table_id,
        int(change_threshold),
        int(days_to_average),
        alert_metric.lower(),
    )


if __name__ == '__main__':
    main()
