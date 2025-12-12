# TorqCare - Complete Setup & Deployment Guide

## 🚀 Project Overview

TorqCare is an autonomous multi-agent network for intelligent vehicle care that combines real-time telemetry monitoring, predictive maintenance, AI-powered diagnostics, and automated scheduling.

### Key Features
- ✅ Real-time vehicle telemetry monitoring
- ✅ ML-based failure prediction
- ✅ AI chatbot for customer engagement
- ✅ Automatic appointment scheduling
- ✅ Manufacturing quality insights
- ✅ Feedback management system

---

## 📋 Prerequisites

### Required Software
- Python 3.9+
- Node.js 16+ & npm
- PostgreSQL 13+
- Git

### Recommended Tools
- Docker & Docker Compose (for containerized deployment)
- Ollama (for local LLM)
- VS Code or PyCharm
- Postman (for API testing)

---

## 🛠️ Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/torqcare.git
cd torqcare
```

### Step 2: Backend Setup

#### 2.1 Create Python Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### 2.2 Install Python Dependencies

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
pip install pandas numpy scikit-learn joblib
pip install python-multipart websockets
pip install langchain langchain-community
pip install requests httpx
```

Create `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
joblib==1.3.2
python-multipart==0.0.6
websockets==12.0
langchain==0.0.350
langchain-community==0.0.1
requests==2.31.0
httpx==0.25.2
python-dotenv==1.0.0
```

#### 2.3 Setup PostgreSQL Database

```bash
# Install PostgreSQL (if not already installed)
# On Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# On macOS
brew install postgresql

# On Windows
# Download from https://www.postgresql.org/download/windows/

# Start PostgreSQL service
sudo service postgresql start

# Create database and user
sudo -u postgres psql

postgres=# CREATE DATABASE torqcare_db;
postgres=# CREATE USER torqcare_user WITH PASSWORD 'your_secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE torqcare_db TO torqcare_user;
postgres=# \q
```

#### 2.4 Configure Environment Variables

Create `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://torqcare_user:your_secure_password@localhost:5432/torqcare_db

# API Keys (if using cloud LLMs)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

#### 2.5 Initialize Database

```bash
# Run database initialization
python database/connection.py

# The script will:
# - Create all tables
# - Set up relationships
# - Seed sample data
```

#### 2.6 Setup Ollama (Local LLM)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model (choose one)
ollama pull llama2        # 7B parameters
ollama pull mistral       # 7B parameters
ollama pull llama2:13b    # 13B parameters (better quality, needs more RAM)

# Start Ollama server
ollama serve
```

### Step 3: Frontend Setup

#### 3.1 Navigate to Frontend Directory

```bash
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install

# If you encounter issues, try:
npm install --legacy-peer-deps
```

#### 3.3 Configure Frontend Environment

Create `.env.local`:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

---

## 📁 Project Structure

```
torqcare/
├── backend/
│   ├── main.py                     # FastAPI application
│   ├── agents/
│   │   ├── orchestrator.py         # Central agent coordinator
│   │   ├── data_analysis_agent.py  # Telemetry analysis
│   │   ├── diagnosis_agent.py      # Failure prediction
│   │   ├── customer_engagement_agent.py  # Chatbot
│   │   ├── scheduling_agent.py     # Appointment scheduling
│   │   ├── quality_insights_agent.py  # Quality analytics
│   │   └── feedback_agent.py       # Feedback management
│   ├── ml_models/
│   │   ├── prediction_model.py     # ML prediction models
│   │   ├── anomaly_detection.py    # Anomaly detection
│   │   └── trained_models/         # Saved model files
│   ├── database/
│   │   ├── connection.py           # Database connection
│   │   ├── models.py               # SQLAlchemy models
│   │   └── schema.sql              # SQL schema
│   ├── utils/
│   │   ├── auth.py                 # Authentication utilities
│   │   └── helpers.py              # Helper functions
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Monitoring.jsx
│   │   │   ├── Chatbot.jsx
│   │   │   ├── Appointments.jsx
│   │   │   └── Feedback.jsx
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── .env.local
├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── AGENT_ARCHITECTURE.md
│   └── DATABASE_SCHEMA.md
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_ml_models.py
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 🚀 Running the Application

### Option 1: Development Mode

#### Terminal 1 - Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

#### Terminal 2 - Start Frontend

```bash
cd frontend
npm start
```

Frontend will be available at: `http://localhost:3000`

#### Terminal 3 - Start Ollama (if using local LLM)

```bash
ollama serve
```

### Option 2: Docker Deployment

#### Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: torqcare_db
      POSTGRES_USER: torqcare_user
      POSTGRES_PASSWORD: your_secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://torqcare_user:your_secure_password@postgres:5432/torqcare_db
      OLLAMA_BASE_URL: http://ollama:11434
    depends_on:
      - postgres
      - ollama
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - backend

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

#### Run with Docker:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🧪 Testing the System

### 1. Test Backend API

```bash
# Health check
curl http://localhost:8000/

# Get agent status
curl http://localhost:8000/api/agents/status

# Submit sensor data
curl -X POST http://localhost:8000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "VEH001",
    "engine_temp": 98.5,
    "rpm": 2500,
    "fuel_level": 45,
    "tire_pressure_fl": 28,
    "tire_pressure_fr": 32,
    "tire_pressure_rl": 32,
    "tire_pressure_rr": 32,
    "battery_voltage": 11.8,
    "oil_pressure": 35,
    "brake_fluid_level": 75,
    "speed": 60
  }'
```

### 2. Test WebSocket Connection

```javascript
// Test in browser console
const ws = new WebSocket('ws://localhost:8000/ws/telemetry/VEH001');
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

### 3. Test ML Predictions

```bash
python -c "
from ml_models.prediction_model import VehicleFailurePredictionModel
model = VehicleFailurePredictionModel()
test_data = {
    'engine_temp': 102,
    'rpm': 2500,
    'battery_voltage': 11.5,
    'oil_pressure': 18
}
features = model.prepare_features(test_data)
print('Features prepared:', features.shape)
"
```

---

## 📊 PowerBI Integration

### Setup Power BI Dashboard

1. **Install Power BI Desktop**
   - Download from: https://powerbi.microsoft.com/desktop/

2. **Connect to PostgreSQL**
   ```
   Get Data → Database → PostgreSQL
   Server: localhost
   Database: torqcare_db
   Username: torqcare_user
   Password: your_secure_password
   ```

3. **Import Key Tables**
   - quality_insights
   - maintenance_history
   - predictions
   - feedback
   - v_vehicle_health_summary (view)
   - v_workshop_performance (view)

4. **Create Visualizations**
   - Failure trend analysis
   - Vehicle health scores
   - Workshop performance metrics
   - Feedback sentiment analysis
   - Cost analysis by failure type

---

## 🔧 Configuration Options

### Agent Configuration

Edit `agents/orchestrator.py` to customize:

```python
# Enable/disable agents
orchestrator.register_agent("data_analysis", data_agent)
orchestrator.register_agent("diagnosis", diagnosis_agent)
# ... etc

# Adjust thresholds
data_agent.baseline_thresholds['engine_temp']['critical'] = 100
```

### ML Model Configuration

Edit `ml_models/prediction_model.py`:

```python
# Adjust model parameters
self.models[failure_type] = RandomForestClassifier(
    n_estimators=200,  # Increase for better accuracy
    max_depth=15,
    random_state=42
)

# Adjust anomaly detection sensitivity
self.anomaly_threshold = 2.0  # Lower = more sensitive
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Test connection
psql -h localhost -U torqcare_user -d torqcare_db
```

#### 2. Ollama Not Responding
```bash
# Restart Ollama
pkill ollama
ollama serve

# Check if model is downloaded
ollama list
```

#### 3. Frontend Won't Start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm start
```

#### 4. Port Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in main.py
uvicorn main:app --port 8001
```

---

## 📈 Performance Optimization

### Database Optimization

```sql
-- Create additional indexes for frequent queries
CREATE INDEX idx_sensor_vehicle_recent ON sensor_data(vehicle_id, timestamp DESC) WHERE timestamp > NOW() - INTERVAL '7 days';

-- Partition large tables by date
CREATE TABLE sensor_data_2024_01 PARTITION OF sensor_data
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Enable query plan caching
SET shared_buffers = '256MB';
SET effective_cache_size = '1GB';
```

### API Performance

```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_vehicle_data(vehicle_id: str):
    # Cached for 5 minutes
    pass

# Enable connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0
)
```

---

## 🔐 Security Best Practices

1. **Change Default Passwords**
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

2. **Enable HTTPS**
   ```python
   # In main.py
   uvicorn.run(
       app,
       host="0.0.0.0",
       port=443,
       ssl_keyfile="/path/to/key.pem",
       ssl_certfile="/path/to/cert.pem"
   )
   ```

3. **Implement Rate Limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=lambda: request.client.host)
   
   @app.get("/api/sensor-data")
   @limiter.limit("100/minute")
   async def get_data():
       pass
   ```

---

## 📝 Next Steps

1. ✅ Complete this setup guide
2. 🔄 Train ML models with historical data
3. 🎨 Customize UI themes and branding
4. 🔗 Integrate with actual vehicle APIs
5. 📱 Develop mobile applications
6. ☁️ Deploy to cloud (AWS/Azure/GCP)
7. 📊 Set up monitoring and analytics
8. 🧪 Implement comprehensive testing

---

## 📞 Support & Resources

- **Documentation**: `/docs` directory
- **API Reference**: `http://localhost:8000/docs`
- **GitHub Issues**: Report bugs and feature requests
- **Community**: Join discussions

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ by the TorqCare Team**