import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI, billingAPI, signalsAPI } from '../api/client';
import SignalTable from '../components/SignalTable';
import SubscribeButton from '../components/SubscribeButton';

function Dashboard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [user, setUser] = useState(null);
  const [signals, setSignals] = useState([]);
  const [isLimited, setIsLimited] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [gatewayInfo, setGatewayInfo] = useState(null);
  const [processingPayment, setProcessingPayment] = useState(false);

  useEffect(() => {
    // Check payment status from URL params
    const payment = searchParams.get('payment');
    if (payment === 'success') {
      setPaymentStatus('success');
    } else if (payment === 'cancelled') {
      setPaymentStatus('cancelled');
    }

    fetchData();
  }, [searchParams]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch user info
      const userResponse = await authAPI.getMe();
      setUser(userResponse.data);
      
      // Fetch signals
      const signalsResponse = await signalsAPI.getSignals();
      setSignals(signalsResponse.data.signals);
      setIsLimited(signalsResponse.data.is_limited);
      setTotalCount(signalsResponse.data.total_count);
      
      // Fetch gateway info
      try {
        const gatewayResponse = await billingAPI.getGatewayInfo();
        setGatewayInfo(gatewayResponse.data);
      } catch {
        // Gateway info fetch failed, use default
        setGatewayInfo({ active_gateway: 'stripe', available_gateways: ['stripe'] });
      }
      
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login');
      } else {
        setError('Failed to fetch data. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleSubscribe = async (gateway = null) => {
    setError('');
    setProcessingPayment(true);
    
    try {
      const selectedGateway = gateway || gatewayInfo?.active_gateway || 'stripe';
      const response = await billingAPI.createCheckout(selectedGateway);
      
      if (response.data.gateway === 'razorpay') {
        // Handle Razorpay checkout
        await handleRazorpayCheckout(response.data);
      } else {
        // Handle Stripe - redirect to checkout URL
        window.location.href = response.data.checkout_url;
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create checkout session');
      setProcessingPayment(false);
    }
  };

  const handleRazorpayCheckout = async (orderData) => {
    // Load Razorpay script if not already loaded
    if (!window.Razorpay) {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;
      document.body.appendChild(script);
      await new Promise(resolve => script.onload = resolve);
    }

    const options = {
      key: orderData.key_id,
      amount: orderData.amount,
      currency: orderData.currency,
      name: 'Stock Signals',
      description: 'Premium Subscription - ₹499',
      order_id: orderData.order_id,
      handler: async function(response) {
        // Verify payment on backend
        try {
          await billingAPI.verifyRazorpayPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          // Refresh data to show premium status
          setPaymentStatus('success');
          fetchData();
        } catch (err) {
          setError('Payment verification failed. Please contact support.');
        }
        setProcessingPayment(false);
      },
      modal: {
        ondismiss: function() {
          setProcessingPayment(false);
        }
      },
      prefill: {
        email: user?.email || '',
      },
      theme: {
        color: '#6366f1'
      }
    };

    const razorpay = new window.Razorpay(options);
    razorpay.open();
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>📈 Stock Signals</h1>
        </div>
        <div className="header-right">
          <span className="user-email">{user?.email}</span>
          <span className={`subscription-badge ${user?.is_paid ? 'paid' : 'free'}`}>
            {user?.is_paid ? '👑 Premium' : 'Free'}
          </span>
          <button onClick={handleLogout} className="btn btn-secondary">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {error && <div className="error-message">{error}</div>}
        
        {paymentStatus === 'success' && (
          <div className="success-message">
            🎉 Payment successful! You now have premium access.
          </div>
        )}
        
        {paymentStatus === 'cancelled' && (
          <div className="warning-message">
            Payment was cancelled. You can try again anytime.
          </div>
        )}

        <div className="signals-section">
          <div className="section-header">
            <h2>Today's Signals</h2>
            {isLimited && (
              <span className="limited-badge">
                Showing {signals.length} of {totalCount} signals
              </span>
            )}
          </div>

          <SignalTable signals={signals} />

          {isLimited && (
            <div className="upgrade-prompt">
              <div className="upgrade-content">
                <h3>🔒 Unlock All {totalCount} Signals</h3>
                <p>Upgrade to premium for just ₹499 and get access to all trading signals!</p>
                
                <div className="payment-options">
                  {gatewayInfo?.available_gateways?.includes('razorpay') && (
                    <SubscribeButton 
                      onClick={() => handleSubscribe('razorpay')} 
                      label="Pay with Razorpay"
                      icon="💳"
                      disabled={processingPayment}
                    />
                  )}
                  {gatewayInfo?.available_gateways?.includes('stripe') && (
                    <SubscribeButton 
                      onClick={() => handleSubscribe('stripe')} 
                      label="Pay with Stripe"
                      icon="💎"
                      disabled={processingPayment}
                    />
                  )}
                  {(!gatewayInfo?.available_gateways || gatewayInfo.available_gateways.length === 0) && (
                    <SubscribeButton 
                      onClick={() => handleSubscribe()} 
                      disabled={processingPayment}
                    />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
