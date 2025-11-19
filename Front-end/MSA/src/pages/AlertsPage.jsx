import { useState, useEffect } from 'react';
import { getAlerts } from '../utils/chatApi';
import './AlertsPage.css';

const AlertsPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const data = await getAlerts();
        // Transform string alerts into structured objects
        const structuredAlerts = data.map((alertText, index) => ({
          id: index + 1,
          text: alertText,
          type: extractType(alertText),
          severity: extractSeverity(alertText),
          location: extractLocation(alertText),
          description: alertText,
          status: 'active',
          time: 'Recent'
        }));
        setAlerts(structuredAlerts);
      } catch (err) {
        setError('Failed to fetch alerts. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, []);

  const extractType = (text) => {
    if (text.toLowerCase().includes('fire')) return 'Fire Safety';
    if (text.toLowerCase().includes('electrical')) return 'Electrical Safety';
    if (text.toLowerCase().includes('transport') || text.toLowerCase().includes('vehicle')) return 'Transportation';
    if (text.toLowerCase().includes('roof fall') || text.toLowerCase().includes('structural')) return 'Structural';
    if (text.toLowerCase().includes('ventilation') || text.toLowerCase().includes('gas')) return 'Ventilation';
    if (text.toLowerCase().includes('equipment') || text.toLowerCase().includes('machinery')) return 'Equipment';
    if (text.toLowerCase().includes('unauthorized')) return 'Access Control';
    if (text.toLowerCase().includes('training') || text.toLowerCase().includes('protocol')) return 'Safety Protocol';
    return 'Safety Alert';
  };

  const extractSeverity = (text) => {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('critical') || lowerText.includes('immediate') || lowerText.includes('urgent')) return 'critical';
    if (lowerText.includes('high') || lowerText.includes('prioritize') || lowerText.includes('enhance')) return 'high';
    return 'high';
  };

  const extractLocation = (text) => {
    // Extract location names from text
    const locationMatch = text.match(/in ([A-Z][a-z]+(?:'s)?\s*[A-Z]?[a-z]*(?:\s+[A-Z][a-z]+)*)/);
    if (locationMatch) return locationMatch[1];
    
    // Common location keywords
    if (text.includes('Chhattisgarh')) return 'Chhattisgarh';
    if (text.includes('Jharkhand')) return 'Jharkhand';
    if (text.includes('Korba')) return 'Korba district';
    if (text.includes('Prakasam')) return 'Prakasam district';
    if (text.includes('West Bengal')) return 'West Bengal';
    if (text.includes('coal mining')) return 'Coal Mining Areas';
    if (text.includes('granite')) return 'Granite Mining Areas';
    
    return 'Multiple Locations';
  };

  const getSeverityClass = (severity) => {
    if (!severity) return 'high';
    return severity.toLowerCase() === 'critical' ? 'critical' : 'high';
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

  const getSeverityIcon = (type) => {
    const icons = {
      'Fire': '🔥',
      'Short Circuit': '⚡',
      'Landslide': '⛰️',
      'Faulty Equipment': '⚙️',
      'Gas Leak': '💨',
      'Structural Damage': '🏗️',
      'Equipment Failure': '⚙️',
      'Ventilation': '💨',
      'Safety Protocol': '⚠️'
    };
    return icons[type] || '⚠️';
  };

  if (loading) {
    return (
      <div className="alerts-page">
        <div className="page-header">
          <h1>Critical Alerts</h1>
          <p>Loading alerts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alerts-page">
        <div className="page-header">
          <h1>Critical Alerts</h1>
          <p className="error-message">{error}</p>
        </div>
      </div>
    );
  }

  const criticalCount = alerts.filter(a => a.severity === 'critical').length;
  const highCount = alerts.filter(a => a.severity === 'high').length;
  const resolvedCount = alerts.filter(a => a.status === 'resolved').length;

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1>Critical Alerts</h1>
        <p>Real-time monitoring of critical safety incidents requiring immediate attention</p>
      </div>

      <div className="alerts-summary">
        <div className="summary-card critical">
          <span className="summary-number">{criticalCount}</span>
          <span className="summary-label">Critical Alerts</span>
        </div>
        <div className="summary-card high">
          <span className="summary-number">{highCount}</span>
          <span className="summary-label">High Priority</span>
        </div>
        <div className="summary-card resolved">
          <span className="summary-number">{resolvedCount}</span>
          <span className="summary-label">Resolved Today</span>
        </div>
      </div>

      <div className="alerts-grid">
        {alerts.length > 0 ? (
          alerts.map((alert) => {
            const statusInfo = getStatusBadge(alert.status || 'active');
            return (
              <div key={alert.id} className={`alert-card ${getSeverityClass(alert.severity)}`}>
                <div className="alert-header">
                  <span className="alert-icon">{getSeverityIcon(alert.type)}</span>
                  <div className="alert-title-group">
                    <h3>{alert.type}</h3>
                    <span className="alert-time">{alert.time}</span>
                  </div>
                  <span className={`status-badge ${statusInfo.class}`}>{statusInfo.text}</span>
                </div>
                <p className="alert-location">📍 {alert.location}</p>
                <p className="alert-description">{alert.description}</p>
              </div>
            );
          })
        ) : (
          <div className="no-alerts">
            <p>✓ No active alerts at this time</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsPage;
