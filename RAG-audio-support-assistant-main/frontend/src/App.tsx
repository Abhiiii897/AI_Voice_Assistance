import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage' 
import ActiveCallPage from './pages/ActiveCallPage'; 

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/call" element={<ActiveCallPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
