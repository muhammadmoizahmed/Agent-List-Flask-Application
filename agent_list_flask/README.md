# Agent List Flask Application

Ek simple Flask web application jo agents ki list manage karne ke liye banai gayi hai.

## Features

- **Admin Panel**: Secure login system ke sath
- **Agent Management**: Add, Edit, aur Delete agents
- **Public Display**: Agents ki public list with WhatsApp buttons
- **SQLite Database**: Lightweight database for data storage
- **Responsive Design**: Bootstrap 5 ke sath modern UI
- **Security**: Password hashing aur session management

## Project Structure

```
agent_list_flask/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── database.db           # SQLite database (auto-created)
├── templates/            # HTML templates
│   ├── index.html        # Public agent list page
│   ├── login.html        # Admin login page
│   ├── admin.html        # Admin dashboard
│   ├── add_agent.html    # Add new agent form
│   └── edit_agent.html   # Edit agent form
└── static/               # Static files (CSS, JS, images)
```

## Installation aur Setup

### 1. Dependencies Install Karein

```bash
pip install -r requirements.txt
```

### 2. Application Run Karein

```bash
python app.py
```

Application `http://localhost:5000` par run ho jayegi.

## Default Admin Login

- **Username**: `admin`
- **Password**: `admin123`

> **Important**: Pehle use karne ke baad password zaroor change karein!

## Pages aur Functions

### 1. Home Page (`/`)
- Public agent list
- WhatsApp contact buttons
- Statistics display
- Responsive design

### 2. Admin Login (`/login`)
- Secure authentication
- Session management
- Flash messages

### 3. Admin Panel (`/admin`)
- Agent management dashboard
- Add/Edit/Delete agents
- Statistics overview
- Logout functionality

### 4. Add Agent (`/add_agent`)
- Form for new agent entry
- Validation
- Success/error messages

### 5. Edit Agent (`/edit_agent/<id>`)
- Update existing agent info
- Pre-filled form
- Current info display

## Database Schema

### Agents Table
- `id` (Primary Key)
- `name` (Agent ka naam)
- `whatsapp_number` (WhatsApp number)
- `city` (Sheher ka naam)
- `created_at` (Timestamp)

### Admins Table
- `id` (Primary Key)
- `username` (Admin username)
- `password` (Hashed password)
- `created_at` (Timestamp)

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- CSRF protection
- SQL injection prevention
- Input validation

## Customization

### Admin Password Change Karne Ke Liye

1. Database me `admins` table me jaayein
2. Admin user ko update karein:
   ```python
   from werkzeug.security import generate_password_hash
   new_password = generate_password_hash('your_new_password')
   ```

### Styling Customize Karne Ke Liye

- Templates me CSS modify karein
- Bootstrap colors change karein
- Font Awesome icons use karein

## Troubleshooting

### Common Issues

1. **Port 5000 already in use**
   ```bash
   # Different port use karein
   python app.py --port 5001
   ```

2. **Database not creating**
   - Permissions check karein
   - Directory writeable hai ya nahi

3. **Login not working**
   - Database me admin user check karein
   - Password properly hashed hai ya nahi

## Development

### New Features Add Karne Ke Liye

1. Routes add karein `app.py` me
2. Templates create karein `templates/` folder me
3. Database schema update karein (agar zaroori ho)

### Production Deployment

For production, consider:
- Gunicorn or uWSGI server
- Environment variables for secrets
- Database backup strategy
- HTTPS setup

## Support

Agar koi issue aaye toh:
1. Error logs check karein
2. Database connection verify karein
3. Dependencies properly install hain ya nahi
