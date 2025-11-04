import './AnalysisPage.css';

const AnalysisPage = () => {
  const patterns = [
    {
      category: 'Equipment Failure',
      total: 287,
      percentage: 23,
      trend: 'increasing',
      yearOverYear: '+12%',
      subcategories: [
        { name: 'Hydraulic Systems', count: 98, percent: 34 },
        { name: 'Electrical Components', count: 76, percent: 26 },
        { name: 'Mechanical Parts', count: 65, percent: 23 },
        { name: 'Control Systems', count: 48, percent: 17 }
      ]
    },
    {
      category: 'Ventilation Issues',
      total: 224,
      percentage: 18,
      trend: 'decreasing',
      yearOverYear: '-8%',
      subcategories: [
        { name: 'Insufficient Airflow', count: 89, percent: 40 },
        { name: 'Filter Blockage', count: 67, percent: 30 },
        { name: 'Fan Malfunction', count: 45, percent: 20 },
        { name: 'Duct Leakage', count: 23, percent: 10 }
      ]
    },
    {
      category: 'Human Error',
      total: 187,
      percentage: 15,
      trend: 'stable',
      yearOverYear: '+2%',
      subcategories: [
        { name: 'Procedural Violations', count: 75, percent: 40 },
        { name: 'Communication Failure', count: 56, percent: 30 },
        { name: 'Inadequate Training', count: 37, percent: 20 },
        { name: 'Fatigue-Related', count: 19, percent: 10 }
      ]
    },
    {
      category: 'Structural Issues',
      total: 149,
      percentage: 12,
      trend: 'decreasing',
      yearOverYear: '-15%',
      subcategories: [
        { name: 'Support Failure', count: 60, percent: 40 },
        { name: 'Ground Subsidence', count: 45, percent: 30 },
        { name: 'Rock Falls', count: 30, percent: 20 },
        { name: 'Wall Collapse', count: 14, percent: 10 }
      ]
    }
  ];

  const comparison = {
    quarters: ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
    equipment: [72, 68, 75, 72],
    ventilation: [65, 58, 52, 49],
    human: [48, 45, 47, 47],
    structural: [42, 38, 35, 34]
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      default: return '➡️';
    }
  };

  const getTrendClass = (trend) => {
    switch (trend) {
      case 'increasing': return 'trend-up';
      case 'decreasing': return 'trend-down';
      default: return 'trend-stable';
    }
  };

  return (
    <div className="analysis-page">
      <div className="page-header">
        <h1>Accident Pattern Analysis</h1>
        <p>Comprehensive breakdown of incident patterns and comparative insights</p>
      </div>

      {/* Pattern Cards */}
      <div className="patterns-container">
        {patterns.map((pattern, index) => (
          <div key={index} className="pattern-detail-card">
            <div className="pattern-main">
              <div className="pattern-overview">
                <h2>{pattern.category}</h2>
                <div className="pattern-metrics">
                  <div className="metric">
                    <span className="metric-value">{pattern.total}</span>
                    <span className="metric-label">Total Incidents</span>
                  </div>
                  <div className="metric">
                    <span className="metric-value">{pattern.percentage}%</span>
                    <span className="metric-label">Of All Incidents</span>
                  </div>
                  <div className={`metric trend ${getTrendClass(pattern.trend)}`}>
                    <span className="metric-value">
                      {getTrendIcon(pattern.trend)} {pattern.yearOverYear}
                    </span>
                    <span className="metric-label">YoY Change</span>
                  </div>
                </div>
              </div>

              <div className="subcategories">
                <h4>Breakdown by Type</h4>
                {pattern.subcategories.map((sub, idx) => (
                  <div key={idx} className="subcategory-item">
                    <div className="subcategory-info">
                      <span className="subcategory-name">{sub.name}</span>
                      <span className="subcategory-count">{sub.count} incidents</span>
                    </div>
                    <div className="subcategory-bar">
                      <div 
                        className="subcategory-fill" 
                        style={{ width: `${sub.percent}%` }}
                      ></div>
                    </div>
                    <span className="subcategory-percent">{sub.percent}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quarterly Comparison */}
      <div className="comparison-section">
        <h2>Quarterly Trend Comparison</h2>
        <p className="section-subtitle">Incident frequency across different categories over time</p>
        
        <div className="comparison-chart">
          <div className="chart-legend">
            <div className="legend-item">
              <span className="legend-dot equipment"></span>
              <span>Equipment Failure</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot ventilation"></span>
              <span>Ventilation Issues</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot human"></span>
              <span>Human Error</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot structural"></span>
              <span>Structural Issues</span>
            </div>
          </div>

          <div className="chart-bars">
            {comparison.quarters.map((quarter, index) => (
              <div key={index} className="quarter-group">
                <div className="bars-stack">
                  <div 
                    className="bar equipment" 
                    style={{ height: `${(comparison.equipment[index] / 80) * 100}%` }}
                    title={`Equipment: ${comparison.equipment[index]}`}
                  >
                    <span className="bar-value">{comparison.equipment[index]}</span>
                  </div>
                  <div 
                    className="bar ventilation" 
                    style={{ height: `${(comparison.ventilation[index] / 80) * 100}%` }}
                    title={`Ventilation: ${comparison.ventilation[index]}`}
                  >
                    <span className="bar-value">{comparison.ventilation[index]}</span>
                  </div>
                  <div 
                    className="bar human" 
                    style={{ height: `${(comparison.human[index] / 80) * 100}%` }}
                    title={`Human: ${comparison.human[index]}`}
                  >
                    <span className="bar-value">{comparison.human[index]}</span>
                  </div>
                  <div 
                    className="bar structural" 
                    style={{ height: `${(comparison.structural[index] / 80) * 100}%` }}
                    title={`Structural: ${comparison.structural[index]}`}
                  >
                    <span className="bar-value">{comparison.structural[index]}</span>
                  </div>
                </div>
                <span className="quarter-label">{quarter}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Key Insights */}
      <div className="insights-section">
        <h2>Key Insights</h2>
        <div className="insights-grid">
          <div className="insight-box">
            <h4>Primary Concern</h4>
            <p>Equipment failure remains the leading cause, requiring enhanced preventive maintenance protocols.</p>
          </div>
          <div className="insight-box">
            <h4>Positive Trend</h4>
            <p>Structural issues decreased by 15% following implementation of advanced monitoring systems.</p>
          </div>
          <div className="insight-box">
            <h4>Action Required</h4>
            <p>Human error incidents remain stable, indicating need for improved training and safety culture.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage;
