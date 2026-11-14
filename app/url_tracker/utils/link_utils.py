def get_top_5_links(user_url):
    """user_url must be annotated with click_count (see UrlOverviewTemplateView)."""
    data = [{
        'id': str(url.id),
        'link': url.link,
        'title': url.title,
        'total_clicks': url.click_count} for url in user_url
        if url.click_count >= 1
    ]

    return sorted(data, key=lambda url: url['total_clicks'], reverse=True)[:5]
