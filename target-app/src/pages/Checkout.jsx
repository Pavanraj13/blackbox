import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, CreditCard, CheckCircle } from 'lucide-react';

export default function Checkout({ cartItems, clearCart }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: 'Alex Morgan',
    email: 'alex.morgan@example.com',
    address: '742 Evergreen Terrace',
    city: 'Springfield',
    zip: '97477',
    cardNumber: '4532 1111 2222 3333',
    expDate: '12/28',
    cvv: '888'
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    clearCart();
    navigate('/confirmation');
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Guest Checkout</h1>
        <span className="text-xs text-green-700 bg-green-50 px-3 py-1 rounded-full font-semibold flex items-center gap-1 border border-green-200">
          <Lock size={12} /> 256-Bit SSL Encrypted
        </span>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Shipping Information */}
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-gray-900 border-b border-gray-100 pb-2">1. Shipping Details</h2>

          <div>
            <label htmlFor="fullName" className="block text-xs font-bold text-gray-700 mb-1">
              Full Name
            </label>
            <input
              id="fullName"
              type="text"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              placeholder="e.g. Alex Morgan"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              required
            />
          </div>

          {/* INTENTIONAL ACCESSIBILITY DEFECT: Email input has NO <label> tag and NO aria-label */}
          <div>
            {/* Intentionally missing label element! */}
            <input
              id="email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter email address for receipt..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none mt-2"
              required
            />
          </div>

          <div>
            <label htmlFor="address" className="block text-xs font-bold text-gray-700 mb-1">
              Street Address
            </label>
            <input
              id="address"
              type="text"
              name="address"
              value={formData.address}
              onChange={handleChange}
              placeholder="123 Main St"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="city" className="block text-xs font-bold text-gray-700 mb-1">
                City
              </label>
              <input
                id="city"
                type="text"
                name="city"
                value={formData.city}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                required
              />
            </div>
            <div>
              <label htmlFor="zip" className="block text-xs font-bold text-gray-700 mb-1">
                ZIP / Postal Code
              </label>
              <input
                id="zip"
                type="text"
                name="zip"
                value={formData.zip}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                required
              />
            </div>
          </div>
        </div>

        {/* Payment & Submit */}
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-gray-900 border-b border-gray-100 pb-2">2. Payment Method</h2>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center gap-3">
              <CreditCard className="text-blue-600" />
              <div>
                <p className="text-xs font-bold text-blue-900">Demo Credit Card Selected</p>
                <p className="text-xs text-blue-700">Simulated Instant Approval</p>
              </div>
            </div>

            <div>
              <label htmlFor="cardNumber" className="block text-xs font-bold text-gray-700 mb-1">
                Card Number
              </label>
              <input
                id="cardNumber"
                type="text"
                name="cardNumber"
                value={formData.cardNumber}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="expDate" className="block text-xs font-bold text-gray-700 mb-1">
                  Expiry
                </label>
                <input
                  id="expDate"
                  type="text"
                  name="expDate"
                  value={formData.expDate}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label htmlFor="cvv" className="block text-xs font-bold text-gray-700 mb-1">
                  CVV
                </label>
                <input
                  id="cvv"
                  type="password"
                  name="cvv"
                  value={formData.cvv}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  required
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100">
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold text-base shadow-md transition flex items-center justify-center gap-2"
            >
              <CheckCircle size={20} /> Place Order & Complete Guest Checkout
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
