import './PreventivePage.css';

const PreventivePage = () => {
  const regions = [
    {
      id: 1,
      name: 'Zone A-3',
      riskLevel: 'high',
      primaryConcern: 'Gas Accumulation',
      measures: [
        {
          title: 'Methane Gas Monitoring',
          priority: 'Critical',
          description: 'Install additional gas sensors at 15-meter intervals throughout all shafts and working areas.',
          frequency: 'Continuous monitoring with hourly manual verification',
          status: 'In Progress'
        },
        {
          title: 'Ventilation Enhancement',
          priority: 'High',
          description: 'Upgrade ventilation fans to increase airflow capacity by 40% and reduce gas concentration.',
          frequency: 'Quarterly maintenance and daily operational checks',
          status: 'Planned'
        },
        {
          title: 'Gas Detection Training',
          priority: 'High',
          description: 'Mandatory training for all personnel on portable gas detector usage and emergency protocols.',
          frequency: 'Monthly refresher sessions',
          status: 'Ongoing'
        }
      ]
    },
    {
      id: 2,
      name: 'Zone B-1',
      riskLevel: 'medium',
      primaryConcern: 'Equipment Aging',
      measures: [
        {
          title: 'Hydraulic System Inspection',
          priority: 'High',
          description: 'Comprehensive inspection of all hydraulic lines, seals, and pumps for wear and pressure integrity.',
          frequency: 'Weekly inspection with monthly detailed maintenance',
          status: 'Active'
        },
        {
          title: 'Electrical System Audit',
          priority: 'Medium',
          description: 'Thermal imaging and load testing of all electrical panels and distribution systems.',
          frequency: 'Bi-monthly comprehensive audit',
          status: 'Active'
        },
        {
          title: 'Equipment Replacement Program',
          priority: 'Medium',
          description: 'Systematic replacement of equipment exceeding operational lifespan or showing degradation.',
          frequency: 'Quarterly review and replacement cycle',
          status: 'In Progress'
        }
      ]
    },
    {
      id: 3,
      name: 'Zone C-2',
      riskLevel: 'medium',
      primaryConcern: 'Structural Stability',
      measures: [
        {
          title: 'Ground Penetrating Radar Survey',
          priority: 'High',
          description: 'Regular GPR surveys to detect subsurface voids, fractures, and areas of ground instability.',
          frequency: 'Monthly comprehensive survey',
          status: 'Active'
        },
        {
          title: 'Support Beam Reinforcement',
          priority: 'Critical',
          description: 'Installation of additional steel support beams in areas showing increased stress indicators.',
          frequency: 'As needed based on monitoring data',
          status: 'In Progress'
        },
        {
          title: 'Seismic Monitoring',
          priority: 'Medium',
          description: 'Deploy seismographs to detect ground movement and vibrations from nearby blasting operations.',
          frequency: 'Continuous monitoring with weekly data analysis',
          status: 'Active'
        }
      ]
    },
    {
      id: 4,
      name: 'Zone D-5',
      riskLevel: 'low',
      primaryConcern: 'Weather Exposure',
      measures: [
        {
          title: 'Drainage System Maintenance',
          priority: 'Medium',
          description: 'Regular clearing and inspection of drainage channels to prevent water accumulation and flooding.',
          frequency: 'Weekly inspection, monthly comprehensive cleaning',
          status: 'Active'
        },
        {
          title: 'Lightning Protection Verification',
          priority: 'Low',
          description: 'Testing and maintenance of lightning protection systems on all tall structures and equipment.',
          frequency: 'Quarterly testing before monsoon season',
          status: 'Planned'
        },
        {
          title: 'Erosion Control Measures',
          priority: 'Medium',
          description: 'Implementation of geotextiles and vegetation to prevent slope erosion from rainfall.',
          frequency: 'Bi-annual inspection and repair',
          status: 'Active'
        }
      ]
    }
  ];

  const getRiskClass = (risk) => {
    switch (risk) {
      case 'high': return 'risk-high';
      case 'medium': return 'risk-medium';
      default: return 'risk-low';
    }
  };

  const getPriorityClass = (priority) => {
    switch (priority) {
      case 'Critical': return 'priority-critical';
      case 'High': return 'priority-high';
      case 'Medium': return 'priority-medium';
      default: return 'priority-low';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'Active': return 'status-active';
      case 'In Progress': return 'status-progress';
      case 'Planned': return 'status-planned';
      default: return 'status-ongoing';
    }
  };

  return (
    <div className="preventive-page">
      <div className="page-header">
        <h1>Preventive Measures</h1>
        <p>Region-specific safety recommendations and maintenance protocols</p>
      </div>

      <div className="summary-cards">
        <div className="summary-item">
          <span className="summary-number">4</span>
          <span className="summary-text">Active Zones</span>
        </div>
        <div className="summary-item">
          <span className="summary-number">12</span>
          <span className="summary-text">Measures Implemented</span>
        </div>
        <div className="summary-item">
          <span className="summary-number">85%</span>
          <span className="summary-text">Compliance Rate</span>
        </div>
      </div>

      <div className="regions-container">
        {regions.map((region) => (
          <div key={region.id} className="region-section">
            <div className="region-header">
              <div className="region-info">
                <h2>{region.name}</h2>
                <span className={`risk-badge ${getRiskClass(region.riskLevel)}`}>
                  {region.riskLevel.toUpperCase()} RISK
                </span>
              </div>
              <div className="primary-concern">
                <span className="concern-label">Primary Concern:</span>
                <span className="concern-value">{region.primaryConcern}</span>
              </div>
            </div>

            <div className="measures-grid">
              {region.measures.map((measure, index) => (
                <div key={index} className="measure-card">
                  <div className="measure-header">
                    <h3>{measure.title}</h3>
                    <span className={`priority-badge ${getPriorityClass(measure.priority)}`}>
                      {measure.priority}
                    </span>
                  </div>

                  <p className="measure-description">{measure.description}</p>

                  <div className="measure-details">
                    <div className="detail-item">
                      <span className="detail-label">Frequency</span>
                      <span className="detail-value">{measure.frequency}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Status</span>
                      <span className={`status-badge ${getStatusClass(measure.status)}`}>
                        {measure.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* General Best Practices */}
      <div className="best-practices">
        <h2>General Safety Best Practices</h2>
        <div className="practices-grid">
          <div className="practice-card">
            <div className="practice-icon">📋</div>
            <h4>Daily Safety Briefings</h4>
            <p>Conduct pre-shift safety meetings to review potential hazards and emergency procedures.</p>
          </div>
          <div className="practice-card">
            <div className="practice-icon">👷</div>
            <h4>PPE Compliance</h4>
            <p>Ensure 100% personal protective equipment usage with regular inspections and replacements.</p>
          </div>
          <div className="practice-card">
            <div className="practice-icon">🔧</div>
            <h4>Preventive Maintenance</h4>
            <p>Implement predictive maintenance programs to identify equipment issues before failure.</p>
          </div>
          <div className="practice-card">
            <div className="practice-icon">📱</div>
            <h4>Incident Reporting</h4>
            <p>Maintain anonymous reporting system for near-misses and safety concerns.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreventivePage;
