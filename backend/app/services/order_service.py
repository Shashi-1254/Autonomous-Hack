"""
Order Service
Handles order generation, management, and fulfillment logic
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app import db
from app.models.order import Order


class OrderService:
    """
    Service for managing inventory orders generated from ML predictions.
    """
    
    def generate_order_from_predictions(
        self,
        experiment_id: int,
        user_id: int,
        predictions: List[Dict[str, Any]],
        current_inventory: Dict[str, float],
        prediction_horizon: str = "next 7 days"
    ) -> Order:
        """
        Generate an order based on ML predictions and current inventory.
        Uses Gemini AI to create intelligent order recommendations.
        
        Args:
            experiment_id: ID of the experiment that generated predictions
            user_id: ID of the user creating the order
            predictions: List of prediction results
            current_inventory: Current stock levels by product
            prediction_horizon: Time period for predictions
            
        Returns:
            Created Order object
        """
        try:
            from app.services.gemini_service import get_gemini_service
            gemini_service = get_gemini_service()
            
            # Generate AI-powered order report
            report = gemini_service.generate_order_report(
                predictions=predictions,
                current_inventory=current_inventory,
                prediction_horizon=prediction_horizon
            )
            
            order = Order(
                experiment_id=experiment_id,
                user_id=user_id,
                status='pending',
                items=report.get('order_items', []),
                summary=report.get('summary', ''),
                risk_factors=report.get('risk_factors', []),
                recommendations=report.get('recommendations', []),
                prediction_horizon=prediction_horizon,
                predictions_data={
                    'predictions': predictions,
                    'current_inventory': current_inventory
                }
            )
            
        except Exception as e:
            # Fallback: Create basic order without AI recommendations
            order = Order(
                experiment_id=experiment_id,
                user_id=user_id,
                status='pending',
                items=self._generate_basic_order_items(predictions, current_inventory),
                summary=f"Auto-generated order based on predictions (AI unavailable: {str(e)})",
                risk_factors=['AI analysis unavailable - manual review recommended'],
                recommendations=['Review predictions manually before approving'],
                prediction_horizon=prediction_horizon,
                predictions_data={
                    'predictions': predictions,
                    'current_inventory': current_inventory
                }
            )
        
        db.session.add(order)
        db.session.commit()
        
        return order
    
    def _generate_basic_order_items(
        self,
        predictions: List[Dict[str, Any]],
        current_inventory: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Generate basic order items without AI (fallback method).
        Simple logic: order quantity = predicted demand - current stock + safety buffer
        """
        items = []
        safety_buffer = 0.2  # 20% safety stock
        
        # Aggregate predictions by product
        product_demand = {}
        for pred in predictions:
            product = pred.get('product', pred.get('item', 'Unknown'))
            demand = pred.get('predicted_demand', pred.get('prediction', 0))
            product_demand[product] = product_demand.get(product, 0) + demand
        
        for product, total_demand in product_demand.items():
            current_stock = current_inventory.get(product, 0)
            needed = total_demand - current_stock
            
            if needed > 0:
                # Add safety buffer
                order_qty = int(needed * (1 + safety_buffer))
                items.append({
                    'product': product,
                    'quantity_to_order': order_qty,
                    'priority': 'high' if needed > current_stock else 'medium',
                    'reasoning': f"Predicted demand: {total_demand}, Current stock: {current_stock}"
                })
        
        return items
    
    def get_pending_orders(self, user_id: int) -> List[Order]:
        """Get all pending orders for a user"""
        return Order.query.filter_by(user_id=user_id, status='pending').all()
    
    def get_order_by_id(self, order_id: int, user_id: int) -> Optional[Order]:
        """Get a specific order by ID"""
        return Order.query.filter_by(id=order_id, user_id=user_id).first()
    
    def approve_order(self, order_id: int, approver_id: int) -> Optional[Order]:
        """Approve an order"""
        order = Order.query.get(order_id)
        if order and order.status == 'pending':
            order.approve(approver_id)
            db.session.commit()
            
            # Trigger fulfillment (placeholder for external API/email)
            self._trigger_fulfillment(order)
            
            return order
        return None
    
    def reject_order(self, order_id: int, rejector_id: int, reason: str) -> Optional[Order]:
        """Reject an order"""
        order = Order.query.get(order_id)
        if order and order.status == 'pending':
            order.reject(rejector_id, reason)
            db.session.commit()
            return order
        return None
    
    def update_order_items(self, order_id: int, user_id: int, items: List[Dict]) -> Optional[Order]:
        """Update order items (human modification before approval)"""
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if order and order.status == 'pending':
            order.items = items
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return order
        return None
    
    def _trigger_fulfillment(self, order: Order):
        """
        Trigger order fulfillment (placeholder for integration).
        In production, this would:
        - Send email notifications
        - Call supplier APIs
        - Create purchase orders in ERP
        - etc.
        """
        # TODO: Implement actual fulfillment logic
        print(f"📦 Order #{order.id} approved - triggering fulfillment...")
        print(f"   Items: {len(order.items)}")
        print(f"   Total quantity: {order.to_dict()['total_quantity']}")
        
        # Log the action
        order.fulfillment_notes = f"Fulfillment triggered at {datetime.utcnow().isoformat()}"
        db.session.commit()


# Singleton instance
_order_service = None


def get_order_service() -> OrderService:
    """Get or create the OrderService singleton"""
    global _order_service
    if _order_service is None:
        _order_service = OrderService()
    return _order_service
