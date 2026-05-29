# Test Credentials

Login URL: `/` (preview URL root)

| Role         | Email                    | Password    | Notes                                  |
|--------------|--------------------------|-------------|----------------------------------------|
| Admin        | `admin@sagarmatha.edu`   | `admin123`  | user_type=1, redirects to `/admin/home/` |
| HOD (Staff)  | `dinesh.80@hod.com`      | `dinesh.80` | user_type=2, role=HOD, dashboard `/staff/home/` |
| Staff (Teacher) | `staff@staff.com`     | `staff123`  | user_type=2, role=Teacher              |
| Student      | `student@student.com`    | `student123`| user_type=3, dashboard `/student/home/` |

| Freshly-promoted student (post-bulk-promote test) | `bulk.alpha@bulk2.test` | `NewPass#2026` | Forced-change flow already completed in iteration 3. |

Re-seed any time with:
```
python manage.py seed_demo
```

**Note on temp passwords**: When you click "Promote to Student" (or bulk-promote), the new user is created with `must_change_password=True` and a random temp password. With the default console email backend, the password is printed to `/var/log/supervisor/backend.out.log` under a `Subject: Welcome to Sagarmatha College ...` block. Switch to real SMTP/SendGrid by setting `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (or `SENDGRID_API_KEY`-style) env vars in `/app/backend/.env`.
