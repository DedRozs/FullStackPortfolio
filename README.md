# Full Stack Portfolio

A modern portfolio website built with Django and React, following Clean Architecture and Domain-Driven Design principles.

## Tech Stack

### Backend
- Python 3.12+
- Django 6.0
- SQLite (development) / PostgreSQL (production)

### Frontend
- React 19
- TypeScript 5.9
- Vite 7
- Tailwind CSS 4
- React Router DOM

## Architecture

This project implements a **modular monolith** architecture with clear separation of concerns:

```
apps/{context}/
├── domain/           # Entities, Value Objects, Repository interfaces
├── application/      # Services, Commands, Queries (use cases)
├── infrastructure/   # Django ORM models, Repository implementations
└── presentation/     # Views (API controllers), URLs, Admin
```

**Bounded Contexts:**
- `blog` - Blog posts and tags management
- `contact` - Contact form submissions
- `shared` - Shared domain concepts and infrastructure

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   
   # Windows
   .\.venv\Scripts\Activate.ps1
   
   # macOS/Linux
   source .venv/bin/activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```bash
   python manage.py migrate
   ```

4. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. For development (with hot reload):
   ```bash
   npm run dev
   ```

4. For production build:
   ```bash
   npm run build
   ```

## Development

### Running Both Servers

For full-stack development:

1. Start Django backend: `python manage.py runserver`
2. In another terminal, start Vite dev server: `cd frontend && npm run dev`

### Building for Production

1. Build the frontend: `cd frontend && npm run build`
2. Django will serve the built React app from `staticfiles/frontend/`

## API Endpoints

- `/api/blog/` - Blog posts and tags
- `/api/contact/` - Contact form submissions
- `/admin/` - Django admin interface

All other routes serve the React SPA.

## Project Structure

```
├── apps/                   # Django applications (bounded contexts)
│   ├── blog/              # Blog context
│   ├── contact/           # Contact context
│   └── shared/            # Shared domain & infrastructure
├── core/                   # Django project settings
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # Reusable React components
│   │   └── pages/         # Page components
│   └── public/            # Static assets
├── staticfiles/           # Collected static files (auto-generated)
├── manage.py
├── requirements.txt
└── README.md
```

## Author

**Joseph Prince**
- LinkedIn: [thejprince](https://www.linkedin.com/in/thejprince/)
- GitHub: [DedRozs](https://github.com/DedRozs)

## License

This project is licensed under the MIT License.
