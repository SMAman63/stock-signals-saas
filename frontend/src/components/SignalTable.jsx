function SignalTable({ signals }) {
  const getActionClass = (action) => {
    switch (action) {
      case 'BUY':
        return 'action-buy';
      case 'SELL':
        return 'action-sell';
      case 'HOLD':
        return 'action-hold';
      default:
        return '';
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!signals || signals.length === 0) {
    return (
      <div className="no-signals">
        <p>No signals available at the moment.</p>
      </div>
    );
  }

  return (
    <div className="signal-table-container">
      <table className="signal-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Action</th>
            <th>Price</th>
            <th>Target</th>
            <th>Stop Loss</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((signal, index) => (
            <tr key={index}>
              <td className="symbol-cell">
                <span className="symbol">{signal.symbol}</span>
              </td>
              <td>
                <span className={`action-badge ${getActionClass(signal.action)}`}>
                  {signal.action}
                </span>
              </td>
              <td className="price-cell">{formatPrice(signal.price)}</td>
              <td className="target-cell">{formatPrice(signal.target)}</td>
              <td className="stoploss-cell">{formatPrice(signal.stop_loss)}</td>
              <td className="time-cell">{formatTime(signal.timestamp)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SignalTable;
