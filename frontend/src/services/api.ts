import axios from 'axios';
import { FileItem, FileMeasurementsResponse, GeoJSONFeatureCollection } from '../types';

const API_BASE = '/api';

export const api = {
  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_BASE}/files/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async listFiles(): Promise<FileItem[]> {
    const response = await axios.get(`${API_BASE}/files/`);
    return response.data;
  },

  async getFileInfo(id: string): Promise<FileItem> {
    const response = await axios.get(`${API_BASE}/files/${id}/`);
    return response.data;
  },

  async getMeasurements(id: string): Promise<FileMeasurementsResponse> {
    const response = await axios.get(`${API_BASE}/files/${id}/measurements/`);
    return response.data;
  },

  async getGeoJSON(id: string): Promise<GeoJSONFeatureCollection> {
    const response = await axios.get(`${API_BASE}/files/${id}/geojson/`);
    return response.data;
  },

  async deleteFile(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/files/${id}/`);
  },
};
