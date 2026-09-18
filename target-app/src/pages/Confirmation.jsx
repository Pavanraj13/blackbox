import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ShoppingBag, ArrowRight } from 'lucide-react';

export default function Confirmation() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-6">
      <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
        <CheckCircle2 size={48} />
      </div>

      <div className="space-y-2">
        <span className="text-xs font-bold uppercase tracking-widest text-green-700 bg-green-50 px-3 py-1 rounded-full border border-green-200">
          Order Verified
        </span>
        <h1 className="text-3xl font-extrabold text-gray-900">Order Confirmed!</h1>
        <p className="text-gray-600">
          Thank you for shopping with SwiftStride! Your guest order has been placed successfully.
        </p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm text-left max-w-md mx-auto space-y-3">
        <div className="flex justify-between border-b border-gray-100 pb-2 text-sm">
          <span className="text-gray-500">Order Number</span>
          <span className="font-mono font-bold text-gray-900">#ORD-98421-BLUE</span>
        </div>
        <div className="flex justify-between border-b border-gray-100 pb-2 text-sm">
          <span className="text-gray-500">Checkout Type</span>
          <span className="font-semibold text-blue-600">Guest Checkout</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Estimated Delivery</span>
          <span className="font-semibold text-gray-900">2-3 Business Days</span>
        </div>
      </div>

      <div className="pt-4">
        <Link
          to="/"
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-xl font-bold text-sm shadow-md transition"
        >
          Return to Home <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
