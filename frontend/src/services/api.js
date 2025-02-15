import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'  // or your backend URL
});

export const processAddress = async (address) => {
  try {
    // Send as JSON data
    const response = await api.post('/process-address', { address });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};