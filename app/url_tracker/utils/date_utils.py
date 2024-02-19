from datetime import timedelta

from django.utils import timezone


def get_date_list(days_count):
    today = timezone.now().date()
    return [today - timedelta(days=i) for i in range(days_count, -1, -1)]


def get_url_clicks_day_range(user_url, days_count):
    day_list = get_date_list(days_count)

    url_titles = [url.title for url in user_url]
    data = [["Day", *url_titles]]

    for day in day_list:
        day_data = [day.strftime('%b %d')]
        for url in user_url:
            total_clicks = url.tracker.filter(created_at__date=day).count()
            day_data.append(total_clicks)
        data.append(day_data)

    return data


def get_links_created_day_range(user_url, days_count):
    day_list = get_date_list(days_count)
    data = []

    for day in day_list:
        day_data = day.strftime('%b %d')
        created_count = sum(1 for url in user_url if url.created_at.date() == day)
        data.append([day_data, created_count, "blue"])

    return data
