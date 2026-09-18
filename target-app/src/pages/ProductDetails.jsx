import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { PRODUCTS } from '../data/products';
import { ShoppingBag, ArrowLeft, Check, Star } from 'lucide-react';

export default function ProductDetails({ addToCart }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [size, setSize] = useState('10');
  const [added, setAdded] = useState(false);

  const product = PRODUCTS.find(p => p.id === id) || PRODUCTS[0];

  const handleAddToCart = () => {
    addToCart(product, size);
    setAdded(true);
    setTimeout(() => {
      navigate('/cart');
    }, 600);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <Link to="/products" className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600 font-medium">
        <ArrowLeft size={16} /> Back to Products
      </Link>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden grid grid-cols-1 md:grid-cols-2 gap-8 p-6 md:p-8">
        {/* Product Image */}
        <div className="rounded-xl overflow-hidden bg-gray-100 flex items-center justify-center">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-96 object-cover"
          />
        </div>

        {/* Product Meta */}
        <div className="flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full uppercase">
              In Stock
            </span>
            <h1 className="text-3xl font-extrabold text-gray-900">{product.name}</h1>
            
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black text-gray-900">${product.price.toFixed(2)}</span>
              <div className="flex items-center text-amber-500 text-sm font-semibold">
                <Star size={16} className="fill-amber-400 text-amber-400 mr-1" />
                {product.rating} (42 reviews)
              </div>
            </div>

            <p className="text-gray-600 leading-relaxed">{product.description}</p>

            {/* Size Selector */}
            <div className="space-y-2 pt-2">
              <label className="block text-sm font-bold text-gray-700">Select Shoe Size (US)</label>
              <div className="flex gap-2">
                {['8', '9', '10', '11', '12'].map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setSize(s)}
                    className={`w-12 h-10 rounded-lg text-sm font-bold border transition ${
                      size === s
                        ? 'border-blue-600 bg-blue-50 text-blue-600'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-4 border-t border-gray-100">
            <button
              onClick={handleAddToCart}
              className={`w-full py-4 rounded-xl font-bold text-base flex items-center justify-center gap-2 shadow-md transition ${
                added
                  ? 'bg-green-600 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {added ? (
                <>
                  <Check size={20} /> Added to Cart! Redirecting...
                </>
              ) : (
                <>
                  <ShoppingBag size={20} /> Add to Cart
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
