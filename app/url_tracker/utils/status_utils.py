def get_total_active_urls(user_url):
    total_active_url = 0

    for url in user_url:
        if url.is_active_url:
            total_active_url += 1

    data = [
        ['Active', 'Inactive'],
        ['Active', total_active_url],
        ['Inactive', len(user_url) - total_active_url]
    ]

    return data
