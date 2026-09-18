import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowRight, Search, ShieldCheck, Truck, RefreshCw } from 'lucide-react';

export default function Home() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/products?q=${encodeURIComponent(searchTerm)}`);
    } else {
      navigate('/products');
    }
  };

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Banner */}
      <section className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white py-16 px-4">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
            Find Your Perfect Running Shoes
          </h1>
          <p className="text-lg text-blue-100 max-w-2xl mx-auto">
            Explore premium lightweight sneakers engineered for distance and daily comfort.
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="max-w-xl mx-auto flex items-center bg-white rounded-lg p-2 shadow-lg">
            <Search className="text-gray-400 ml-3 w-5 h-5" />
            <input
              type="text"
              placeholder="Search for blue running shoes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 text-gray-900 focus:outline-none"
              aria-label="Search products"
            />
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-md font-medium text-sm transition"
            >
              Search
            </button>
          </form>

          <div className="pt-4 flex justify-center gap-4">
            <Link
              to="/products"
              className="inline-flex items-center gap-2 bg-white text-blue-800 px-6 py-3 rounded-lg font-bold hover:bg-blue-50 transition shadow"
            >
              Shop Running Shoes <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Categories */}
      <section className="max-w-7xl mx-auto px-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Popular Categories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <Link
            to="/products?query=blue"
            className="group relative h-48 rounded-xl overflow-hidden bg-gray-900 shadow-md flex items-end p-6"
          >
            <img
              src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=60"
              alt="Blue Shoes"
              className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:scale-105 transition duration-300"
            />
            <div className="relative z-10 text-white">
              <h3 className="text-xl font-bold">Blue Shoes under $100</h3>
              <p className="text-sm text-gray-200">Lightweight & Fast</p>
            </div>
          </Link>

          <Link
            to="/products?category=running"
            className="group relative h-48 rounded-xl overflow-hidden bg-gray-900 shadow-md flex items-end p-6"
          >
            <img
              src="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500&auto=format&fit=crop&q=60"
              alt="Marathon Shoes"
              className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:scale-105 transition duration-300"
            />
            <div className="relative z-10 text-white">
              <h3 className="text-xl font-bold">Pro Marathon Series</h3>
              <p className="text-sm text-gray-200">Carbon Plate Tech</p>
            </div>
          </Link>

          <Link
            to="/products?category=trail"
            className="group relative h-48 rounded-xl overflow-hidden bg-gray-900 shadow-md flex items-end p-6"
          >
            <img
              src="https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=500&auto=format&fit=crop&q=60"
              alt="Trail Shoes"
              className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:scale-105 transition duration-300"
            />
            <div className="relative z-10 text-white">
              <h3 className="text-xl font-bold">Trail & Hiking</h3>
              <p className="text-sm text-gray-200">All-Terrain Durable</p>
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}
