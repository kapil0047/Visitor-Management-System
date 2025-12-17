# Visitor-Management-System
✅ Visitor Management System – Full Project Prompt
I’ve built a Visitor Management System for Pyrotech Electronics Pvt. Ltd. using Flask (Python) and PostgreSQL. It is a real-world solution with the following features:

🔧 Tech Stack
Backend: Flask

Database: PostgreSQL

Frontend: HTML, CSS (Glassmorphism UI)

PDF generation: xhtml2pdf

Email: SMTP (optional)

Deployment target: Localhost or internal server

🧩 Core Functionalities Implemented
✅ Super Admin and Admin login with role management

✅ Admin Dashboard with visitor logs, delete/export/print options

✅ Visitor Registration with:

Image capture via webcam

Form validation

Image preview

✅ Visitor pass generation (PDF + print)

✅ Styled PDF layout (matches on-screen pass)

✅ Visitor pass includes:

Photo, name, time, reason, person to meet

✅ "Delete Selected" and "Delete All" logs (fixed)

✅ Filter logs by employee, date, and range

✅ Edit Visitor, Add Employee, and Create Admin (UI-styled)

✅ Theme consistency (blue glass design throughout)

✅ Final structured layout for admin panel and all forms

✅ Favicon added

✅ Form validations applied

✅ Tab logo added

✅ Background animation and card effects

✅ Admin filter and employee filter fixed

✅ Readme writing pending

✅ Final UI and logic done

⚠️ Tasks Done in DB (via pgAdmin)
✅ Checked existing admins

✅ Will remove non-super admins manually from admin table

⏳ Remaining Final Touches (1 Hour):
Task	Est. Time	Status
Add favicon to browser tab	5–10 min	✅ Done
Final cleanup (remove test files, rename)	15 min	⏳
Test all user flows once	20–30 min	⏳
Write deployment README	10–15 min	⏳
Delete extra admins via pgAdmin	5 min	⏳

🔐 Security Features
CSRF protection (Flask-WTF) – planned but not added

Session expiration – optional

CAPTCHA – skipped (internal use only)