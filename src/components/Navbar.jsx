import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="backdrop-blur-sm fixed top-0 left-0 right-0 z-50 px-8 py-6">
      <div className="max-w-7xl mx-auto flex justify-center items-center">
        {/* Logo/Brand */}
        <Link to="/" className="text-white text-4xl font-light hover:text-green-400 transition-colors">
          My AI Projects
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center space-x-8">
          {/* Add more nav items here later */}
        </div>
      </div>
    </nav>
  );
}

export default Navbar; 