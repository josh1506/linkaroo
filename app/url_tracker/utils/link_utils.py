def get_top_5_links(user_url):
    data = [{
        'id': str(url.id),
        'link': url.link,
        'title': url.title,
        'total_clicks': url.total_clicks} for url in user_url
        if url.total_clicks >= 1
    ]

    return sorted(data, key=lambda url: url['total_clicks'], reverse=True)[:5]
