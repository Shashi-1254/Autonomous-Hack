"""
Inventory AI Agents
AI-powered agents for inventory management, analysis, and predictions
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class InventoryAgentService:
    """
    AI Agent service for inventory management
    Uses Gemini AI for intelligent analysis and recommendations
    """
    
    def __init__(self):
        self.gemini_service = None
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini AI service"""
        try:
            from app.services.gemini_service import get_gemini_service
            self.gemini_service = get_gemini_service()
        except Exception as e:
            print(f"⚠️ Gemini service not available: {e}")
            self.gemini_service = None
    
    # ========================================
    # AGENT 1: Stock Analysis Agent
    # ========================================
    
    def analyze_stock(self, inventory_items: List[Dict]) -> Dict[str, Any]:
        """
        Analyze current stock levels and identify issues
        
        Returns:
            - Low stock items
            - Out of stock items
            - Overstocked items
            - Stock health score
        """
        low_stock = []
        out_of_stock = []
        overstocked = []
        healthy = []
        
        for item in inventory_items:
            qty = item.get('quantity', 0)
            min_level = item.get('min_stock_level', 10)
            max_level = item.get('max_stock_level', 100)
            
            if qty == 0:
                out_of_stock.append(item)
            elif qty <= min_level:
                low_stock.append(item)
            elif qty > max_level * 1.2:  # 20% over max
                overstocked.append(item)
            else:
                healthy.append(item)
        
        total_items = len(inventory_items)
        health_score = (len(healthy) / total_items * 100) if total_items > 0 else 0
        
        analysis = {
            'total_items': total_items,
            'health_score': round(health_score, 1),
            'out_of_stock': {
                'count': len(out_of_stock),
                'items': out_of_stock
            },
            'low_stock': {
                'count': len(low_stock),
                'items': low_stock
            },
            'overstocked': {
                'count': len(overstocked),
                'items': overstocked
            },
            'healthy': {
                'count': len(healthy)
            }
        }
        
        # Generate AI insights if available
        if self.gemini_service and (low_stock or out_of_stock):
            analysis['ai_insights'] = self._generate_stock_insights(analysis)
        
        return analysis
    
    def _generate_stock_insights(self, analysis: Dict) -> str:
        """Generate AI insights for stock analysis"""
        if not self.gemini_service:
            return "AI insights unavailable"
        
        prompt = f"""
        Analyze this inventory status and provide actionable insights:
        
        - Total Items: {analysis['total_items']}
        - Health Score: {analysis['health_score']}%
        - Out of Stock: {analysis['out_of_stock']['count']} items
        - Low Stock: {analysis['low_stock']['count']} items
        - Overstocked: {analysis['overstocked']['count']} items
        
        Low stock items: {json.dumps([i['name'] for i in analysis['low_stock']['items'][:5]])}
        Out of stock items: {json.dumps([i['name'] for i in analysis['out_of_stock']['items'][:5]])}
        
        Provide:
        1. Priority actions needed
        2. Risk assessment
        3. Recommendations
        
        Keep response concise (max 200 words).
        """
        
        try:
            response = self.gemini_service.generate_text(prompt)
            return response
        except Exception as e:
            return f"Could not generate insights: {str(e)}"
    
    # ========================================
    # AGENT 2: Expiry Prediction Agent
    # ========================================
    
    def analyze_expiry(self, inventory_items: List[Dict]) -> Dict[str, Any]:
        """
        Analyze expiry dates and generate selling tips
        
        Returns:
            - Expired items
            - Expiring soon (7 days)
            - Expiring this month
            - Selling tips for each
        """
        now = datetime.utcnow()
        
        expired = []
        expiring_soon = []  # Within 7 days
        expiring_month = []  # Within 30 days
        
        for item in inventory_items:
            expiry_str = item.get('expiry_date')
            if not expiry_str:
                continue
            
            try:
                if isinstance(expiry_str, str):
                    expiry = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                else:
                    expiry = expiry_str
                
                days_left = (expiry - now).days
                
                item_with_expiry = {**item, 'days_until_expiry': days_left}
                
                if days_left < 0:
                    expired.append(item_with_expiry)
                elif days_left <= 7:
                    expiring_soon.append(item_with_expiry)
                elif days_left <= 30:
                    expiring_month.append(item_with_expiry)
            except:
                continue
        
        # Sort by urgency
        expired.sort(key=lambda x: x['days_until_expiry'])
        expiring_soon.sort(key=lambda x: x['days_until_expiry'])
        expiring_month.sort(key=lambda x: x['days_until_expiry'])
        
        result = {
            'expired': {
                'count': len(expired),
                'items': expired,
                'action': 'REMOVE FROM SHELF IMMEDIATELY'
            },
            'expiring_soon': {
                'count': len(expiring_soon),
                'items': expiring_soon,
                'action': 'URGENT - Apply discount or bundle'
            },
            'expiring_month': {
                'count': len(expiring_month),
                'items': expiring_month,
                'action': 'Monitor and plan promotions'
            }
        }
        
        # Generate selling tips
        if self.gemini_service and (expiring_soon or expiring_month):
            result['selling_tips'] = self._generate_selling_tips(expiring_soon + expiring_month)
        
        return result
    
    def _generate_selling_tips(self, expiring_items: List[Dict]) -> List[Dict]:
        """Generate AI-powered selling tips for expiring items"""
        if not self.gemini_service or not expiring_items:
            return []
        
        items_summary = []
        for item in expiring_items[:10]:  # Top 10 most urgent
            items_summary.append({
                'name': item['name'],
                'category': item.get('category', 'General'),
                'quantity': item['quantity'],
                'days_left': item['days_until_expiry'],
                'selling_price': item.get('selling_price', 0)
            })
        
        prompt = f"""
        Generate creative selling tips for these expiring products:
        
        {json.dumps(items_summary, indent=2)}
        
        For each item, suggest:
        1. Recommended discount percentage
        2. Bundle ideas (what to pair with)
        3. Marketing message
        
        Return as JSON array with format:
        [
            {{
                "item_name": "...",
                "discount_percent": 20,
                "bundle_suggestion": "...",
                "marketing_message": "..."
            }}
        ]
        """
        
        try:
            response = self.gemini_service.generate_text(prompt)
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return [{'raw_tips': response}]
        except Exception as e:
            return [{'error': str(e)}]
    
    # ========================================
    # AGENT 3: Order Generation Agent
    # ========================================
    
    def generate_order_suggestions(self, inventory_items: List[Dict], vendors: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate purchase order suggestions based on stock analysis
        
        Returns:
            - Suggested order items
            - Recommended quantities
            - Priority levels
            - Estimated costs
        """
        order_items = []
        
        for item in inventory_items:
            qty = item.get('quantity', 0)
            min_level = item.get('min_stock_level', 10)
            max_level = item.get('max_stock_level', 100)
            
            if qty <= min_level:
                # Calculate order quantity to reach optimal level (80% of max)
                optimal_qty = int(max_level * 0.8)
                order_qty = optimal_qty - qty
                
                if order_qty > 0:
                    urgency = 'critical' if qty == 0 else 'high' if qty < min_level * 0.5 else 'normal'
                    
                    order_items.append({
                        'item_id': item['id'],
                        'item_name': item['name'],
                        'category': item.get('category', 'General'),
                        'current_quantity': qty,
                        'order_quantity': order_qty,
                        'unit': item.get('unit', 'units'),
                        'estimated_cost': order_qty * item.get('cost_price', 0),
                        'urgency': urgency
                    })
        
        # Sort by urgency
        urgency_order = {'critical': 0, 'high': 1, 'normal': 2}
        order_items.sort(key=lambda x: urgency_order.get(x['urgency'], 3))
        
        total_cost = sum(item['estimated_cost'] for item in order_items)
        
        result = {
            'suggested_items': order_items,
            'total_items': len(order_items),
            'estimated_total_cost': total_cost,
            'critical_count': len([i for i in order_items if i['urgency'] == 'critical']),
            'high_priority_count': len([i for i in order_items if i['urgency'] == 'high'])
        }
        
        # Generate AI reasoning
        if self.gemini_service and order_items:
            result['ai_reasoning'] = self._generate_order_reasoning(result)
        
        return result
    
    def _generate_order_reasoning(self, order_data: Dict) -> str:
        """Generate AI explanation for order suggestions"""
        if not self.gemini_service:
            return ""
        
        prompt = f"""
        Explain why this purchase order is recommended:
        
        - Total items to order: {order_data['total_items']}
        - Critical items: {order_data['critical_count']}
        - High priority items: {order_data['high_priority_count']}
        - Estimated cost: ${order_data['estimated_total_cost']:.2f}
        
        Top items: {json.dumps([i['item_name'] for i in order_data['suggested_items'][:5]])}
        
        Provide a brief business justification (max 100 words).
        """
        
        try:
            return self.gemini_service.generate_text(prompt)
        except:
            return "Order generated based on stock levels below minimum thresholds."
    
    # ========================================
    # AGENT 4: Vendor Quotation Agent
    # ========================================
    
    def evaluate_quotations(self, quotations: List[Dict], order_items: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate vendor quotations and recommend best option
        
        Returns:
            - Ranked quotations
            - AI recommendation
            - Comparison analysis
        """
        if not quotations:
            return {'error': 'No quotations to evaluate'}
        
        scored_quotations = []
        
        for quote in quotations:
            # Calculate score based on multiple factors
            price_score = 100 - min(quote.get('total_price', 0) / 1000, 100)  # Lower is better
            delivery_score = 100 - min(quote.get('delivery_days', 7) * 10, 100)  # Faster is better
            vendor_rating = quote.get('vendor', {}).get('rating', 3) * 20  # Max 100
            
            # Weighted average
            total_score = (price_score * 0.4) + (delivery_score * 0.3) + (vendor_rating * 0.3)
            
            scored_quotations.append({
                **quote,
                'ai_score': round(total_score, 1),
                'price_rank': 0,
                'delivery_rank': 0
            })
        
        # Rank quotations
        scored_quotations.sort(key=lambda x: x['ai_score'], reverse=True)
        
        for i, q in enumerate(scored_quotations):
            q['overall_rank'] = i + 1
        
        # Sort by price for price rank
        by_price = sorted(scored_quotations, key=lambda x: x.get('total_price', 0))
        for i, q in enumerate(by_price):
            q['price_rank'] = i + 1
        
        # Sort by delivery for delivery rank
        by_delivery = sorted(scored_quotations, key=lambda x: x.get('delivery_days', 999))
        for i, q in enumerate(by_delivery):
            q['delivery_rank'] = i + 1
        
        # Re-sort by overall score
        scored_quotations.sort(key=lambda x: x['ai_score'], reverse=True)
        
        result = {
            'ranked_quotations': scored_quotations,
            'recommended': scored_quotations[0] if scored_quotations else None,
            'total_quotations': len(scored_quotations)
        }
        
        # Generate AI recommendation
        if self.gemini_service and len(scored_quotations) > 1:
            result['ai_recommendation'] = self._generate_quotation_recommendation(scored_quotations)
        
        return result
    
    def _generate_quotation_recommendation(self, quotations: List[Dict]) -> str:
        """Generate AI recommendation for quotation selection"""
        if not self.gemini_service:
            return ""
        
        summary = []
        for q in quotations[:3]:
            summary.append({
                'vendor': q.get('vendor', {}).get('name', 'Unknown'),
                'price': q.get('total_price', 0),
                'delivery_days': q.get('delivery_days', 0),
                'score': q.get('ai_score', 0)
            })
        
        prompt = f"""
        Compare these vendor quotations and recommend the best choice:
        
        {json.dumps(summary, indent=2)}
        
        Consider price, delivery time, and overall value.
        Provide a clear recommendation with reasoning (max 100 words).
        """
        
        try:
            return self.gemini_service.generate_text(prompt)
        except:
            return "Recommended based on best combination of price, delivery, and vendor rating."
    
    # ========================================
    # AGENT 5: Local Trends Agent
    # ========================================
    
    def analyze_local_trends(self, location: str, date_range: int = 30) -> Dict[str, Any]:
        """
        Analyze local events and trends for demand forecasting
        
        Args:
            location: Store location/area
            date_range: Days to look ahead
            
        Returns:
            - Upcoming events
            - Demand predictions
            - Recommended inventory adjustments
        """
        # Simulated local events (in production, would use Google Places API, etc.)
        simulated_events = self._get_simulated_events(location, date_range)
        
        result = {
            'location': location,
            'date_range_days': date_range,
            'events': simulated_events,
            'total_events': len(simulated_events)
        }
        
        # Generate demand forecast
        if self.gemini_service and simulated_events:
            result['demand_forecast'] = self._generate_demand_forecast(location, simulated_events)
        
        return result
    
    def _get_simulated_events(self, location: str, days: int) -> List[Dict]:
        """Get simulated local events (replace with real API in production)"""
        now = datetime.utcnow()
        
        # Simulated events based on common patterns
        events = [
            {
                'name': 'Weekend Rush',
                'type': 'recurring',
                'start_date': (now + timedelta(days=(5 - now.weekday()) % 7)).isoformat(),
                'end_date': (now + timedelta(days=(6 - now.weekday()) % 7 + 1)).isoformat(),
                'impact': 'high',
                'affected_categories': ['Groceries', 'Beverages', 'Snacks'],
                'expected_demand_change': 30
            },
            {
                'name': 'Month End',
                'type': 'recurring',
                'start_date': (now.replace(day=28) if now.day < 28 else now).isoformat(),
                'end_date': (now.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat(),
                'impact': 'medium',
                'affected_categories': ['Essentials', 'Groceries'],
                'expected_demand_change': 15
            },
            {
                'name': 'Local Festival Season',
                'type': 'special',
                'start_date': (now + timedelta(days=10)).isoformat(),
                'end_date': (now + timedelta(days=15)).isoformat(),
                'impact': 'very_high',
                'affected_categories': ['Sweets', 'Gifts', 'Decorations', 'Beverages'],
                'expected_demand_change': 50
            }
        ]
        
        return events
    
    def _generate_demand_forecast(self, location: str, events: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered demand forecast"""
        if not self.gemini_service:
            return {}
        
        prompt = f"""
        Based on these upcoming events near {location}, predict demand changes:
        
        Events:
        {json.dumps(events, indent=2)}
        
        Provide:
        1. Overall demand outlook (increase/decrease percentage)
        2. Top 5 categories to stock up
        3. Specific recommendations
        
        Return as JSON:
        {{
            "overall_change_percent": 20,
            "outlook": "positive",
            "top_categories": ["cat1", "cat2"],
            "recommendations": ["rec1", "rec2"]
        }}
        """
        
        try:
            response = self.gemini_service.generate_text(prompt)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'raw_forecast': response}
        except Exception as e:
            return {'error': str(e)}


# Singleton instance
_agent_service = None

def get_inventory_agent_service() -> InventoryAgentService:
    """Get or create the inventory agent service instance"""
    global _agent_service
    if _agent_service is None:
        _agent_service = InventoryAgentService()
    return _agent_service
