# AI Travel Planner

A modern travel planning application powered by AI that helps users discover destinations, plan trips, and find accommodations. Built with React, Django, and Google's Gemini AI.

## Features

-  AI-powered travel assistant
-  Destination discovery and recommendations
- Hotel and accommodation search
- Trip planning and itinerary generation
- Location information and details
- Booking management
- Travel guides and tips

## Tech Stack

### Frontend
- React 18+
- Vite
- React Router
- CSS Modules
- Font Awesome Icons

### Backend
- Django 5.0
- Django REST Framework
- Google Gemini AI
- PostgreSQL (optional)

## Getting Started

### Prerequisites
- Node.js 16+
- Python 3.10+
- pip
- virtualenv (recommended)

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the backend directory with:
```
DJANGO_SECRET_KEY=your_secret_key
GOOGLE_API_KEY=your_gemini_api_key
DEBUG=True
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Development

### Available Scripts

Frontend:
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

Backend:
- `python manage.py runserver` - Start Django development server
- `python manage.py makemigrations` - Create database migrations
- `python manage.py migrate` - Apply database migrations
- `python manage.py createsuperuser` - Create admin user

### Project Structure

```
frontend/
  ├── src/
  │   ├── components/   # React components
  │   ├── styles/       # CSS modules
  │   ├── assets/       # Static assets
  │   └── api.js        # API client
  └── ...

backend/
  ├── assistant/        # AI chat & classification
  ├── Location/         # Destination management
  ├── Booking/          # Booking system
  ├── Accounts/         # User authentication
  └── ...
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

