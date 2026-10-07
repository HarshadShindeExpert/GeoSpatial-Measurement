export type ProcessingStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
export type MeasurementStatus = 'CALCULATED' | 'NOT_APPLICABLE' | 'INVALID_GEOMETRY' | 'UNSUPPORTED';

export interface FileItem {
  id: string;
  filename: string;
  file_type: string;
  feature_count: number;
  crs: string;
  projected_crs?: string;
  status: ProcessingStatus;
  created_at: string;
}

export interface AreaMeasurement {
  sq_meters: number;
  hectares: number;
  sq_km: number;
}

export interface LengthMeasurement {
  meters: number;
  kilometers: number;
}

export interface GeodesicMeasurement {
  geodesic_area_sq_m?: number;
  geodesic_length_m?: number;
}

export interface FeatureMeasurement {
  feature_index: number;
  feature_id?: string;
  geometry_type: string;
  crs: string;
  measurement_status: MeasurementStatus;
  area?: AreaMeasurement;
  length?: LengthMeasurement;
  geodesic?: GeodesicMeasurement;
  properties: Record<string, any>;
  notes?: string;
}

export interface MeasurementSummary {
  total_features: number;
  polygon_count: number;
  linestring_count: number;
  point_count: number;
  other_count: number;
  total_area_sq_m: number;
  total_area_hectares: number;
  total_area_sq_km: number;
  total_length_m: number;
  total_length_km: number;
}

export interface FileMeasurementsResponse {
  file_id: string;
  filename: string;
  crs: string;
  projected_crs: string;
  summary: MeasurementSummary;
  features: FeatureMeasurement[];
}

export interface GeoJSONFeatureCollection {
  type: string;
  features: Array<{
    type: string;
    geometry: any;
    properties: Record<string, any>;
  }>;
}
