import './HomePage.css';

const HomePage = () => {
  const commonPatterns = [
    { type: 'Equipment Failure', percentage: 23, incidents: 34, trend: 'up' },
    { type: 'Ventilation Issues', percentage: 18, incidents: 27, trend: 'down' },
    { type: 'Human Error', percentage: 15, incidents: 22, trend: 'stable' },
    { type: 'Structural Collapse', percentage: 12, incidents: 18, trend: 'down' }
  ];

  const stats = [
    { label: 'Total Incidents Analyzed', value: '1,247', icon: '📊' },
    { label: 'Active Monitoring Sites', value: '38', icon: '🏭' },
    { label: 'Safety Recommendations', value: '156', icon: '✅' },
    { label: 'Days Without Incident', value: '12', icon: '📅' }
  ];

  return (
    <div className="homepage">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>Mine Safety Intelligence System</h1>
          <p className="hero-description">
            Our advanced AI-powered platform represents a paradigm shift in mining safety management. 
            Through comprehensive analysis of historical incident data, real-time environmental monitoring, 
            and predictive modeling, we deliver actionable insights that save lives. Our commitment extends 
            beyond technology—we partner with mining operations to cultivate a culture of safety, ensuring 
            every worker returns home safely. With deep learning algorithms analyzing patterns across 
            thousands of incidents, we identify risks before they materialize, transforming reactive 
            safety measures into proactive protection.
          </p>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="stats-section">
        <div className="stats-grid">
          {stats.map((stat, index) => (
            <div key={index} className="stat-card">
              <span className="stat-icon">{stat.icon}</span>
              <h3>{stat.value}</h3>
              <p>{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Common Patterns Summary */}
      <section className="patterns-section">
        <div className="section-header">
          <h2>Common Accident Patterns</h2>
          <p>Overview of the most frequent incident types across all monitored sites</p>
        </div>

        <div className="patterns-grid">
          {commonPatterns.map((pattern, index) => (
            <div key={index} className="pattern-card">
              <div className="pattern-header">
                <h3>{pattern.type}</h3>
                <span className={`trend-badge ${pattern.trend}`}>
                  {pattern.trend === 'up' && '↑'}
                  {pattern.trend === 'down' && '↓'}
                  {pattern.trend === 'stable' && '→'}
                </span>
              </div>
              <div className="pattern-stats">
                <div className="stat-item">
                  <span className="stat-label">Occurrence Rate</span>
                  <span className="stat-value">{pattern.percentage}%</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Incidents (Last Year)</span>
                  <span className="stat-value">{pattern.incidents}</span>
                </div>
              </div>
              <div className="pattern-bar">
                <div className="pattern-fill" style={{ width: `${pattern.percentage}%` }}></div>
              </div>
            </div>
          ))}
        </div>

        <div className="view-more">
          <a href="/analysis" className="view-more-link">
            View Detailed Analysis →
          </a>
        </div>
      </section>

      {/* Quick Insights */}
      <section className="insights-section">
        <div className="insights-grid">
          <div className="insight-card critical">
            <h4>Critical Alert</h4>
            <p>Zone A-3 requires immediate attention due to elevated methane levels</p>
            <span className="insight-time">2 hours ago</span>
          </div>
          <div className="insight-card warning">
            <h4>Weather Warning</h4>
            <p>Heavy rainfall predicted for next 48 hours. Review drainage systems</p>
            <span className="insight-time">5 hours ago</span>
          </div>
          <div className="insight-card success">
            <h4>Safety Milestone</h4>
            <p>Site B-7 completed 100 days without any safety incidents</p>
            <span className="insight-time">1 day ago</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
