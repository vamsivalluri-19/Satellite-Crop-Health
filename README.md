## Satellite Crop Health Monitoring

End-to-end crop monitoring app with a Flask backend and a rich dashboard UI. It combines NDVI-based health checks, AI-style disease detection (simulated), weather lookups, recommendations, and soil health guidance.

Live site:

https://satellite-crop-health.onrender.com

## Features

- Crop health checks using NDVI (simulated satellite data)
- Disease detection from uploaded images with confidence and treatment tips
- Weather and forecast lookups (Open-Meteo API)
- Location-based weather via Google Maps
- Crop database with season filters
- Maintenance guides and soil health analysis
- User authentication, profiles, and history tracking

## Tech Stack

- Backend: Flask, Flask-SQLAlchemy, Flask-Session
- Frontend: HTML, CSS, vanilla JavaScript
- Data: SQLite for local storage

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies.
3. Start the server.

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the App

```bash
python run.py
```

The app runs at:

```
http://localhost:5000
```

Demo login:

- Username: demo
- Password: demo123

## Environment Variables

Optional SMTP settings for email alerts:

- `SMTP_SERVER`
- `SMTP_PORT`
- `SENDER_EMAIL`
- `SENDER_PASSWORD`

If not configured, email alerts are skipped and the app continues normally.

## Key API Endpoints

- `GET /health` - Service health check
- `POST /register` - Create a user
- `POST /login` - Login
- `POST /logout` - Logout
- `GET /session` - Session check
- `GET/PUT /profile` - Profile details
- `POST /ndvi` - Crop health check
- `GET /weather` - Weather data
- `GET /weather-forecast` - Forecast data
- `POST /disease-detect` - Disease detection
- `GET /history` - User history
- `GET /crop-database` - Crop data
- `POST /crop-recommendations` - Recommendations
- `GET /maintenance-guide/<crop>` - Maintenance guide
- `POST /soil-health` - Soil analysis

## Project Structure

```
backend/
	app.py
	ai_model.py
	alerts.py
	satellite_data.py
	weather_data.py
frontend/
	static/
		style.css
		script.js
		templates/
			index.html
run.py
requirements.txt
```

## Notes

- NDVI and disease detection are simulated for demo purposes.
- Weather uses Open-Meteo (no API key required).
- Google Maps requires a valid API key in the script tag in the HTML.

## Troubleshooting

- Blank page: make sure `index.html` is in `frontend/static/templates` and the server is running.
- Weather map not loading: check the Google Maps API key and network access.
- Missing data: confirm the backend is running on port 5000.

## Deploy (Render - Free)

This project includes `render.yaml` for one-click deployment.

1. Push the repo to GitHub.
2. In Render, create a new Web Service and connect your GitHub repo.
3. Render will detect `render.yaml` and configure build/start commands.
4. Once deployed, open the public Render URL to access the app.

Notes:

- The SQLite database resets on each deploy.
- Email alerts are disabled unless you add SMTP env vars in Render.

### Required Render Env Vars (Optional)

- `SMTP_SERVER`
- `SMTP_PORT`
- `SENDER_EMAIL`
- `SENDER_PASSWORD`
