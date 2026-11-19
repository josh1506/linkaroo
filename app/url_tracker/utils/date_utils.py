from datetime import datetime, time, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone


def get_date_list(days_count):
    # Local dates (settings.TIME_ZONE), matching how clicks are bucketed below.
    today = timezone.localdate()
    return [today - timedelta(days=i) for i in range(days_count, -1, -1)]


def get_url_clicks_day_range(user_url, days_count):
    from app.url_tracker.models import URLTracker

    day_list = get_date_list(days_count)
    start = timezone.make_aware(datetime.combine(day_list[0], time.min))

    # One grouped query instead of one COUNT per url per day.
    # ponytail: IN-list of the user's url ids; switch to a subquery if a user ever owns tens of thousands of links.
    counts = {
        (row['url_id'], row['day']): row['n']
        for row in URLTracker.objects
        .filter(url_id__in=[url.pk for url in user_url], created_at__gte=start)
        .annotate(day=TruncDate('created_at'))
        .values('url_id', 'day')
        .annotate(n=Count('id'))
    }

    data = [["Day", *[url.title for url in user_url]]]
    for day in day_list:
        data.append([day.strftime('%b %d'), *[counts.get((url.pk, day), 0) for url in user_url]])

    return data


def get_links_created_day_range(user_url, days_count):
    day_list = get_date_list(days_count)
    data = []

    for day in day_list:
        day_data = day.strftime('%b %d')
        created_count = sum(1 for url in user_url if timezone.localdate(url.created_at) == day)
        data.append([day_data, created_count, "blue"])

    return data


WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def get_click_activity(clicks, days_count, pattern_days):
    """
    clicks: URLTracker queryset already scoped to the viewer's links.
    Returns chart rows for: total clicks per day (last days_count days), and clicks by weekday and by hour
    of day over the last pattern_days days. Local time (settings.TIME_ZONE), like the charts above.
    """
    from django.db.models.functions import ExtractHour, ExtractIsoWeekDay

    day_list = get_date_list(days_count)
    since = timezone.now() - timedelta(days=pattern_days)
    start = min(since, timezone.make_aware(datetime.combine(day_list[0], time.min)))

    per_day, per_weekday, per_hour = {}, [0] * 7, [0] * 24
    rows = (clicks.filter(created_at__gte=start)
            .annotate(day=TruncDate('created_at'), weekday=ExtractIsoWeekDay('created_at'), hour=ExtractHour('created_at'))
            .values('day', 'weekday', 'hour')
            .annotate(n=Count('id')))
    for row in rows:
        per_day[row['day']] = per_day.get(row['day'], 0) + row['n']
        # Grouped by day too, so each (day, hour) bucket is wholly inside or outside the pattern window.
        if row['day'] >= timezone.localdate(since):
            per_weekday[row['weekday'] - 1] += row['n']
            per_hour[row['hour']] += row['n']

    return {
        'per_day': [['Day', 'Clicks'], *[[day.strftime('%b %d'), per_day.get(day, 0)] for day in day_list]],
        'per_weekday': [['Day', 'Clicks'], *zip(WEEKDAYS, per_weekday)],
        'per_hour': [['Hour', 'Clicks'], *[[f'{h:02d}:00', n] for h, n in enumerate(per_hour)]],
    }
