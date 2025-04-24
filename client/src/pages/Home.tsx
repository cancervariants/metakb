import { Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";

const HomePage = () => {
  return (
    <>
      <Header />

      {/* Page content */}
      <main className="min-h-screen bg-white px-4 py-12 md:px-8 lg:px-16">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
            Welcome to MetaKB
          </h1>
          <p className="text-lg text-gray-700 mb-10">
            A knowledgebase to support precision oncology. Search, explore, and contribute data-driven insights.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link to="/search" className="rounded-2xl bg-blue-600 px-6 py-3 text-white font-semibold hover:bg-blue-700 transition">
              Search Knowledgebase
            </Link>
            <Link to="/about" className="rounded-2xl border border-blue-600 px-6 py-3 text-blue-600 font-semibold hover:bg-blue-50 transition">
              Learn More
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
};

export default HomePage;
