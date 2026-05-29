# Sagarmatha College ERP (SagarmathaEngineeringCollegeERPDemo)

A Django-based College ERP system (backend + frontend). This repository contains the Django project, a small frontend proxy, and supporting scripts to run the application locally for development.

This README explains how to set up the development environment, install dependencies, run the database migrations, and start the dev servers for both backend and frontend.

**Contents**
- **Project:** Django app in the repository root (project `college_management_system`, app `main_app`).
- **Frontend:** Lightweight proxy in [frontend](frontend/) used for local development.
- **Backend deps:** `requirements.txt` (root) and `backend/requirements.txt` (additional packages).

**Prerequisites**
- Python 3.11+ installed.
- Node.js + npm (only needed for the simple proxy in `frontend/`).
- Git (optional).

Quick setup (Windows PowerShell)

1. Create and activate a virtual environment inside the project root:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

2. Upgrade pip and install root Python dependencies:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

3. (Optional) Install the extra backend packages:

```powershell
python -m pip install -r backend/requirements.txt
```

Notes about `backend/requirements.txt`:
- This file previously referenced a private package (`emergentintegrations`). That entry is commented out in this checkout to allow local installs. If you need that package, add your private package index or wheel URL and re-enable the requirement.

Environment variables
- Copy and adapt an environment file or set the following variables in your shell as needed:
	- `SECRET_KEY` — Django secret key (recommended to set for production)
	- `DEBUG` — set to `True` for local development
	- `ALLOWED_HOSTS` — comma-separated hosts
	- `RECAPTCHA_PUBLIC_KEY` / `RECAPTCHA_PRIVATE_KEY` — if using reCAPTCHA
	- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — for email

Running database migrations and creating a superuser

```powershell
python manage.py migrate --noinput
python manage.py createsuperuser
```

Start the Django development server

```powershell
python manage.py runserver 0.0.0.0:8000
```

Open http://127.0.0.1:8000/ in your browser.

Frontend proxy (local development)

The `frontend/` folder contains a tiny Node.js proxy used in some development setups. To run it:

```powershell
cd frontend
npm install
npm start
# proxy runs `node proxy.js` by default
```

Common issues and troubleshooting

- CSRF verification failed on login (403):
	- Quick local workaround: the `doLogin` view has been temporarily decorated with `@csrf_exempt` in [main_app/views.py](main_app/views.py) to allow testing when the frontend or origin differs. THIS IS INSECURE for production — revert it and fix the root cause before deploying.
	- Proper fix: ensure the browser receives the Django CSRF cookie and that the login form includes `{% csrf_token %}` (the templates already include it). If you use a proxy, ensure `CSRF_TRUSTED_ORIGINS` in [college_management_system/settings.py](college_management_system/settings.py) contains the scheme+host+port of your frontend/proxy.

- Private packages: If `backend/requirements.txt` requires private wheels or indexes, add the index with `--extra-index-url` or provide the wheel file locally.

- Django version mismatch: The repository expects Django 6.0.5; `backend/requirements.txt` was adjusted to use `Django==6.0.5` to avoid repeated reinstall cycles. If you must use another Django version, run the test suite and update compatibility.

Development tips

- Use the configured virtual environment in this repo: `.venv` (created above).
- Run `python manage.py runserver` and keep an eye on the terminal output for autoreload messages.
- To run unit tests:

```powershell
python manage.py test
```

Contributing

1. Create a branch for your changes.
2. Run tests and linters before opening a PR.

License

See the [LICENSE](LICENSE) file in the repository root.

Acknowledgements

This project was adapted from the Sagarmatha College ERP demo repository. If you want, I can also add a run script (`scripts/setup_dev.ps1`) to automate environment creation and install steps.
