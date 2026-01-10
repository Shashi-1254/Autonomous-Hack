"""
Order Routes
API endpoints for managing inventory orders
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.order import Order
from app.services.order_service import get_order_service

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('', methods=['GET'])
@jwt_required()
def list_orders():
    """
    List all orders for the current user.
    Query params:
        - status: Filter by status (pending, approved, rejected, fulfilled)
    """
    user_id = int(get_jwt_identity())
    status = request.args.get('status')
    
    query = Order.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return jsonify({
        'orders': [order.to_dict() for order in orders],
        'total': len(orders)
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get a specific order by ID"""
    user_id = int(get_jwt_identity())
    
    order_service = get_order_service()
    order = order_service.get_order_by_id(order_id, user_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({'order': order.to_dict()}), 200


@orders_bp.route('', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create a new order from predictions.
    Body:
        - experiment_id: ID of the experiment with predictions
        - predictions: List of prediction results
        - current_inventory: Current stock levels by product
        - prediction_horizon: Time period (e.g., "next 7 days")
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    experiment_id = data.get('experiment_id')
    predictions = data.get('predictions', [])
    current_inventory = data.get('current_inventory', {})
    prediction_horizon = data.get('prediction_horizon', 'next 7 days')
    
    if not experiment_id:
        return jsonify({'error': 'Experiment ID is required'}), 400
    
    if not predictions:
        return jsonify({'error': 'Predictions are required'}), 400
    
    try:
        order_service = get_order_service()
        order = order_service.generate_order_from_predictions(
            experiment_id=experiment_id,
            user_id=user_id,
            predictions=predictions,
            current_inventory=current_inventory,
            prediction_horizon=prediction_horizon
        )
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create order: {str(e)}'}), 500


@orders_bp.route('/<int:order_id>/items', methods=['PUT'])
@jwt_required()
def update_order_items(order_id):
    """
    Update order items (human modification before approval).
    Body:
        - items: Updated list of order items
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Items are required'}), 400
    
    order_service = get_order_service()
    order = order_service.update_order_items(order_id, user_id, data['items'])
    
    if not order:
        return jsonify({'error': 'Order not found or cannot be modified'}), 404
    
    return jsonify({
        'message': 'Order items updated',
        'order': order.to_dict()
    }), 200


@orders_bp.route('/<int:order_id>/approve', methods=['POST'])
@jwt_required()
def approve_order(order_id):
    """Approve an order, triggering fulfillment"""
    user_id = int(get_jwt_identity())
    
    order_service = get_order_service()
    order = order_service.approve_order(order_id, user_id)
    
    if not order:
        return jsonify({'error': 'Order not found or already processed'}), 404
    
    return jsonify({
        'message': 'Order approved successfully',
        'order': order.to_dict()
    }), 200


@orders_bp.route('/<int:order_id>/reject', methods=['POST'])
@jwt_required()
def reject_order(order_id):
    """
    Reject an order.
    Body:
        - reason: Reason for rejection
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    reason = data.get('reason', 'No reason provided') if data else 'No reason provided'
    
    order_service = get_order_service()
    order = order_service.reject_order(order_id, user_id, reason)
    
    if not order:
        return jsonify({'error': 'Order not found or already processed'}), 404
    
    return jsonify({
        'message': 'Order rejected',
        'order': order.to_dict()
    }), 200


@orders_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_orders():
    """Get all pending orders for the current user"""
    user_id = int(get_jwt_identity())
    
    order_service = get_order_service()
    orders = order_service.get_pending_orders(user_id)
    
    return jsonify({
        'orders': [order.to_dict() for order in orders],
        'total': len(orders)
    }), 200
