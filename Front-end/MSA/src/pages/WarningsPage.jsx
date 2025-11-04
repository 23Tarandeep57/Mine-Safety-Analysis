import './WarningsPage.css';

const WarningsPage = () => {
  const warnings = [
    {
      id: 1,
      type: 'Weather',
      title: 'Heavy Rainfall Warning',
      severity: 'high',
      time: '2 hours ago',
      description: 'Meteorological department predicts 150mm rainfall in next 48 hours. Potential for flooding in low-lying areas.',
      icon: '🌧️',
      impacts: ['Flooding risk', 'Reduced visibility', 'Equipment damage'],
      recommendations: ['Inspect drainage systems', 'Secure loose materials', 'Prepare emergency pumps']
    },
    {
      id: 2,
      type: 'Seismic',
      title: 'Earthquake Activity',
      severity: 'medium',
      time: '6 hours ago',
      description: 'Minor seismic activity (3.2 magnitude) detected 45km from site. No immediate danger but monitoring continues.',
      icon: '🌍',
      impacts: ['Structural stress', 'Equipment misalignment', 'Power disruption'],
      recommendations: ['Check structural integrity', 'Secure heavy equipment', 'Review evacuation plans']
    },
    {
      id: 3,
      type: 'Cascade Risk',
      title: 'Power Failure Cascade',
      severity: 'high',
      time: '8 hours ago',
      description: 'Earthquake can trigger power grid failures, leading to ventilation system shutdown and gas accumulation.',
      icon: '⚠️',
      impacts: ['Ventilation failure', 'Gas accumulation', 'Communication loss'],
      recommendations: ['Test backup generators', 'Check gas sensors', 'Verify emergency protocols']
    },
    {
      id: 4,
      type: 'Environmental',
      title: 'High Temperature Alert',
      severity: 'medium',
      time: '12 hours ago',
      description: 'Ambient temperature forecast to exceed 42°C. Increased risk of heat-related incidents and equipment stress.',
      icon: '🌡️',
      impacts: ['Worker fatigue', 'Equipment overheating', 'Fire risk increase'],
      recommendations: ['Increase hydration breaks', 'Monitor equipment temps', 'Adjust work schedules']
    },
    {
      id: 5,
      type: 'Air Quality',
      title: 'Dust Storm Approaching',
      severity: 'medium',
      time: '1 day ago',
      description: 'Regional dust storm expected to reach site by evening. Will affect air quality and equipment operation.',
      icon: '💨',
      impacts: ['Respiratory hazards', 'Equipment contamination', 'Visibility reduction'],
      recommendations: ['Issue respirators', 'Cover sensitive equipment', 'Seal air intakes']
    },
    {
      id: 6,
      type: 'Geological',
      title: 'Ground Subsidence Detection',
      severity: 'high',
      time: '1 day ago',
      description: 'Ground monitoring sensors indicate gradual subsidence in Zone D-2. Rate: 2cm per week.',
      icon: '⛰️',
      impacts: ['Structural instability', 'Equipment damage', 'Access route closure'],
      recommendations: ['Restrict area access', 'Install additional sensors', 'Consult geological team']
    }
  ];

  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'high': return 'severity-high';
      case 'medium': return 'severity-medium';
      default: return 'severity-low';
    }
  };

  return (
    <div className="warnings-page">
      <div className="page-header">
        <h1>Potential Warnings</h1>
        <p>Predictive alerts for hazards that may impact operations and safety</p>
      </div>

      <div className="warnings-stats">
        <div className="stat-item high">
          <span className="stat-number">3</span>
          <span className="stat-label">High Priority</span>
        </div>
        <div className="stat-item medium">
          <span className="stat-number">3</span>
          <span className="stat-label">Medium Priority</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">24h</span>
          <span className="stat-label">Monitoring Window</span>
        </div>
      </div>

      <div className="warnings-grid">
        {warnings.map((warning) => (
          <div key={warning.id} className={`warning-card ${getSeverityClass(warning.severity)}`}>
            <div className="warning-header">
              <div className="warning-icon">{warning.icon}</div>
              <div className="warning-info">
                <div className="warning-type">{warning.type}</div>
                <h3>{warning.title}</h3>
                <span className="warning-time">{warning.time}</span>
              </div>
            </div>

            <p className="warning-description">{warning.description}</p>

            <div className="warning-section">
              <h4>Potential Impacts</h4>
              <ul className="impacts-list">
                {warning.impacts.map((impact, index) => (
                  <li key={index}>{impact}</li>
                ))}
              </ul>
            </div>

            <div className="warning-section">
              <h4>Recommendations</h4>
              <ul className="recommendations-list">
                {warning.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>

            <button className="acknowledge-btn">Acknowledge Warning</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WarningsPage;
