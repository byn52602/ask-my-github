import axios from 'axios';
import { IndexRequest, QueryRequest, QueryResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async indexRepository(data: IndexRequest): Promise<{ status: string }> {
    const response = await axios.post(`${API_BASE_URL}/index`, data);
    return response.data;
  },

  async queryRepository(data: QueryRequest): Promise<QueryResponse> {
    const response = await axios.post(`${API_BASE_URL}/query`, data);
    return response.data;
  },

  async healthCheck(): Promise<{ status: string }> {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  },
};
