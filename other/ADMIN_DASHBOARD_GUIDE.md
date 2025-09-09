# LinguaFlex Admin Dashboard Guide

## Overview
The LinguaFlex Admin Dashboard provides a comprehensive interface for managing all aspects of the platform, including users, campaigns, bookings, lessons, payments, and more.

## Features

### Custom Admin Site
- **Custom Dashboard**: Enhanced dashboard with statistics and quick access to key features
- **Professional Design**: Custom CSS styling for a modern, intuitive interface
- **Centralized Management**: All models registered with the custom admin site

### Dashboard Statistics
The main dashboard displays:
- Total number of users, teachers, students
- Campaign statistics (total campaigns, recent sends)
- Booking metrics (upcoming sessions, completed sessions)
- Payment summaries
- System health indicators

### Model Administration

#### User Management (`core` app)
- **Users**: Manage user accounts with role-based access
- **User Profiles**: Detailed user information and preferences
- **Languages**: Manage supported languages

#### Account Management (`accounts` app)
- **Teacher Profiles**: Teacher-specific information and qualifications
- **Student Profiles**: Student learning preferences and progress

#### Campaign Management (`campaigns` app)
- **Campaigns**: Create and manage email campaigns
- **Campaign Recipients**: Track email delivery status
- **Email Statistics**: Monitor open rates, click rates, and delivery metrics

#### Booking Management (`bookings` app)
- **Sessions**: Manage tutoring sessions and appointments
- **Teachers**: Teacher availability and scheduling
- **Students**: Student booking history and preferences

#### Gig Management (in `accounts` app)
- **Gigs**: Freelance tutoring opportunities
- **Gig Reviews**: Rating and feedback system

#### Payment Management (`payments` app)
- **Payment Records**: Transaction history and status
- **Payment Refunds**: Refund processing and tracking

#### Blog Management (`blogs` app)
- **Blog Posts**: Content management
- **Blog Categories**: Content organization
- **Blog Views**: Analytics and engagement metrics

## Access & Security

### Admin Access
- Navigate to: `http://127.0.0.1:8000/admin/`
- Login with superuser credentials
- Role-based permissions ensure appropriate access levels

### Security Features
- Django's built-in CSRF protection
- User authentication and authorization
- Secure password handling
- Session management

## Admin Customizations

### Enhanced List Views
- Comprehensive list displays with key information
- Smart filtering options for quick data discovery
- Search functionality across relevant fields
- Bulk actions for efficient management

### Custom Actions
- Bulk email sending for campaigns
- Session status updates
- Payment processing actions
- User role management

### Data Integrity
- Readonly fields for system-generated data
- Validation for user inputs
- Foreign key relationships properly displayed
- Date hierarchies for time-based filtering

## Usage Tips

### Navigation
1. **Dashboard**: Start here for an overview of system status
2. **Quick Actions**: Use the sidebar for direct access to key functions
3. **Search**: Utilize the search functionality to quickly find specific records
4. **Filters**: Apply filters to narrow down large datasets

### Best Practices
- **Regular Monitoring**: Check dashboard statistics regularly
- **Data Cleanup**: Use bulk actions to maintain data quality
- **User Management**: Monitor user registrations and role assignments
- **Campaign Tracking**: Review email campaign performance regularly

### Troubleshooting
- **Server Issues**: Check the terminal for error messages
- **Permission Errors**: Verify user roles and permissions
- **Data Issues**: Use Django's admin validation messages as guidance

## Technical Details

### File Structure
```
rag_app/
├── admin_site.py          # Custom admin site configuration
└── urls.py               # Admin URL routing

templates/admin/
└── index.html            # Custom dashboard template

static/admin/css/
└── dashboard.css         # Custom admin styling

{app}/admin.py            # App-specific admin configurations
```

### Dependencies
- Django Admin framework
- Custom admin site implementation
- Enhanced model configurations
- CSS customizations

## Development & Maintenance

### Adding New Models
1. Create the model in the appropriate app
2. Add admin configuration in `{app}/admin.py`
3. Register with the custom admin site
4. Update this documentation

### Customizing Views
- Modify admin classes for specific display requirements
- Add custom actions for bulk operations
- Implement custom templates for enhanced UI

### Performance Optimization
- Use `select_related()` and `prefetch_related()` in admin queries
- Implement pagination for large datasets
- Optimize database queries in custom admin methods

---

**Note**: This admin dashboard is designed for development and testing. For production use, ensure proper security configurations and consider using Django's production-ready settings.
