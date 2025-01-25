# Pastein

Pastein is a modern, feature-rich clone of Pastebin created for practice and learning purposes. It allows users to store, share, and manage text snippets online effortlessly. Built with Django, a high-level Python web framework, Pastein includes robust functionality such as user authentication, paste visibility settings, CAPTCHA protection, and more.

## 🌟 Features

- **User Authentication:** Login, registration, and logout functionality.
- **Paste Management:** Create, view, edit, and delete pastes.
- **Visibility Options:** Set paste visibility to public, unlisted, or private.
- **Secure Pastes:** Option to password-protect your pastes.
- **Profile Management:** Update your profile and upload a profile picture.
- **CAPTCHA Protection:** Integrated Cloudflare Turnstile to prevent spam.
- **Dark Mode:** User-friendly dark mode support for enhanced usability.
- **Responsive Design:** Fully responsive design built with Bootstrap.

## 🌐 Live Demo

- [https://pastein.my.id/](https://pastein.my.id/)
- [https://django-pastein.vercel.app/](https://django-pastein.vercel.app/)

## ✅ Requirements

- Python 3.9 or higher
- PostgreSQL or MySQL database
- S3-compatible storage for media files
- Redis for caching

## 🚀 Installation

Follow these steps to set up the Pastein project locally:

1. **Clone the repository:**
    ```sh
    git clone https://github.com/gingantic/pastein.git
    cd pastein
    ```

2. **Create a virtual environment and activate it:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**  
   Create a `.env` file using the example provided in `.env.dummy`:
    ```sh
    nano .env
    ```

5. **Apply migrations:**
    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

6. **Collect static files:**
    ```sh
    python manage.py collectstatic
    ```

7. **Run the development server:**
    ```sh
    python manage.py runserver
    ```

Alternatively, deploy it on Vercel:

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/import/project?template=https://github.com/gingantic/pastein.git)

> **Note:**  
> To make the hit/view counter work, visit or using cron to `api/update-views/` with a header containing:  
> `Authorization: Bearer <cron-secret-key>`

## 📖 Usage

1. Visit the website in your web browser.
2. Register a new account or log in with an existing account.
3. Create, view, edit, and delete pastes.
4. Manage your profile and upload a profile picture.

## 📋 TODO List

Here are some planned features and improvements for Pastein:

- [ ] The Last 24 Hours Pastes.
- [ ] Improve the UI/UX.
- [ ] Admin Panels
- [ ] Optimize database queries for better performance.
- [ ] Create an API for external integration (e.g., third-party apps).

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repository, make changes, and submit a pull request.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📬 Contact

If you have any questions, feedback, or suggestions, feel free to contact me on [GitHub](https://github.com/gingantic).

Thank you for using Pastein!
