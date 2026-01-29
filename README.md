# Stock Signals SaaS

A complete SaaS platform for stock trading signals with user authentication, Stripe/Razorpay billing, Redis caching, and a modern React dashboard.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│   SQLite/       │
│   (Frontend)    │ JWT │   (Backend)     │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │                       ▼
        │               ┌─────────────────┐
        │               │     Redis       │
        │               │  (Cache/Rate)   │
        │               └─────────────────┘
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│     Stripe      │     │    Razorpay     │
│   (Payments)    │     │   (Payments)    │
└─────────────────┘     └─────────────────┘
```

## ✨ Features

- **User Authentication**: JWT-based signup/login with bcrypt password hashing
- **Rate Limiting**: Redis-based rate limiting (5 requests/minute)
- **Dual Payment Gateways**: Support for both Stripe AND Razorpay
- **Webhook Idempotency**: Prevents duplicate subscription grants
- **Signal Caching**: Redis caching with 5-minute TTL
- **Access Control**: Free users see 3 signals, paid users see all 8

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Redis Server (optional for local dev)
- Stripe OR Razorpay Account

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your credentials

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuration

### Backend (.env)

```env
# Payment Gateway Selection (stripe or razorpay)
PAYMENT_GATEWAY=razorpay

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID=price_xxx

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAY_WEBHOOK_SECRET=xxx
RAZORPAY_PLAN_AMOUNT=49900  # ₹499 in paise
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login and get JWT |
| GET | `/auth/me` | Get current user |

### Billing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/billing/create-checkout` | Create checkout (auto-selects gateway) |
| POST | `/billing/stripe/create-checkout` | Create Stripe checkout |
| POST | `/billing/razorpay/create-order` | Create Razorpay order |
| POST | `/billing/razorpay/verify-payment` | Verify Razorpay payment |
| GET | `/billing/gateway-info` | Get available gateways |

### Signals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/signals` | Get trading signals (protected) |

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
pytest -v
```

### Test Webhooks Locally

**Stripe:**
```bash
stripe listen --forward-to localhost:8000/billing/stripe/webhook
```

**Razorpay:**
Use ngrok or similar to expose localhost, then configure webhook URL in Razorpay dashboard.

## 🔒 Payment Gateway Selection

The frontend shows payment buttons for available gateways:
- If only Stripe is configured → Shows Stripe button
- If only Razorpay is configured → Shows Razorpay button
- If both are configured → Shows both buttons

Set `PAYMENT_GATEWAY` in `.env` to choose the default.

## 📁 Project Structure

```
stock-signals-saas/
├── backend/
│   ├── app/
│   │   ├── middleware/         # Rate limiting
│   │   ├── models/             # SQLAlchemy models
│   │   ├── routers/
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── billing.py      # Dual gateway support
│   │   │   └── signals.py      # Trading signals
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/
│   │   │   ├── auth.py         # Auth service
│   │   │   ├── stripe_service.py
│   │   │   ├── razorpay_service.py
│   │   │   └── redis_service.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # Reusable components
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Both payment options
│   │   │   ├── Login.jsx
│   │   │   └── Signup.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── README.md
└── DEPLOYMENT.md
```

## 📝 License

MIT
