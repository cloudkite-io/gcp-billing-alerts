import os
from datetime import datetime, timedelta, date
from google.cloud import bigquery

from slack_notify import send_slack_message
from email_notify import send_email


def check_limits(
    source_bigquery_table_id,
    change_threshold,
    days_to_average,
):
    n_days_ago = datetime.strftime(
        datetime.utcnow() - timedelta(days=int(days_to_average + 1)), "%Y-%m-%d")

    # Construct a BigQuery client object.
    client = bigquery.Client()

    # Build query
    query = f"""
        SELECT DATE(usage_end_time) as usage_day, sku.id AS sku_id, sku.description AS sku_description, project.id as project, sum(cost) as cost, max(currency) as currency 
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

        slack_msg = {
            "title": f"GCP billing summary for {last_complete_day}",
            "billing_date": last_complete_day,
            "body": ""
            }

        changes_list = []
        for group_id, sku_project_df in results_df.groupby(["sku_id", "project"]):
            sku_id = group_id[0]
            project_id = group_id[1]
            sku_project_df.reset_index(inplace=True)
            last_complete_day_df = sku_project_df[sku_project_df.usage_day == last_complete_day]
            if len(last_complete_day_df):
                last_complete_day_cost = sku_project_df[sku_project_df.usage_day == last_complete_day].cost.item()
                average_cost_df = sku_project_df[sku_project_df.usage_day < last_complete_day]
                if len(average_cost_df):
                    average_cost = average_cost_df.cost.mean()
                    max_cost = average_cost_df.cost.max()
                    
                    sku_description = average_cost_df.iloc[0].sku_description
                    if last_complete_day_cost > average_cost:
                        change = last_complete_day_cost - average_cost
                        perc_change = (change/average_cost)*100
                        if change >= change_threshold:
                            changes_list.append({
                                "project_id": project_id,
                                "sku_id": sku_id,
                                "sku_description": sku_description,
                                "change": round(change, 2),
                                "perc_change": round(perc_change, 2),
                                "change_type": "average",
                            })
                    if last_complete_day_cost > max_cost:
                        change = last_complete_day_cost - max_cost
                        perc_change = (change/max_cost)*100
                        if change >= change_threshold:
                            changes_list.append({
                                "project_id": project_id,
                                "sku_id": sku_id,
                                "sku_description": sku_description,
                                "change": round(change, 2),
                                "perc_change": round(perc_change, 2),
                                "change_type": "max",
                            })
        changes_list = sorted(changes_list, key=lambda d: d['change'])

        if len(results_df.usage_day.unique() - 2) < int(days_to_average):
            slack_msg["pretext"] = f"Only {len(results_df.usage_day.unique() - 2)}/{days_to_average} days of data is available in BigQuery."
        
        if len(changes_list):
            email_msg = ""
            for change in changes_list:
                slack_msg["body"] += (f"- '{change['sku_description']}' exceeded the last *{days_to_average}-day*" + 
                    f" {change['change_type']} by *{change['perc_change']}%* ({change['change']} {currency})\n")
                email_msg += (f"- <i>{change['sku_description']}</i> exceeded the last <strong>{days_to_average}-day</strong>" + 
                    f" {change['change_type']} by <strong>{change['perc_change']}%</strong> ({change['change']} {currency})\n")

            send_email(email_msg)
            send_slack_message(slack_msg)
        else:
            print(f"No billing limits have been exceeded on {last_complete_day}.")
    else:
        print("The results returned by your Query parameters aren't sufficient for analysis!")


def main():
    source_bigquery_table_id = os.environ['SOURCE_BIGQUERY_TABLE_ID']
    days_to_average = os.getenv('DAYS_TO_AVERAGE', 30)
    change_threshold = os.getenv('CHANGE_THRESHOLD', 0)
    print(f"Checking GCP billing limits:\n\
            source_bigquery_table_id: {source_bigquery_table_id}\n\
            days_to_average: {days_to_average}\n\
            change_threshold: {change_threshold}\n\
            ")
    check_limits(
        source_bigquery_table_id,
        change_threshold,
        days_to_average,
    )


if __name__ == '__main__':
    main()
