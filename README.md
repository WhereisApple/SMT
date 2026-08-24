# Society Maintenance Tracker

A comprehensive platform for managing apartment society complaints with admin oversight, status tracking, and resident notifications.

## Features

- **Resident Management**
  - Register and login with credentials
  - Raise complaints with photos and descriptions
  - Track complaint status in real-time
  - View complete history of each complaint
  - Receive email notifications on status changes

- **Admin Management**
  - View all complaints with filtering by category, status, or priority
  - Set complaint priority (Low, Medium, High)
  - Update complaint status (Open, In Progress, Resolved)
  - Automatic overdue detection and flagging
  - Dashboard with statistics by category and status
  - Post notices to the notice board
  - Pin important notices for visibility

- **Notice Board**
  - Share important announcements with residents
  - Pin important notices to appear at the top
  - Email notifications for important notices
  - Resident access to notice board

- **Dashboard**
  - Total complaints overview
  - Complaints by status breakdown
  - Complaints by category breakdown
  - Overdue complaints count
  - Quick admin insights

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Storage**: Supabase (Photo uploads)
- **Email**: SMTP (Gmail)
- **Authentication**: JWT
- **Database**: PostgreSQL with Supabase

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Supabase account
- Gmail account (for email notifications)

### Backend Setup

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your actual configuration:
   - Database URL (PostgreSQL)
   - Supabase credentials
   - Email configuration
   - Secret key

5. **Initialize database**
   ```bash
   python
   from models.database import engine, Base
   Base.metadata.create_all(bind=engine)
   exit()
   ```

6. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

   API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend folder**
   ```bash
   cd ../frontend
   ```

2. **Update API URL in app.js**
   - Open `app.js` and update `API_BASE_URL` if not using localhost:8000

3. **Serve using a simple HTTP server**
   ```bash
   python -m http.server 8080
   ```
   Or use any other static file server.

   Frontend will be available at `http://localhost:8080`

## API Documentation

### Authentication Endpoints

#### Register Resident
- **POST** `/api/auth/register/resident`
- Body:
  ```json
  {
    "email": "resident@example.com",
    "password": "Password123",
    "name": "John Doe",
    "flat_number": "A-101",
    "phone": "9876543210"
  }
  ```

#### Login
- **POST** `/api/auth/login`
- Body:
  ```json
  {
    "email": "user@example.com",
    "password": "Password123"
  }
  ```

#### Get Current User
- **GET** `/api/auth/me`
- Header: `Authorization: Bearer <token>`

### Complaints Endpoints

#### Create Complaint
- **POST** `/api/complaints/`
- Body: `form-data` with fields:
  - `category`: string (plumbing, electrical, structural, cleanliness, noise, parking, common_area, other)
  - `description`: string
  - `file`: optional image file

#### Get My Complaints (Resident)
- **GET** `/api/complaints/resident/my-complaints`
- Header: `Authorization: Bearer <token>`

#### Get Complaint Details
- **GET** `/api/complaints/{complaint_id}`
- Header: `Authorization: Bearer <token>`

#### Update Complaint (Admin)
- **PUT** `/api/complaints/{complaint_id}`
- Body:
  ```json
  {
    "status": "in_progress",
    "priority": "high",
    "note": "Work in progress"
  }
  ```

#### Get All Complaints (Admin)
- **GET** `/api/complaints/admin/all?category=plumbing&status=open&priority=high`
- Header: `Authorization: Bearer <token>`

#### Get Overdue Complaints (Admin)
- **GET** `/api/complaints/admin/overdue`
- Header: `Authorization: Bearer <token>`

#### Get Dashboard Stats (Admin)
- **GET** `/api/complaints/admin/dashboard`
- Header: `Authorization: Bearer <token>`

### Notices Endpoints

#### Create Notice (Admin)
- **POST** `/api/notices/`
- Body:
  ```json
  {
    "title": "Notice Title",
    "content": "Notice content",
    "is_important": true
  }
  ```

#### Get All Notices
- **GET** `/api/notices/`

#### Get Notice Details
- **GET** `/api/notices/{notice_id}`

#### Update Notice (Admin)
- **PUT** `/api/notices/{notice_id}`
- Body:
  ```json
  {
    "title": "Updated Title",
    "content": "Updated content",
    "is_important": false
  }
  ```

#### Delete Notice (Admin)
- **DELETE** `/api/notices/{notice_id}`

## Database Schema

### Users Table
- `id`: UUID (Primary Key)
- `name`: String
- `email`: String (Unique)
- `password_hash`: String
- `role`: Enum (resident, admin)
- `flat_number`: String (for residents)
- `phone`: String
- `is_active`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

### Complaints Table
- `id`: UUID (Primary Key)
- `resident_id`: UUID (Foreign Key)
- `category`: Enum (plumbing, electrical, structural, cleanliness, noise, parking, common_area, other)
- `description`: Text
- `photo_url`: String (nullable)
- `status`: Enum (open, in_progress, resolved, closed)
- `priority`: Enum (low, medium, high)
- `is_overdue`: Boolean
- `days_to_overdue`: Integer (default: 7)
- `created_at`: DateTime
- `updated_at`: DateTime
- `resolved_at`: DateTime (nullable)

### Complaint History Table
- `id`: UUID (Primary Key)
- `complaint_id`: UUID (Foreign Key)
- `created_by_id`: UUID (Foreign Key)
- `status`: Enum (open, in_progress, resolved, closed)
- `priority`: Enum (low, medium, high) (nullable)
- `note`: Text (nullable)
- `created_at`: DateTime

### Notices Table
- `id`: UUID (Primary Key)
- `admin_id`: UUID (Foreign Key)
- `title`: String
- `content`: Text
- `is_important`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

## Features Overview

### Complaint Lifecycle
1. **Resident creates complaint** with category, description, and optional photo
2. **Admin reviews complaint** in dashboard
3. **Admin sets priority** based on urgency
4. **Admin updates status** as work progresses (Open → In Progress → Resolved)
5. **Resident receives emails** on each status update
6. **Complaint marked resolved** when completed
7. **System tracks complete history** with timestamps

### Overdue Detection
- Complaints automatically flagged as overdue after configurable days (default: 7)
- Overdue complaints appear at top of admin dashboard
- Admin can view all overdue complaints separately

### Photo Handling
- Residents can attach photos to complaints
- Photos uploaded to Supabase storage
- Secure URL returned and stored with complaint
- Residents can view photos in complaint details

### Notification System
- Email sent when complaint status changes
- Email sent when important notice is posted
- Uses Gmail SMTP (configurable for other providers)
- Async email sending to prevent API delays

## Deployment

### Backend Deployment (Render/Railway)

1. Push code to GitHub
2. Create new Web Service on Render/Railway
3. Set environment variables in platform settings
4. Deploy from repository

### Frontend Deployment (Vercel)

1. Push code to GitHub
2. Connect repository to Vercel
3. Deploy automatically on push

## Configuration

### Overdue Threshold
Edit `OVERDUE_DAYS` in `.env` (default: 7 days)

### Email Provider
Currently configured for Gmail. To use another provider:
1. Update `SMTP_SERVER` and `SMTP_PORT` in `.env`
2. Update authentication in `utils/email.py`

### Photo Storage
Uses Supabase. To use another provider:
1. Update `utils/supabase.py` with your storage provider
2. Update configuration in `.env`

## Security Considerations

- JWT tokens expire after 30 minutes
- Passwords hashed with bcrypt
- Role-based access control (RBAC)
- CORS configured for frontend
- SQL injection prevention via SQLAlchemy ORM
- Environment variables for sensitive data

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database exists

### Email Not Sending
- Verify SMTP credentials in .env
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Check SENDER_EMAIL format

### Photo Upload Error
- Verify Supabase credentials
- Check bucket name in .env
- Ensure bucket allows public access

### Token Invalid Error
- Token may have expired (refresh by logging in again)
- Check SECRET_KEY is same across sessions
- Verify token format in Authorization header

## Future Enhancements

- Two-factor authentication
- Advanced search and filters
- Export reports as PDF
- Complaint templates
- SLA management
- Integration with SMS notifications
- Mobile app
- Payment integration for maintenance fees
- Bulk complaint upload

## License

MIT License

## Support

For issues, questions, or suggestions, please create an issue in the repository.
