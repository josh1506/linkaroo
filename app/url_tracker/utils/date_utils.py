from datetime import timedelta

from django.utils import timezone


def get_latest_7_days_total_clicks(user_url):
    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    url_titles = [url.title for url in user_url]
    data = [["Day", *url_titles]]

    for day in last_7_days:
        day_data = [day.strftime('%b %d')]
        for url in user_url:
            total_clicks = url.tracker.filter(created_at__date=day).count()
            day_data.append(total_clicks)
        data.append(day_data)

    return data
