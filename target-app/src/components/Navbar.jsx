import React from 'react';
import { Link } from 'react-router-dom';
import { ShoppingBag, Search, Tag } from 'lucide-react';

export default function Navbar({ cartCount }) {
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-blue-600">
          <span className="bg-blue-600 text-white px-2 py-1 rounded">SS</span>
          SwiftStride
        </Link>

        <div className="flex items-center space-x-6">
          <Link to="/" className="text-gray-700 hover:text-blue-600 font-medium text-sm">
            Home
          </Link>
          <Link to="/products" className="text-gray-700 hover:text-blue-600 font-medium text-sm">
            Products
          </Link>
          {/* Intentional Redundant Navigation Path */}
          <Link to="/products?category=deals" className="text-gray-500 hover:text-blue-600 text-sm flex items-center gap-1">
            <Tag size={14} />
            Special Deals
          </Link>
          
          {/* INTENTIONAL ACCESSIBILITY DEFECT: Icon-only button without aria-label or accessible text label */}
          <Link to="/cart" className="relative p-2 text-gray-700 hover:text-blue-600">
            <ShoppingBag className="w-6 h-6" />
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                {cartCount}
              </span>
            )}
          </Link>
        </div>
      </div>
    </nav>
  );
}
