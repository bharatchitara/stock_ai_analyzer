# Stock Market News AI - Project Instructions

## Project Overview
This is a Django-based application for tracking Indian stock market news before 9:10 AM market opening with AI-powered categorization and recommendations.

## Technology Stack
- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **AI/ML**: OpenAI API, Transformers
- **Frontend**: Django Templates, Bootstrap 5, Chart.js
- **Background Tasks**: Celery, Redis
- **News Sources**: Indian financial news websites

## Project Structure
- `news/` - News scraping and storage
- `analysis/` - AI-powered news analysis
- `dashboard/` - Frontend dashboard
- `core/` - Project settings and utilities

## Key Features
1. Automated news collection before market hours
2. AI-powered sentiment analysis and categorization
3. Stock recommendations based on news impact
4. Real-time dashboard with charts
5. Mobile-responsive design

## Development Guidelines
- Follow Django best practices
- Use class-based views where appropriate
- Implement proper error handling
- Add logging for debugging
- Use environment variables for sensitive data