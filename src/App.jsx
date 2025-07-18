import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import SuperhumanFriend from './components/SuperhumanFriend';
import RagAI from './components/RagAI';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-black">
        <Navbar />
        {/* Add padding-top to account for fixed navbar */}
        <div className="pt-20">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<SuperhumanFriend />} />
            <Route path="/rag" element={<RagAI />} />
            {/* Add more routes as services are implemented */}
            <Route path="*" element={<HomePage />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
