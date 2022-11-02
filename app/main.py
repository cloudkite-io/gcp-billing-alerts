import os
from datetime import datetime, timedelta
from google.cloud import bigquery

from slack_notify import send_slack_message


def check_limits(
    source_bigquery_table,
    average_upper_limit_amount_change,
    average_upper_limit_percentage_change, daily_upper_limit_amount_change,
    daily_upper_limit_percentage_change,
    days_to_average=2,
):
    n_days_ago = datetime.strftime(
        datetime.utcnow() - timedelta(days=int(days_to_average)), "%Y-%m-%d")
    today = datetime.strftime(
        datetime.utcnow(), "%Y-%m-%d")
    print(n_days_ago, today)

    # Construct a BigQuery client object.
    client = bigquery.Client()

    # Build query
    query = f"""
        SELECT project, usage_start_time, usage_end_time, cost, currency
        FROM `{source_bigquery_table}`
        WHERE usage_start_time > '{n_days_ago}' AND usage_end_time < '{today}'
    """
    query_job = client.query(query)  # Make an API request.
    # Convert results into a Pandas DataFrame
    results_df = query_job.to_dataframe()

    if not results_df.empty:
        currency = results_df.iloc[0].currency

        results_df["usage_day"] = results_df.usage_end_time.apply(
            lambda dd: dd.date)
        results_df['project'] = results_df.project.apply(lambda p: p['id'])

        # Sum daily results
        agg_results_df = results_df.groupby(['usage_day']).sum()
        agg_results_df.reset_index(inplace=True)
        agg_results_df.sort_values('usage_day', ascending=True)

        average_cost = agg_results_df.cost.mean()
        latest_data = agg_results_df.iloc[-1]
        before_latest_data = agg_results_df.iloc[-2]

        slack_msg = {
            "title": f"GCP billing summary for {latest_data.usage_day}", "body": ""}

        if average_upper_limit_amount_change:
            if (avrg_change := latest_data.cost -
                    average_cost) > float(average_upper_limit_amount_change):
                slack_msg["body"] += (
                    f"- Exceeded *{days_to_average}-day* average by *{round(avrg_change, 2)} {currency}*\n")
        if average_upper_limit_percentage_change:
            if (perc_change := (latest_data.cost - average_cost) /
                    average_cost * 100) > float(average_upper_limit_percentage_change):
                slack_msg["body"] += (
                    f"- Exceeded *{days_to_average}-day* average by *{round(perc_change, 2)}%*\n")
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

        if slack_msg["body"]:
            send_slack_message(slack_msg)
    else:
        print("Query parameters returned no results!")


def main():
    source_bigquery_table = os.environ['SOURCE_BIGQUERY_TABLE']
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
            source_bigquery_table: {source_bigquery_table}\n\
            days_to_average: {days_to_average}\n\
            average_upper_limit_amount_change: {average_upper_limit_amount_change}\n\
            average_upper_limit_percentage_change: {average_upper_limit_percentage_change}\n\
            daily_upper_limit_amount_change: {daily_upper_limit_amount_change}\n\
            daily_upper_limit_percentage_change: {daily_upper_limit_percentage_change}\n\
                ")
    check_limits(
        source_bigquery_table,
        average_upper_limit_amount_change,
        average_upper_limit_percentage_change, daily_upper_limit_amount_change,
        daily_upper_limit_percentage_change,
        days_to_average,
    )


if __name__ == '__main__':
    main()
