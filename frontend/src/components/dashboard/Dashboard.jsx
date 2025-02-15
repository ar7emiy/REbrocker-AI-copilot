import React from 'react';
import { useNavigate } from 'react-router-dom';

const Button = ({ onClick, children, variant = 'primary' }) => {
  const baseStyles = "px-6 py-3 rounded-md font-medium transition-colors duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-opacity-50 min-h-[44px]";
  
  const variants = {
    primary: "bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white focus:ring-blue-500",
    secondary: "bg-green-500 hover:bg-green-600 active:bg-green-700 text-white focus:ring-green-500"
  };

  return (
    <button 
      onClick={onClick}
      className={`${baseStyles} ${variants[variant]}`}
    >
      {children}
    </button>
  );
};

const Dashboard = () => {
  const navigate = useNavigate();
  const SHEET_ID = "1NnDWfGSaRck9IfVUNMAXItP1feJChq1zEp43sD1YnyM";

  const handleEnterAddress = () => {
    navigate('/address');
  };

  const handleViewProperties = () => {
    window.open(`https://docs.google.com/spreadsheets/d/${SHEET_ID}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            coBroker.ai
          </h1>
          <p className="text-gray-600">
            Enter a new address or view your properties
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button 
            onClick={handleEnterAddress}
            variant="primary"
          >
            Enter Address
          </Button>

          <Button 
            onClick={handleViewProperties}
            variant="secondary"
          >
            View Properties
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;