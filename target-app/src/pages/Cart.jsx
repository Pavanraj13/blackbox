import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, ArrowRight, ShoppingBag } from 'lucide-react';

export default function Cart({ cartItems, removeFromCart }) {
  const navigate = useNavigate();
  const subtotal = cartItems.reduce((acc, item) => acc + item.price * (item.quantity || 1), 0);
  const shipping = subtotal > 0 ? 5.99 : 0;
  const total = subtotal + shipping;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Your Shopping Cart</h1>

      {cartItems.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-gray-200 space-y-4">
          <ShoppingBag className="w-16 h-16 text-gray-300 mx-auto" />
          <h2 className="text-xl font-bold text-gray-700">Your cart is empty</h2>
          <p className="text-gray-500">Discover blue running shoes and add them to your order.</p>
          <Link
            to="/products"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-bold text-sm"
          >
            Browse Products
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items List */}
          <div className="lg:col-span-2 space-y-4">
            {cartItems.map((item, idx) => (
              <div
                key={`${item.id}-${idx}`}
                className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center gap-4"
              >
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-20 h-20 object-cover rounded-lg bg-gray-100"
                />
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900">{item.name}</h3>
                  <p className="text-xs text-gray-500">Size: US {item.selectedSize || '10'}</p>
                  <p className="text-sm font-semibold text-blue-600 mt-1">${item.price.toFixed(2)}</p>
                </div>
                <button
                  onClick={() => removeFromCart(idx)}
                  className="text-gray-400 hover:text-red-600 p-2"
                  aria-label={`Remove ${item.name} from cart`}
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>

          {/* Cart Summary */}
          <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6 h-fit">
            <h2 className="text-xl font-bold text-gray-900 border-b border-gray-100 pb-3">Order Summary</h2>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span className="font-semibold text-gray-900">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Standard Shipping</span>
                <span className="font-semibold text-gray-900">${shipping.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-base font-extrabold text-gray-900 border-t border-gray-100 pt-3">
                <span>Total</span>
                <span className="text-blue-600">${total.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={() => navigate('/checkout')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3.5 rounded-xl font-bold text-sm shadow-md transition flex items-center justify-center gap-2"
            >
              Proceed to Guest Checkout <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
