function SubscribeButton({ onClick, label, icon, disabled }) {
  return (
    <button 
      onClick={onClick} 
      className="btn btn-subscribe"
      disabled={disabled}
    >
      <span className="subscribe-icon">{icon || '⚡'}</span>
      <span className="subscribe-text">
        <span className="subscribe-label">{label || 'Upgrade to Premium'}</span>
        <span className="subscribe-price">₹499 one-time</span>
      </span>
    </button>
  );
}

export default SubscribeButton;
