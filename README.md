# 🚗 TorqCare - Autonomous Multi-Agent Vehicle Care Network

A comprehensive AI-powered vehicle care management system using multiple specialized agents for predictive maintenance, diagnostics, and customer engagement.

## 🌟 Features

### Multi-Agent System
1. **Data Analysis Agent** - Real-time telemetry monitoring and anomaly detection
2. **Diagnosis Agent** - ML-powered failure prediction and component identification
3. **Chatbot Agent** - Conversational AI for customer support
4. **Scheduling Agent** - Automatic appointment booking with workshops
5. **Quality Insights Agent** - Manufacturing defect pattern analysis
6. **Feedback Agent** - User feedback processing and sharing

### Technical Capabilities
- ⚡ Real-time monitoring of 100 electric vehicles
- 🤖 Machine Learning models (XGBoost, Random Forest, Gradient Boosting)
- 📊 20 different failure scenarios with predictive analytics
- 💬 LLM-powered conversational interface (Groq + Llama 3.1)
- 📅 Intelligent appointment scheduling
- 📈 Quality insights dashboard for manufacturers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              React Frontend (Vite)              │
│  Dashboard | Diagnostics | Chatbot | Maintenance│
└──────────────────┬──────────────────────────────┘
                   │ REST API / WebSocket
┌──────────────────┴──────────────────────────────┐
│           FastAPI Backend Server                │
│  ┌────────────────────────────────────────┐    │
│  │    Multi-Agent Orchestration Layer     │    │
│  │  [6 Specialized AI Agents with LLMs]   │    │
│  └────────────────────────────────────────┘    │
│  ┌──────────────┐  ┌─────────────────────┐    │
│  │  ML Models   │  │  Database Layer     │    │
│  │  (XGBoost,   │  │  (PostgreSQL)       │    │
│  │   RF, GB)    │  │  (SQLAlchemy ORM)   │    │
│  └──────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend)
- **PostgreSQL 15** (if running without Docker)
- **Groq API Key** (free tier available)

## 🚀 Quick Start with Docker

### 1. Clone and Setup

```bash
# Clone the repository (or create the structure)
mkdir torqcare && cd torqcare

# Create .env file
cat > backend/.env << EOF
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://torqcare_user:torqcare_pass@postgres:5432/torqcare_db
EOF
```

### 2. Get Groq API Key (Free)

1. Visit: https://console.groq.com
2. Sign up for free account
3. Create an API key
4. Add to `backend/.env` file

### 3. Generate Data and Train Models

```bash
# Generate mock data
python backend/utils/data_generator.py

# Train ML models
python ml_models/train_models.py
```

### 4. Start Services

```bash
# Build and start all services
docker-compose up --build

# Or use Make commands
make data    # Generate data
make train   # Train models
make build   # Build containers
make up      # Start services
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (optional)

## 🛠️ Local Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Generate data
python utils/data_generator.py

# Initialize database
python database/database.py

# Train models
cd ../ml_models
python train_models.py

# Run server
cd ../backend
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📊 Data Generation

The system generates realistic mock data for:

- **100 Electric Vehicles** (EV-00001 to EV-00100)
- **1,000 sensor readings** per vehicle (10-second intervals)
- **200 maintenance records** with repair history
- **20 failure scenarios** (Battery, Motor, Brake, Tire, etc.)
- **50 appointments** across 10 service centers
- **150 customer feedback** records

### Data Files Created

```
backend/data/
├── sensor_data.csv          (100,000 rows)
├── maintenance_history.csv  (200 rows)
├── appointments.csv         (50 rows)
├── feedback.csv             (150 rows)
└── workshops.csv            (10 rows)
```

## 🤖 ML Models

### Training Pipeline

```bash
python ml_models/train_models.py
```

### Models Trained

1. **Failure Classifier** (XGBoost)
   - Binary classification: Will vehicle fail?
   - Accuracy: ~95%

2. **Component Classifier** (Random Forest)
   - Multi-class: Which component will fail?
   - Identifies: Battery, Motor, Brake, Tire, Suspension

3. **RUL Estimator** (Gradient Boosting)
   - Regression: Remaining Useful Life in hours
   - R² Score: ~0.85

## 🔌 API Endpoints

### Vehicles
- `GET /api/vehicles` - List all vehicles
- `GET /api/vehicles/{vehicle_id}` - Get vehicle details
- `GET /api/vehicles/{vehicle_id}/health` - Get health summary

### Sensor Data
- `GET /api/sensor/{vehicle_id}/latest` - Latest reading
- `GET /api/sensor/{vehicle_id}/history` - Historical data
- `GET /api/sensor/{vehicle_id}/analyze` - Analyze for anomalies

### Diagnosis
- `POST /api/diagnosis/{vehicle_id}` - Run diagnosis

### Chatbot
- `POST /api/chat/{vehicle_id}?message=...` - Chat with assistant

### Appointments
- `GET /api/workshops` - List service centers
- `POST /api/appointments/propose/{vehicle_id}` - Get appointment options
- `POST /api/appointments/confirm` - Confirm appointment
- `GET /api/appointments/{vehicle_id}` - Get appointments

### Maintenance
- `GET /api/maintenance/{vehicle_id}` - Maintenance history

### Feedback
- `POST /api/feedback` - Submit feedback

### Quality Insights
- `GET /api/insights` - Get manufacturer insights

## 🎨 Frontend Components

### Dashboard
- Overall vehicle health score
- Component-wise health metrics
- Recent activity timeline
- Quick action buttons

### Diagnostics
- Real-time sensor readings
- Anomaly detection results
- AI-generated analysis reports
- System status indicators

### Chatbot
- Conversational interface
- Context-aware responses
- Vehicle-specific queries
- Appointment suggestions

### Maintenance
- Service history
- Upcoming appointments
- Repair details and costs
- Feedback submission

## 🧪 Testing

### Test Individual Agents

```bash
# Test Data Analysis Agent
cd backend/agents
python data_analysis_agent.py

# Test Diagnosis Agent
python diagnosis_agent.py

# Test Chatbot Agent
python chatbot_agent.py

# Test Scheduling Agent
python scheduling_agent.py
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get vehicle health
curl http://localhost:8000/api/vehicles/EV-00001/health

# Run diagnosis
curl -X POST http://localhost:8000/api/diagnosis/EV-00001
```

## 📈 Performance Metrics

- **Response Time**: < 200ms for most API calls
- **ML Inference**: < 50ms per prediction
- **Data Processing**: 100,000+ readings in < 5 seconds
- **Concurrent Users**: Supports 100+ simultaneous connections

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart postgres

# View logs
docker-compose logs postgres
```

### ML Model Errors

```bash
# Retrain models
rm -rf ml_models/trained_models/*.pkl
python ml_models/train_models.py
```

### API Key Issues

```bash
# Verify Groq API key
cat backend/.env | grep GROQ_API_KEY

# Test API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

## 📚 Project Structure

```
torqcare/
├── backend/
│   ├── agents/                    # AI Agents
│   │   ├── data_analysis_agent.py
│   │   ├── diagnosis_agent.py
│   │   ├── chatbot_agent.py
│   │   ├── scheduling_agent.py
│   │   ├── quality_insights_agent.py
│   │   └── feedback_agent.py
│   ├── models/                    # ML Models
│   │   └── predictive_models.py
│   ├── database/                  # Database Layer
│   │   ├── models.py
│   │   ├── database.py
│   │   └── crud.py
│   ├── utils/                     # Utilities
│   │   ├── data_generator.py
│   │   └── config.py
│   ├── data/                      # Generated Data
│   ├── main.py                    # FastAPI Server
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Main Application
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── ml_models/
│   ├── trained_models/           # Saved Models
│   └── train_models.py
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── Makefile
└── README.md
```

## 🤝 Contributing

This is a demonstration project. For production use:

1. Implement proper authentication and authorization
2. Add comprehensive error handling
3. Implement rate limiting
4. Add monitoring and logging (Prometheus, Grafana)
5. Implement CI/CD pipeline
6. Add comprehensive test suite
7. Implement data backup and recovery
8. Add security hardening

## 📄 License

This project is created for demonstration purposes.

## 🙏 Acknowledgments

- **LangChain** - Agent framework
- **Groq** - Fast LLM inference
- **FastAPI** - Modern web framework
- **React** - Frontend framework
- **PostgreSQL** - Robust database
- **scikit-learn & XGBoost** - ML libraries

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check agent logs in terminal
4. Verify all services are running: `docker-compose ps`

---

**Built with ❤️ using Multi-Agent AI Architecture**
