import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Products from './pages/Products';
import ProductDetails from './pages/ProductDetails';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Confirmation from './pages/Confirmation';

export default function App() {
  const [cartItems, setCartItems] = useState([
    // Pre-seed empty or test cart if needed
  ]);

  const addToCart = (product, size) => {
    setCartItems(prev => [...prev, { ...product, selectedSize: size }]);
  };

  const removeFromCart = (index) => {
    setCartItems(prev => prev.filter((_, idx) => idx !== index));
  };

  const clearCart = () => {
    setCartItems([]);
  };

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
        <Navbar cartCount={cartItems.length} />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<Products />} />
            <Route path="/product/:id" element={<ProductDetails addToCart={addToCart} />} />
            <Route path="/cart" element={<Cart cartItems={cartItems} removeFromCart={removeFromCart} />} />
            <Route path="/checkout" element={<Checkout cartItems={cartItems} clearCart={clearCart} />} />
            <Route path="/confirmation" element={<Confirmation />} />
          </Routes>
        </main>
        <footer className="bg-white border-t border-gray-200 py-6 text-center text-xs text-gray-500">
          Demo Target Application for Autonomous UI/UX & Accessibility Testing Agent
        </footer>
      </div>
    </Router>
  );
}
