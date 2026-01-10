"""
Models Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.experiment import Experiment

models_bp = Blueprint('models', __name__)


@models_bp.route('', methods=['GET'])
@jwt_required()
def list_models():
    """List all trained models for current user"""
    user_id = int(get_jwt_identity())
    
    # Get completed experiments (trained models)
    experiments = Experiment.query.filter_by(
        user_id=user_id,
        status='completed'
    ).order_by(Experiment.completed_at.desc()).all()
    
    return jsonify({
        'models': [e.to_dict() for e in experiments],
        'total': len(experiments)
    }), 200


@models_bp.route('/<int:model_id>', methods=['GET'])
@jwt_required()
def get_model(model_id):
    """Get model details"""
    user_id = int(get_jwt_identity())
    
    experiment = Experiment.query.filter_by(id=model_id, user_id=user_id).first()
    if not experiment:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify({'model': experiment.to_dict()}), 200


@models_bp.route('/<int:model_id>/download', methods=['GET'])
@jwt_required()
def download_model(model_id):
    """Download model package as ZIP file"""
    from flask import Response
    from app.services.minio_service import get_minio_service
    
    user_id = int(get_jwt_identity())
    
    experiment = Experiment.query.filter_by(id=model_id, user_id=user_id).first()
    if not experiment:
        return jsonify({'error': 'Model not found'}), 404
    
    if experiment.status != 'completed':
        return jsonify({'error': 'Model training not completed'}), 400
    
    # Get model package path from results
    results = experiment.results or {}
    model_package_path = results.get('model_package_path')
    
    print(f"📥 Download request for model {model_id}", flush=True)
    print(f"   Results: {results}", flush=True)
    print(f"   Package path: {model_package_path}", flush=True)
    
    if not model_package_path:
        print(f"   ❌ No model_package_path in results", flush=True)
        return jsonify({'error': 'Model package not available. Please train a new model.'}), 404
    
    try:
        # Download from MinIO
        minio_service = get_minio_service()
        print(f"   📦 Downloading from MinIO: {model_package_path}", flush=True)
        zip_content = minio_service.download_bytes('models', model_package_path)
        
        if not zip_content:
            print(f"   ❌ download_bytes returned None", flush=True)
            return jsonify({'error': 'Failed to download model package'}), 500
        
        # Return as downloadable file
        filename = f"{experiment.name.replace(' ', '_')}_model.zip"
        
        return Response(
            zip_content,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(zip_content))
            }
        )
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@models_bp.route('/<int:model_id>/schema', methods=['GET'])
@jwt_required()
def get_model_schema(model_id):
    """Get model UI schema for prediction form generation"""
    user_id = int(get_jwt_identity())
    
    experiment = Experiment.query.filter_by(id=model_id, user_id=user_id).first()
    if not experiment:
        return jsonify({'error': 'Model not found'}), 404
    
    # TODO: Load UI schema from model package
    
    return jsonify({
        'model_id': model_id,
        'model_name': experiment.name,
        'target_column': experiment.target_column,
        'ui_schema': {
            'fields': []  # TODO: Load from saved schema
        }
    }), 200


@models_bp.route('/<int:model_id>', methods=['DELETE'])
@jwt_required()
def delete_model(model_id):
    """Delete a model"""
    user_id = int(get_jwt_identity())
    
    experiment = Experiment.query.filter_by(id=model_id, user_id=user_id).first()
    if not experiment:
        return jsonify({'error': 'Model not found'}), 404
    
    # TODO: Delete model files from MinIO
    
    db.session.delete(experiment)
    db.session.commit()
    
    return jsonify({'message': 'Model deleted successfully'}), 200
