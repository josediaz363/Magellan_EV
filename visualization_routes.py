from flask import Blueprint, jsonify
from services.visualization.donut_service import DonutService
from services.visualization.histogram_service import HistogramService
from services.visualization.scurve_service import SCurveService
from services.visualization.quantity_service import QuantityService
from services.visualization.spi_service import SPIService

# Initialize services
donut_service = DonutService()
histogram_service = HistogramService()
scurve_service = SCurveService()
quantity_service = QuantityService()
spi_service = SPIService()

# Create a blueprint for visualization API endpoints
visualization_bp = Blueprint('visualization', __name__, url_prefix='/api/visualizations')

@visualization_bp.route('/donut/<int:project_id>')
def get_donut_data(project_id):
    """API endpoint to get donut chart data for a project"""
    try:
        data = donut_service.get_data(project_id)
        return jsonify(data)
    except Exception as e:
        print(f"Error getting donut chart data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@visualization_bp.route('/histogram/<int:project_id>')
def get_histogram_data(project_id):
    """API endpoint to get progress histogram data for a project"""
    try:
        data = histogram_service.get_data(project_id)
        return jsonify(data)
    except Exception as e:
        print(f"Error getting histogram data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@visualization_bp.route('/scurve/<int:project_id>')
def get_scurve_data(project_id):
    """API endpoint to get S-curve data for a project"""
    try:
        data = scurve_service.get_data(project_id)
        return jsonify(data)
    except Exception as e:
        print(f"Error getting S-curve data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@visualization_bp.route('/quantity/<int:project_id>')
def get_quantity_data(project_id):
    """API endpoint to get quantity distribution data for a project"""
    try:
        data = quantity_service.get_data(project_id)
        return jsonify(data)
    except Exception as e:
        print(f"Error getting quantity distribution data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@visualization_bp.route('/spi/<int:project_id>')
def get_spi_data(project_id):
    """API endpoint to get Schedule Performance Index data for a project"""
    try:
        data = spi_service.get_data(project_id)
        return jsonify(data)
    except Exception as e:
        print(f"Error getting SPI data: {str(e)}")
        return jsonify({"error": str(e)}), 500
