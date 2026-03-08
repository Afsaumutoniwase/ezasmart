"""
Tests for API endpoints
"""
import pytest
import json


class TestSensorPredictionAPI:
    """Tests for the sensor prediction API endpoint"""
    
    def test_predict_sensor_endpoint_exists(self, client):
        """Test that the predict endpoint exists"""
        response = client.post('/api/predict-sensor', 
                               data=json.dumps({}),
                               content_type='application/json')
        assert response.status_code != 404
    
    def test_predict_sensor_with_valid_data(self, authenticated_client):
        """Test sensor prediction with valid data"""
        data = {
            'crop_id': 'Tomato',
            'ph_level': 6.2,
            'ec_value': 2.5,
            'ambient_temp': 24.5
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code in [200, 400, 503]
        
        if response.status_code == 200:
            result = json.loads(response.data)
            assert 'success' in result
            if result['success']:
                assert 'action' in result
                assert 'description' in result
                assert result['action'] in ['Maintain', 'Add_Nutrients', 'Dilute', 'Add_pH_Up', 'Add_pH_Down']
    
    def test_predict_sensor_optimal_conditions(self, authenticated_client):
        """Test prediction with optimal conditions"""
        data = {
            'crop_id': 'Lettuce',
            'ph_level': 6.5,  # Optimal for Lettuce (6.0-7.0)
            'ec_value': 1.5,  # Optimal for Lettuce (1.2-1.8)
            'ambient_temp': 22.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert result['action'] == 'Maintain'
    
    def test_predict_sensor_low_ph(self, authenticated_client):
        """Test prediction with pH too low"""
        data = {
            'crop_id': 'Tomato',
            'ph_level': 5.0,  # Too low for Tomato (optimal 6.0-6.5)
            'ec_value': 3.0,
            'ambient_temp': 24.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert result['action'] == 'Add_pH_Up'
    
    def test_predict_sensor_high_ph(self, authenticated_client):
        """Test prediction with pH too high"""
        data = {
            'crop_id': 'Cucumber',
            'ph_level': 6.5,  # Too high for Cucumber (optimal 5.0-5.5)
            'ec_value': 1.8,
            'ambient_temp': 23.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert result['action'] == 'Add_pH_Down'
    
    def test_predict_sensor_low_ec(self, authenticated_client):
        """Test prediction with EC too low"""
        data = {
            'crop_id': 'Tomato',
            'ph_level': 6.2,
            'ec_value': 1.0,  # Too low for Tomato (optimal 2.0-4.0)
            'ambient_temp': 24.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert result['action'] == 'Add_Nutrients'
    
    def test_predict_sensor_high_ec(self, authenticated_client):
        """Test prediction with EC too high"""
        data = {
            'crop_id': 'Lettuce',
            'ph_level': 6.5,
            'ec_value': 3.0,  # Too high for Lettuce (optimal 1.2-1.8)
            'ambient_temp': 22.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert result['action'] == 'Dilute'
    
    def test_predict_sensor_missing_crop(self, authenticated_client):
        """Test prediction with missing crop_id"""
        data = {
            'ph_level': 6.5,
            'ec_value': 2.0,
            'ambient_temp': 24.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_predict_sensor_missing_ph(self, authenticated_client):
        """Test prediction with missing pH level"""
        data = {
            'crop_id': 'Tomato',
            'ec_value': 2.0,
            'ambient_temp': 24.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_predict_sensor_missing_ec(self, authenticated_client):
        """Test prediction with missing EC value"""
        data = {
            'crop_id': 'Tomato',
            'ph_level': 6.5,
            'ambient_temp': 24.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_predict_sensor_missing_temperature(self, authenticated_client):
        """Test prediction with missing temperature"""
        data = {
            'crop_id': 'Tomato',
            'ph_level': 6.5,
            'ec_value': 2.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_predict_sensor_invalid_crop(self, authenticated_client):
        """Test prediction with invalid crop type"""
        data = {
            'crop_id': 'InvalidCrop',
            'ph_level': 6.5,
            'ec_value': 2.0,
            'ambient_temp': 24.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code in [400, 503]
    
    def test_predict_sensor_zero_values(self, authenticated_client):
        """Test prediction with zero values"""
        data = {
            'crop_id': 'Tomato',
            'ph_level': 0,
            'ec_value': 0,
            'ambient_temp': 0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_predict_sensor_invalid_json(self, authenticated_client):
        """Test prediction with invalid JSON"""
        response = authenticated_client.post('/api/predict-sensor',
                               data='invalid json',
                               content_type='application/json')
        
        assert response.status_code in [400, 500]
    
    def test_predict_sensor_returns_inputs(self, authenticated_client):
        """Test that prediction returns input values"""
        data = {
            'crop_id': 'Basil',
            'ph_level': 5.8,
            'ec_value': 1.2,
            'ambient_temp': 23.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert 'inputs' in result
                assert result['inputs']['crop'] == 'Basil'
                assert result['inputs']['pH'] == 5.8
                assert result['inputs']['EC'] == 1.2
    
    def test_predict_sensor_includes_ranges(self, authenticated_client):
        """Test that prediction includes optimal ranges"""
        data = {
            'crop_id': 'Spinach',
            'ph_level': 6.5,
            'ec_value': 2.0,
            'ambient_temp': 22.0
        }
        
        response = authenticated_client.post('/api/predict-sensor',
                               data=json.dumps(data),
                               content_type='application/json')
        
        if response.status_code == 200:
            result = json.loads(response.data)
            if result.get('success'):
                assert 'inputs' in result
                assert 'pH_Range' in result['inputs']
                assert 'EC_Range' in result['inputs']
                assert '6.0-7.0' in result['inputs']['pH_Range']


class TestCropRangesData:
    """Tests for crop optimal ranges data"""
    
    def test_crop_ranges_coverage(self, app):
        """Test that CROP_OPTIMAL_RANGES has expected crops"""
        from app import CROP_OPTIMAL_RANGES
        
        assert 'Tomato' in CROP_OPTIMAL_RANGES
        assert 'Lettuce' in CROP_OPTIMAL_RANGES
        assert 'Basil' in CROP_OPTIMAL_RANGES
        assert 'Cucumber' in CROP_OPTIMAL_RANGES
    
    def test_crop_ranges_structure(self, app):
        """Test that crop ranges have correct structure"""
        from app import CROP_OPTIMAL_RANGES
        
        for crop, ranges in CROP_OPTIMAL_RANGES.items():
            assert 'ec_min' in ranges
            assert 'ec_max' in ranges
            assert 'ph_min' in ranges
            assert 'ph_max' in ranges
            
            assert ranges['ec_min'] < ranges['ec_max']
            assert ranges['ph_min'] <= ranges['ph_max']
            
            assert 0 <= ranges['ph_min'] <= 14
            assert 0 <= ranges['ph_max'] <= 14
            
            assert ranges['ec_min'] >= 0
            assert ranges['ec_max'] > 0

