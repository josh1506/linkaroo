# Linkaroo

Linkaroo is a web application that allows users to create custom URLs that redirect to specific pages while tracking all URL clicks. With Linkaroo, you can easily manage and monitor the performance of your links, gaining insights into user engagement and behavior.

## Features

- **Custom URL Creation**: Generate personalized URLs that redirect to any desired destination.
- **Click Tracking**: Track every click on your custom URLs to understand user engagement.
- **Analytics Dashboard**: Gain insights into link performance through an intuitive analytics dashboard.
- **URL Management**: Easily manage and edit your custom URLs as needed.

## Installation

Linkaroo is a web-based application. A public production URL has not been published yet.
To run it locally: create a Python 3.12 virtualenv, `pip install --require-hashes -r requirements/dev.lock`, copy `.env.example` to `.env` (set `SECRET_KEY`, `DEBUG=True`), then `python manage.py migrate` and `python manage.py runserver`.

> Note: `linkaroo.com` is **not** operated by this project (it currently redirects to a domain-sale page). Don't share short links or send support requests to that domain.

## Usage

1. **Sign Up or Log In**: If you're a new user, sign up for a Linkaroo account. Existing users can log in with their credentials.

2. **Create a Custom URL**: Once logged in, navigate to the dashboard and click on the "Create New URL" button. Enter the destination URL and choose a custom alias if desired.

3. **Track Clicks**: As users click on your custom URLs, Linkaroo will track each click, providing you with valuable insights into user engagement.

4. **Analyze Performance**: Visit the analytics dashboard to view detailed statistics about your custom URLs, including click counts, geographic distribution of clicks, and more.

5. **Manage URLs**: Edit or delete your custom URLs as needed from the dashboard.

## Contributing

Contributions are welcome! If you have any ideas for new features, improvements, or bug fixes, feel free to open an issue or submit a pull request on our [GitHub repository](https://github.com/josh1506/linkaroo).

## Support

If you encounter any issues or have questions, please open an issue on the [GitHub repository](https://github.com/josh1506/linkaroo/issues). Please don't include passwords or personal data in issues.

## License

Linkaroo is licensed under the [MIT License](LICENSE).
