import './AlertsPage.css';

const AlertsPage = () => {
  const criticalAlerts = [
    {
      id: 1,
      type: 'Fire',
      location: 'Zone A-3, Level 2',
      severity: 'critical',
      time: '15 minutes ago',
      description: 'Fire detection system triggered in machinery room. Emergency response team dispatched.',
      status: 'active',
      icon: '🔥'
    },
    {
      id: 2,
      type: 'Short Circuit',
      location: 'Zone B-1, Main Power Grid',
      severity: 'critical',
      time: '1 hour ago',
      description: 'Major electrical fault detected in primary distribution panel. Power redirected to backup.',
      status: 'active',
      icon: '⚡'
    },
    {
      id: 3,
      type: 'Landslide',
      location: 'Eastern Slope, Section 4',
      severity: 'high',
      time: '3 hours ago',
      description: 'Ground sensors indicate unstable slope conditions. Area evacuated and cordoned off.',
      status: 'monitoring',
      icon: '⛰️'
    },
    {
      id: 4,
      type: 'Faulty Equipment',
      location: 'Zone C-2, Drill Station 7',
      severity: 'high',
      time: '5 hours ago',
      description: 'Hydraulic drill showing abnormal pressure readings. Operations suspended pending inspection.',
      status: 'investigating',
      icon: '⚙️'
    },
    {
      id: 5,
      type: 'Gas Leak',
      location: 'Zone A-3, Ventilation Shaft',
      severity: 'critical',
      time: '8 hours ago',
      description: 'Elevated methane levels detected. Ventilation systems operating at maximum capacity.',
      status: 'resolved',
      icon: '💨'
    },
    {
      id: 6,
      type: 'Structural Damage',
      location: 'Zone B-5, Support Beam 12',
      severity: 'high',
      time: '12 hours ago',
      description: 'Stress fractures detected in primary support structure. Reinforcement work in progress.',
      status: 'investigating',
      icon: '🏗️'
    }
  ];

  const getSeverityClass = (severity) => {
    return severity === 'critical' ? 'critical' : 'high';
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { text: 'Active', class: 'status-active' },
      monitoring: { text: 'Monitoring', class: 'status-monitoring' },
      investigating: { text: 'Investigating', class: 'status-investigating' },
      resolved: { text: 'Resolved', class: 'status-resolved' }
    };
    return statusConfig[status] || statusConfig.active;
  };

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1>Critical Alerts</h1>
        <p>Real-time monitoring of critical safety incidents requiring immediate attention</p>
      </div>

      <div className="alerts-summary">
        <div className="summary-card critical">
          <span className="summary-number">3</span>
          <span className="summary-label">Critical Alerts</span>
        </div>
        <div className="summary-card high">
          <span className="summary-number">3</span>
          <span className="summary-label">High Priority</span>
        </div>
        <div className="summary-card resolved">
          <span className="summary-number">1</span>
          <span className="summary-label">Resolved Today</span>
        </div>
      </div>

      <div className="alerts-container">
        {criticalAlerts.map((alert) => (
          <div key={alert.id} className={`alert-card ${getSeverityClass(alert.severity)}`}>
            <div className="alert-icon">{alert.icon}</div>
            
            <div className="alert-content">
              <div className="alert-header">
                <div className="alert-title">
                  <h3>{alert.type}</h3>
                  <span className={`status-badge ${getStatusBadge(alert.status).class}`}>
                    {getStatusBadge(alert.status).text}
                  </span>
                </div>
                <span className="alert-time">{alert.time}</span>
              </div>
              
              <div className="alert-location">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                {alert.location}
              </div>
              
              <p className="alert-description">{alert.description}</p>
              
              <div className="alert-actions">
                <button className="action-btn primary">View Details</button>
                <button className="action-btn secondary">Update Status</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsPage;
