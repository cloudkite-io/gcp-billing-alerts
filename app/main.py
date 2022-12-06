import os
from datetime import datetime, timedelta
from google.cloud import bigquery

from slack_notify import send_slack_message


def check_limits(
    source_bigquery_table_id,
    average_upper_limit_amount_change,
    average_upper_limit_percentage_change, daily_upper_limit_amount_change,
    daily_upper_limit_percentage_change,
    days_to_average=7,
):
    n_days_ago = datetime.strftime(
        datetime.utcnow() - timedelta(days=int(days_to_average)), "%Y-%m-%d")

    # Construct a BigQuery client object.
    client = bigquery.Client()

    # Build query
    query = f"""
        SELECT DATE(usage_end_time) as usage_day, sum(cost) as cost, max(currency) as currency
        FROM `{source_bigquery_table_id}`
        WHERE usage_start_time >= '{n_days_ago}'
        GROUP BY usage_day ORDER BY usage_day
    """
    query_job = client.query(query)  # Make an API request.
    # Convert results into a Pandas DataFrame
    results_df = query_job.to_dataframe()
    
    if not results_df.empty and len(results_df) > 1:
        currency = results_df.iloc[0].currency

        results_df.sort_values('usage_day', ascending=True)

        average_cost = results_df.iloc[:-1].cost.mean()
        latest_data = results_df.iloc[-1]
        before_latest_data = results_df.iloc[-2]

        slack_msg = {
            "title": f"GCP billing summary for {latest_data.usage_day}",
            "body_title": f"Total bill for {latest_data.usage_day} was {round(latest_data.cost, 2)} {currency}.",
            "billing_date": latest_data.usage_day,
            "body": ""
            }

        if average_upper_limit_amount_change:
            if (avrg_change := latest_data.cost -
                    average_cost) > float(average_upper_limit_amount_change):
                slack_msg["body"] += (
                    f"- Exceeded the last *{days_to_average}-day* average by *{round(avrg_change, 2)} {currency}*\n")
        if average_upper_limit_percentage_change:
            if (perc_change := (latest_data.cost - average_cost) /
                    average_cost * 100) > float(average_upper_limit_percentage_change):
                slack_msg["body"] += (
                    f"- Exceeded the last *{days_to_average}-day* average by *{round(perc_change, 2)}%*\n")
        if daily_upper_limit_amount_change:
            if (daily_change := latest_data.cost -
                    before_latest_data.cost) > float(daily_upper_limit_amount_change):
                slack_msg["body"] += (
                    f"- Exceeded that of *{before_latest_data.usage_day}* by *{round(daily_change, 2)} {currency}*\n")
        if daily_upper_limit_percentage_change:
            if (daily_perc_change := (latest_data.cost - before_latest_data.cost) /
                    before_latest_data.cost * 100) > float(daily_upper_limit_percentage_change):
                slack_msg["body"] += (
                    f"- Exceeded that of *{before_latest_data.usage_day}* by *{round(daily_perc_change, 2)}%*\n")

        if len(results_df) < int(days_to_average):
            slack_msg["pretext"] = f"Only {len(results_df)}/{days_to_average} days of data is available in BigQuery."
        
        if slack_msg["body"]:
            send_slack_message(slack_msg)
        else:
            print(f"No billing limits have been exceeded on {latest_data.usage_day}.")
    else:
        print("The results returned by your Query parameters aren't sufficient for analysis!")


def main():
    source_bigquery_table_id = os.environ['SOURCE_BIGQUERY_TABLE_ID']
    days_to_average = os.getenv('DAYS_TO_AVERAGE')
    average_upper_limit_amount_change = os.getenv(
        'AVERAGE_UPPER_LIMIT_AMOUNT_CHANGE')
    average_upper_limit_percentage_change = os.getenv(
        'AVERAGE_UPPER_LIMIT_PERCENTAGE_CHANGE')
    daily_upper_limit_amount_change = os.getenv(
        'DAILY_UPPER_LIMIT_AMOUNT_CHANGE')
    daily_upper_limit_percentage_change = os.getenv(
        'DAILY_UPPER_LIMIT_PERCENTAGE_CHANGE')
    print(f"Checking GCP billing limits:\n\
            source_bigquery_table_id: {source_bigquery_table_id}\n\
            days_to_average: {days_to_average}\n\
            average_upper_limit_amount_change: {average_upper_limit_amount_change}\n\
            average_upper_limit_percentage_change: {average_upper_limit_percentage_change}\n\
            daily_upper_limit_amount_change: {daily_upper_limit_amount_change}\n\
            daily_upper_limit_percentage_change: {daily_upper_limit_percentage_change}\n\
                ")
    check_limits(
        source_bigquery_table_id,
        average_upper_limit_amount_change,
        average_upper_limit_percentage_change, daily_upper_limit_amount_change,
        daily_upper_limit_percentage_change,
        days_to_average,
    )


if __name__ == '__main__':
    main()
