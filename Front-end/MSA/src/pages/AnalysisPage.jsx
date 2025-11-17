import { useState, useEffect } from 'react';
import { getIncidents } from '../utils/chatApi';
import './AnalysisPage.css';

const AnalysisPage = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [patterns, setPatterns] = useState([]);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        setLoading(true);
        const data = await getIncidents();
        setIncidents(data);
        
        // Process incidents to generate patterns
        const processedPatterns = processIncidentPatterns(data);
        setPatterns(processedPatterns);
      } catch (err) {
        setError('Failed to fetch incidents. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchIncidents();
  }, []);

  const processIncidentPatterns = (data) => {
    if (!data || data.length === 0) return [];

    const now = new Date();
    const currentYear = now.getFullYear();
    const lastYear = currentYear - 1;

    // Separate this year and last year incidents
    const thisYearIncidents = [];
    const lastYearIncidents = [];

    data.forEach(incident => {
      const incidentDate = new Date(incident.accident_date || incident.date_reported);
      const incidentYear = incidentDate.getFullYear();
      
      if (incidentYear === currentYear) {
        thisYearIncidents.push(incident);
      } else if (incidentYear === lastYear) {
        lastYearIncidents.push(incident);
      }
    });

    // Group by category for both years
    const thisYearCategoryCount = {};
    const lastYearCategoryCount = {};
    const categoryDetails = {};

    const processIncident = (incident, countMap) => {
      let category = 
        incident.incident_details?.cause_category || 
        incident.cause_category || 
        incident.category;
      
      if (!category || category === 'Other' || category === 'Uncategorized') {
        const briefCause = incident.incident_details?.brief_cause || '';
        const summary = incident.summary || '';
        const rawTitle = incident.raw_title || incident._raw_title || '';
        const rawText = incident.raw_text || incident._raw_text || '';
        
        category = categorizeFromText(briefCause, summary, rawTitle, rawText);
      }
      
      countMap[category] = (countMap[category] || 0) + 1;
      return category;
    };

    thisYearIncidents.forEach(incident => {
      const category = processIncident(incident, thisYearCategoryCount);
      if (!categoryDetails[category]) {
        categoryDetails[category] = [];
      }
      categoryDetails[category].push(incident);
    });

    lastYearIncidents.forEach(incident => {
      processIncident(incident, lastYearCategoryCount);
    });

    // Calculate trends
    const total = thisYearIncidents.length;
    return Object.entries(thisYearCategoryCount)
      .map(([category, count]) => {
        const lastYearCount = lastYearCategoryCount[category] || 0;
        let trend = 'stable';
        let yearOverYear = '0%';

        if (lastYearCount === 0) {
          // New category with no previous year incidents
          trend = 'increasing';
          yearOverYear = '+100%';
        } else {
          const change = ((count - lastYearCount) / lastYearCount) * 100;
          const changeRounded = Math.round(change);
          
          if (changeRounded > 5) {
            trend = 'increasing';
            yearOverYear = `+${changeRounded}%`;
          } else if (changeRounded < -5) {
            trend = 'decreasing';
            yearOverYear = `${changeRounded}%`;
          } else {
            trend = 'stable';
            yearOverYear = `${changeRounded >= 0 ? '+' : ''}${changeRounded}%`;
          }
        }

        return {
          category,
          total: count,
          percentage: Math.round((count / total) * 100),
          trend,
          yearOverYear,
          incidents: categoryDetails[category] || []
        };
      })
      .sort((a, b) => b.total - a.total)
      .slice(0, 6);
  };  const categorizeFromText = (...texts) => {
    // Combine all text sources
    const combinedText = texts.filter(t => t).join(' ').toLowerCase();
    
    if (!combinedText || combinedText.length < 5) return 'Uncategorized';
    
    // More comprehensive pattern matching based on DGMS categories
    if (combinedText.match(/\b(fall.*roof|roof.*fall|side.*fall|fall.*side|collapse|cave|strata)\b/i)) {
      return 'Fall of Roof/Sides';
    }
    if (combinedText.match(/\b(transport|vehicle|haulag|truck|dumper|tipper|collision|run.*over|loading|unloading)\b/i)) {
      return 'Transportation/Haulage';
    }
    if (combinedText.match(/\b(electric|electrocution|shock|power|current|wire|cable|contact.*live)\b/i)) {
      return 'Electrical Accidents';
    }
    if (combinedText.match(/\b(machinery|equipment|mechanical|machine|drill|excavator|conveyor|belt|pulley|rope|winch)\b/i)) {
      return 'Machinery Accidents';
    }
    if (combinedText.match(/\b(explosion|blast|fire|burn|ignition|flame)\b/i)) {
      return 'Explosion/Fire';
    }
    if (combinedText.match(/\b(gas|methane|carbon|suffocation|asphyxia|inundation|water|flood|pump)\b/i)) {
      return 'Gas/Inundation';
    }
    if (combinedText.match(/\b(slip|trip|fell|fall.*height|fall.*from|fallen)\b/i)) {
      return 'Slip/Trip/Fall';
    }
    if (combinedText.match(/\b(hit|struck|crush|caught|pinned|trap|between|falling.*object)\b/i)) {
      return 'Hit by Object/Caught';
    }
    if (combinedText.match(/\b(shaft|winding|cage|skip|hoisting)\b/i)) {
      return 'Shaft/Winding';
    }
    if (combinedText.match(/\b(drill|boring|blast.*hole|charging)\b/i)) {
      return 'Drilling/Blasting';
    }
    
    // If we have some text but no match, categorize by mineral type or location
    if (combinedText.match(/\b(coal)\b/i)) {
      return 'Coal Mining Operations';
    }
    if (combinedText.match(/\b(iron|ore|metal|mineral)\b/i)) {
      return 'Ore Mining Operations';
    }
    
    return 'Other';
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

  if (loading) {
    return (
      <div className="analysis-page">
        <div className="page-header">
          <h1>Accident Pattern Analysis</h1>
          <p>Loading incident data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-page">
        <div className="page-header">
          <h1>Accident Pattern Analysis</h1>
          <p className="error-message">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-page">
      <div className="page-header">
        <h1>Accident Pattern Analysis</h1>
        <p>Comprehensive breakdown of incident patterns from database - Total Incidents: {incidents.length}</p>
      </div>

      {/* Pattern Cards */}
      <div className="patterns-container">
        {patterns.length > 0 ? (
          patterns.map((pattern, index) => (
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
                      <span className="metric-label">Of Total</span>
                    </div>
                    <div className={`metric ${getTrendClass(pattern.trend)}`}>
                      <span className="metric-value">
                        {getTrendIcon(pattern.trend)} {pattern.yearOverYear}
                      </span>
                      <span className="metric-label">YoY Change</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent incidents in this category */}
              <div className="recent-incidents">
                <h4>Recent Incidents:</h4>
                {pattern.incidents.slice(0, 3).map((incident, idx) => (
                  <div key={idx} className="incident-item">
                    <span className="incident-date">
                      {new Date(incident.accident_date || incident.date_reported || incident.date).toLocaleDateString()}
                    </span>
                    <span className="incident-location">
                      {incident.mine_details?.name || 
                       incident.mine_details?.district || 
                       incident.mine_details?.state ||
                       incident.mine ||
                       incident.location || 
                       'Unknown Location'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="no-data">
            <p>No incident patterns available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPage;
