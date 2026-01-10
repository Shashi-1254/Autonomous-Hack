"""
Order Model
Represents inventory orders generated from ML predictions
"""
from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class Order(db.Model):
    """
    Represents an inventory order generated from ML predictions.
    Orders go through a workflow: pending -> approved/rejected -> fulfilled
    """
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiments.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Order status: pending, approved, rejected, fulfilled
    status = db.Column(db.String(50), default='pending')
    
    # Order items as JSON array
    # Each item: { product, quantity, unit_price, reasoning }
    items = db.Column(JSON, default=list)
    
    # AI-generated summary and recommendations
    summary = db.Column(db.Text)
    risk_factors = db.Column(JSON, default=list)
    recommendations = db.Column(JSON, default=list)
    
    # Prediction context
    prediction_horizon = db.Column(db.String(100))  # e.g., "next 7 days"
    predictions_data = db.Column(JSON)  # Store the predictions used
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Approval workflow
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Fulfillment
    fulfilled_at = db.Column(db.DateTime, nullable=True)
    fulfillment_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    experiment = db.relationship('Experiment', backref='orders')
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'user_id': self.user_id,
            'status': self.status,
            'items': self.items or [],
            'summary': self.summary,
            'risk_factors': self.risk_factors or [],
            'recommendations': self.recommendations or [],
            'prediction_horizon': self.prediction_horizon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'fulfilled_at': self.fulfilled_at.isoformat() if self.fulfilled_at else None,
            'fulfillment_notes': self.fulfillment_notes,
            'total_items': len(self.items) if self.items else 0,
            'total_quantity': sum(item.get('quantity_to_order', 0) for item in (self.items or []))
        }
    
    def approve(self, user_id: int):
        """Approve the order"""
        self.status = 'approved'
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
    
    def reject(self, user_id: int, reason: str):
        """Reject the order"""
        self.status = 'rejected'
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def fulfill(self, notes: str = None):
        """Mark order as fulfilled"""
        self.status = 'fulfilled'
        self.fulfilled_at = datetime.utcnow()
        self.fulfillment_notes = notes
