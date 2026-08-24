# System Design: Society Maintenance Tracker

## Overview
The Society Maintenance Tracker is a web-based platform designed to streamline complaint management in apartment societies. It provides residents with a transparent channel to report maintenance issues and enables administrators to track, prioritize, and resolve complaints efficiently.

## Architecture

### Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL
- **File Storage**: Supabase Storage
- **Authentication**: JWT (JSON Web Tokens)
- **Email**: SMTP (Gmail)

### High-Level Components

```
┌─────────────────┐
│   Frontend      │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────────────┐
│   FastAPI Backend       │
│  (Routes, Services)     │
└────────┬────────────────┘
         │
    ┌────┴────┬──────────┬───────────┐
    ↓         ↓          ↓           ↓
┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│   DB   │ │SMTP  │ │Supabase  │ │JWT Auth  │
│(Postgre)│ │Email │ │ Storage  │ │ Service  │
└────────┘ └──────┘ └──────────┘ └──────────┘
```

## Data Models

### 1. User Model
```
Table: users
- id: UUID (PK)
- name: String
- email: String (Unique)
- password_hash: String
- role: Enum (resident, admin)
- flat_number: String (nullable, for residents)
- phone: String (nullable)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

**Relationships**: One user can have many complaints and history records.

### 2. Complaint Model
```
Table: complaints
- id: UUID (PK)
- resident_id: UUID (FK to users)
- category: Enum (8 categories)
- description: Text
- photo_url: String (nullable)
- status: Enum (open, in_progress, resolved, closed)
- priority: Enum (low, medium, high)
- is_overdue: Boolean
- days_to_overdue: Integer (configurable, default: 7)
- created_at: DateTime
- updated_at: DateTime
- resolved_at: DateTime (nullable)
```

**Indexes**: resident_id, status, created_at, is_overdue for fast filtering.

**Rationale**:
- Storing photo_url instead of actual photo saves database storage
- Priority is separate from status to allow independent updates
- is_overdue flag enables quick queries for overdue complaints
- days_to_overdue allows per-complaint overdue threshold configuration

### 3. ComplaintHistory Model
```
Table: complaint_history
- id: UUID (PK)
- complaint_id: UUID (FK to complaints)
- created_by_id: UUID (FK to users)
- status: Enum
- priority: Enum (nullable)
- note: Text (nullable)
- created_at: DateTime
```

**Design Decision**: 
- Immutable history table prevents data loss
- Records actor (created_by) for audit trail
- Timestamps enable tracking response time
- Optional note provides context for each update

### 4. Notice Model
```
Table: notices
- id: UUID (PK)
- admin_id: UUID (FK to users)
- title: String
- content: Text
- is_important: Boolean
- created_at: DateTime
- updated_at: DateTime
```

**Index**: is_important for query optimization.

## Complaint Lifecycle & Status History

### Workflow States
```
         ┌─────────┐
         │  OPEN   │ ← Resident creates complaint
         └────┬────┘
              │ Admin starts work
         ┌────↓─────────┐
         │ IN_PROGRESS  │
         └────┬─────────┘
              │ Work complete
         ┌────↓────────┐
         │  RESOLVED   │ ← Email sent to resident
         └────┬────────┘
              │ Auto-close after verification
         ┌────↓───┐
         │ CLOSED │
         └────────┘
```

### History Tracking Implementation

**Every status update**:
1. Create ComplaintHistory record with timestamp
2. Record actor ID (which admin made the change)
3. Store optional note explaining the update
4. Complaint.updated_at is automatically updated

**Resident view**:
- Residents see complete history of their complaint
- Each history entry shows: date, status, who updated it, and any notes
- Timeline provides transparency and trust

**Admin view**:
- Can sort complaints by status changes
- Filter by date range to track productivity
- Identify bottlenecks in workflow

## Overdue Detection

### Algorithm

```python
def check_complaint_overdue(created_at, days_threshold=7):
    overdue_date = created_at + timedelta(days=days_threshold)
    return datetime.utcnow() > overdue_date
```

### Implementation Details

1. **Configurable Threshold**: `OVERDUE_DAYS` in environment (default: 7)
2. **Per-Complaint Threshold**: Each complaint has `days_to_overdue` field for flexibility
3. **Flag Management**:
   - is_overdue flag set to True when complaint becomes overdue
   - Flag cleared when complaint is resolved
   - Prevents recalculation on every query

4. **Query Optimization**:
   ```sql
   SELECT * FROM complaints 
   WHERE status != 'resolved' 
   AND is_overdue = true
   ORDER BY created_at ASC
   ```

5. **Admin Dashboard**:
   - Overdue complaints displayed prominently
   - Color-coded (red) for quick visibility
   - Count tracked in statistics

### Edge Cases Handled
- Complaints resolved within threshold don't appear as overdue
- Threshold can be adjusted per complaint if needed
- System marks status as overdue after resolution automatically resets

## Photo Upload & Storage

### Workflow
```
┌─────────────┐
│   Resident  │
│ uploads     │
│   photo     │
└──────┬──────┘
       │
       ↓
┌──────────────────────┐
│ Save to temp file    │
│ (server side)        │
└──────┬───────────────┘
       │
       ↓
┌──────────────────────────────┐
│ Upload to Supabase Storage   │
│ (filename: UUID_originalname)│
└──────┬───────────────────────┘
       │
       ↓
┌──────────────────────────────┐
│ Get public URL               │
└──────┬───────────────────────┘
       │
       ↓
┌──────────────────────────────┐
│ Store URL in complaint.      │
│ photo_url field              │
└──────────────────────────────┘
```

### Design Decisions

1. **Cloud Storage**: Using Supabase instead of local storage
   - Scalability: Unlimited storage
   - Performance: CDN delivery
   - Security: Access control via bucket policies
   - Availability: 99.9% uptime SLA

2. **Filename Strategy**: `UUID_original_filename`
   - Prevents collisions
   - Maintains original filename for UX
   - Easy to identify complaint from filename

3. **Async Upload**: Non-blocking operation
   - Request returns complaint even if photo upload fails
   - User receives feedback via separate notification

4. **Error Handling**:
   - Failed uploads logged but don't block complaint creation
   - Residents can reupload photos later
   - Admin can manually add photos if needed

### Storage Structure
```
Bucket: complaints-photos
├── complaints/
    ├── 550e8400-e29b-41d4-a716-446655440000_leaking_tap.jpg
    ├── 550e8400-e29b-41d4-a716-446655440001_broken_door.jpg
    └── ...
```

## Notification System

### Email Triggers

**1. Complaint Status Change**
```
Trigger: Admin updates complaint status
When: After status update, before response sent
To: Complaint resident's email
Template: 
  Subject: Complaint #{ID} Status Updated
  Body: Current status, any notes, link to dashboard
Async: Yes (non-blocking)
```

**2. Important Notice Posted**
```
Trigger: Admin creates notice with is_important = true
When: After notice created
To: All residents' emails
Template:
  Subject: Important Notice: {title}
  Body: Notice title, teaser, link to notice board
Async: Yes (batched sending)
```

### Implementation

```python
async def send_complaint_status_email(email, complaint_id, status, note):
    # Async email sending doesn't block API response
    # Uses SMTP with Gmail configuration
    # Retry logic for failed sends
    pass
```

**Reliability**:
- Try-except blocks prevent email errors from crashing API
- Failed emails logged for manual follow-up
- Residents can view status even if email fails

**Configuration** (in .env):
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

## API Design

### Authentication
- JWT tokens issued on login
- Token expires after 30 minutes
- Refresh by logging in again (no refresh token endpoint)
- Token stored in `Authorization: Bearer {token}` header

### Role-Based Access Control
```
RESIDENT Role:
  ✓ View own complaints
  ✓ Create complaints
  ✓ View notice board
  ✗ Access admin features

ADMIN Role:
  ✓ View all complaints
  ✓ Update complaint status/priority
  ✓ Manage notices
  ✓ View dashboard & statistics
  ✗ Create complaints (theoretical security)
```

### Key Endpoints

**Authentication**:
- POST /api/auth/register/resident - Register resident
- POST /api/auth/login - User login
- GET /api/auth/me - Current user info

**Complaints**:
- POST /api/complaints/ - Create complaint
- GET /api/complaints/resident/my-complaints - My complaints
- GET /api/complaints/{id} - Complaint details with history
- PUT /api/complaints/{id} - Update complaint (admin)
- GET /api/complaints/admin/all - All complaints (admin)
- GET /api/complaints/admin/overdue - Overdue list (admin)
- GET /api/complaints/admin/dashboard - Dashboard stats (admin)

**Notices**:
- POST /api/notices/ - Create notice (admin)
- GET /api/notices/ - Get all notices
- GET /api/notices/{id} - Notice details
- PUT /api/notices/{id} - Update notice (admin)
- DELETE /api/notices/{id} - Delete notice (admin)

## Database Indexes

```sql
-- Optimizes resident complaint queries
CREATE INDEX idx_complaints_resident_id ON complaints(resident_id);

-- Fast status filtering for dashboard
CREATE INDEX idx_complaints_status ON complaints(status);

-- Overdue detection queries
CREATE INDEX idx_complaints_is_overdue ON complaints(is_overdue);

-- Historical queries
CREATE INDEX idx_complaint_history_complaint_id ON complaint_history(complaint_id);
CREATE INDEX idx_complaint_history_created_at ON complaint_history(created_at);

-- Notice importance and date
CREATE INDEX idx_notices_is_important ON notices(is_important);
CREATE INDEX idx_notices_created_at ON notices(created_at);
```

## Security Considerations

1. **Password Storage**: Bcrypt hashing with salt
2. **JWT**: HS256 algorithm with strong secret
3. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
4. **CORS**: Configured to allow frontend domain
5. **Environment Variables**: Secrets stored in .env, not hardcoded
6. **Input Validation**: Pydantic models validate all inputs
7. **Rate Limiting**: Can be added via middleware if needed

## Scalability Considerations

### Database Optimization
- Indexes on frequently queried fields
- Pagination for large result sets
- Connection pooling via SQLAlchemy

### Caching Strategy
- Not implemented initially (complexity vs. benefit trade-off)
- Can add Redis for:
  - User session caching
  - Dashboard statistics cache (5-min TTL)
  - Notice board cache (1-hour TTL)

### Horizontal Scaling
- Stateless API servers (can run multiple instances)
- Database connection pooling for concurrent requests
- Supabase handles multi-region storage

## Deployment Architecture

```
┌─────────────┐
│ User Device │
└──────┬──────┘
       │ HTTPS
       ↓
┌──────────────────┐      ┌─────────────────┐
│   CDN / Load     │      │ Backend Servers │
│   Balancer       │─────→│  (FastAPI)      │
└──────────────────┘      └────────┬────────┘
                                   │
                          ┌────────┴──────────┐
                          ↓                   ↓
                      ┌──────┐           ┌──────────┐
                      │  DB  │           │Supabase  │
                      │(Postgre)         │ Storage  │
                      └──────┘           └──────────┘
```

## Future Enhancements

1. **Advanced Analytics**: Reports on response time trends
2. **Bulk Operations**: Upload multiple complaints
3. **Mobile App**: Native iOS/Android apps
4. **SMS Notifications**: In addition to email
5. **SLA Management**: Auto-escalate overdue complaints
6. **Payment Integration**: Maintenance fee collection
7. **Predictive Analytics**: Identify common issues
8. **Integration APIs**: Third-party system connections
