import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { processAddress } from '../../services/api';

const AddressInput = () => {
  const navigate = useNavigate();
  const [streetAddress, setStreetAddress] = useState('');
  const [zipcode, setZipcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [processedAddresses, setProcessedAddresses] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!streetAddress.trim() || !zipcode.trim()) {
      setStatus({ type: 'error', message: 'Please enter both street address and zipcode' });
      return;
    }

    // Combine address components
    const fullAddress = `${streetAddress}, Chicago, IL ${zipcode}`;

    setLoading(true);
    setStatus(null);

    try {
      const response = await processAddress(fullAddress);
      if (response.status === 'skipped') {
        setStatus({ 
          type: 'warning', 
          message: response.message || 'Address already exists' 
        });
      } else {
        setStatus({ 
          type: 'success', 
          message: 'Address processed successfully' 
        });
        setProcessedAddresses(prev => [...prev, fullAddress]);
      }
      setStreetAddress('');
    } catch (error) {
      setStatus({ 
        type: 'error', 
        message: error.message || 'Failed to process address' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Back button */}
        <button
          onClick={() => navigate('/')}
          className="mb-8 flex items-center text-gray-600 hover:text-gray-900"
        >
          <svg className="w-5 h-5 mr-2" fill="none" strokeLinecap="round" 
               strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" 
               stroke="currentColor">
            <path d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </button>

        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Enter Address
          </h1>
          <p className="text-gray-600">
            Enter the property details below
          </p>
        </div>

        {/* Status Message */}
        {status && (
          <div className={`mb-4 p-4 rounded-md ${
            status.type === 'success' ? 'bg-green-50 text-green-800' :
            status.type === 'error' ? 'bg-red-50 text-red-800' :
            'bg-yellow-50 text-yellow-800'
          }`}>
            {status.message}
          </div>
        )}

        {/* City, State, Zipcode Container */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                City
              </label>
              <input
                type="text"
                value="Chicago"
                disabled
                className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                State
              </label>
              <input
                type="text"
                value="IL"
                disabled
                className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Zipcode
              </label>
              <input
                type="text"
                value={zipcode}
                onChange={(e) => setZipcode(e.target.value)}
                placeholder="Enter zipcode"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm 
                         focus:border-blue-500 focus:ring-blue-500"
                maxLength="5"
                pattern="[0-9]*"
              />
            </div>
          </div>
        </div>

        {/* Street Address Form */}
        <div className="bg-white shadow rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="street-address" 
                     className="block text-sm font-medium text-gray-700">
                Street Address
              </label>
              <input
                type="text"
                id="street-address"
                value={streetAddress}
                onChange={(e) => setStreetAddress(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm 
                         focus:border-blue-500 focus:ring-blue-500"
                placeholder="Enter street address"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full flex justify-center py-2 px-4 border border-transparent 
                         rounded-md shadow-sm text-sm font-medium text-white 
                         ${loading 
                           ? 'bg-blue-400 cursor-not-allowed' 
                           : 'bg-blue-600 hover:bg-blue-700'
                         }`}
            >
              {loading ? 'Processing...' : 'Process Address'}
            </button>
          </form>
        </div>

        {/* Processed Addresses History */}
        {processedAddresses.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recently Processed Addresses</h2>
            <div className="space-y-2">
              {processedAddresses.map((addr, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-md text-gray-700">
                  {addr}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddressInput;