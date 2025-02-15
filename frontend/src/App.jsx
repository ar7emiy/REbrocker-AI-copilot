import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/dashboard/Dashboard';
import AddressInput from './components/address/AddressInput';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/address" element={<AddressInput />} />
      </Routes>
    </Router>
  );
};

export default App;