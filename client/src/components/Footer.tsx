import { Link } from "react-router-dom";

const Footer = () => {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        {/* Logo / Site Title */}
        <Link to="/" className="text-2xl font-bold text-blue-700 hover:text-blue-900">
          MetaKB
        </Link>

        {/* Navigation */}
        <nav className="space-x-4">
          <Link
            to="/search"
            className="text-gray-700 hover:text-blue-600 font-medium transition"
          >
            Search
          </Link>
          <Link
            to="/about"
            className="text-gray-700 hover:text-blue-600 font-medium transition"
          >
            About
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Footer;
