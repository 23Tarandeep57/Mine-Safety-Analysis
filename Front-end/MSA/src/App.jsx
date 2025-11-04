import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import AlertsPage from './pages/AlertsPage';
import WarningsPage from './pages/WarningsPage';
import AnalysisPage from './pages/AnalysisPage';
import PreventivePage from './pages/PreventivePage';
import Chatbot from './components/chatbot/Chatbot';

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/warnings" element={<WarningsPage />} />
        <Route path="/analysis" element={<AnalysisPage />} />
        <Route path="/preventive" element={<PreventivePage />} />
      </Routes>
      <Chatbot />
    </Router>
  );
}

export default App;