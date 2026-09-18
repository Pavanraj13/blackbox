import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { PRODUCTS } from '../data/products';
import { Filter, Search, ArrowRight } from 'lucide-react';

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryParam = searchParams.get('q') || searchParams.get('query') || '';
  const [searchTerm, setSearchTerm] = useState(queryParam);
  const [maxPrice, setMaxPrice] = useState(200);

  useEffect(() => {
    if (queryParam) {
      setSearchTerm(queryParam);
    }
  }, [queryParam]);

  const filteredProducts = PRODUCTS.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          product.color.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          product.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPrice = product.price <= maxPrice;
    return matchesSearch && matchesPrice;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">All Running Shoes</h1>
        <p className="text-gray-600">Select your model and find your perfect size.</p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-3 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search shoes by color or model..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            aria-label="Filter products by search term"
          />
        </div>

        <div className="flex items-center gap-4 w-full md:w-auto">
          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
            <Filter size={16} /> Max Price: ${maxPrice}
          </label>
          <input
            type="range"
            min="50"
            max="200"
            value={maxPrice}
            onChange={(e) => setMaxPrice(Number(e.target.value))}
            className="w-36"
            aria-label="Filter by maximum price"
          />
        </div>
      </div>

      {/* Product List Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProducts.map(product => (
          <div key={product.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col justify-between hover:shadow-md transition">
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-48 object-cover"
            />
            <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex justify-between items-start">
                  <h3 className="font-bold text-lg text-gray-900">{product.name}</h3>
                  <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded capitalize">
                    {product.color}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{product.description}</p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                <span className="text-xl font-extrabold text-gray-900">${product.price.toFixed(2)}</span>
                <Link
                  to={`/product/${product.id}`}
                  className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition inline-flex items-center gap-1"
                >
                  View Details <ArrowRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Intentional UX Flaw: Distant button requiring scrolling */}
      <div className="pt-24 pb-12 text-center border-t border-gray-200 mt-16">
        <p className="text-sm text-gray-500 mb-2">Looking for seasonal clearance?</p>
        <button
          onClick={() => alert('No additional discounts available right now!')}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-6 py-3 rounded-lg font-medium text-sm"
        >
          Load Additional Clearance Shoes Below
        </button>
      </div>
    </div>
  );
}
