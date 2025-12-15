import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:3000/dev', 
});

export const fetchJobs = async () => {
  try {
    const response = await API.get('/jobs');
    return response.data;
  } catch (error) {
    console.error("API Error fetchJobs:", error);
    throw error;
  }
};

export const createCandidate = async (candidateData) => {
  try {
    const response = await API.post('/candidates', candidateData);
    return response.data;
  } catch (error) {
    console.error("API Error createCandidate:", error);
    throw error;
  }
};

export const fetchApplications = async (jobId) => {
  try {
    const response = await API.get(`/applications?job_id=${jobId}`);
    return response.data;
  } catch (error) {
    console.error("API Error fetchApplications:", error);
    throw error;
  }
};

export const createJob = async (jobData) => {
  try {
    const response = await API.post('/jobs', jobData);
    return response.data;
  } catch (error) {
    console.error("API Error createJob:", error);
    throw error;
  }
};