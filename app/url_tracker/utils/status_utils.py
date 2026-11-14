def get_total_active_urls(user_url):
    """user_url must be annotated with click_count. "Active" = has at least one click (existing meaning, kept)."""
    total_active_url = sum(1 for url in user_url if url.click_count > 0)

    data = [
        ['Active', 'Inactive'],
        ['Active', total_active_url],
        ['Inactive', len(user_url) - total_active_url]
    ]

    return data
