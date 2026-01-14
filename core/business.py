"""Business Manager for ProducerOS - Finances, invoices, and product catalog."""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from core.database import get_database


# Default product presets
DEFAULT_PRODUCTS = [
    {"title": "MP3 Lease", "type": "license", "price": 29.99, "description": "MP3 format lease license"},
    {"title": "WAV Lease", "type": "license", "price": 49.99, "description": "High quality WAV lease license"},
    {"title": "Trackout/Stems", "type": "license", "price": 99.99, "description": "Full stems/trackout package"},
    {"title": "Exclusive Rights", "type": "license", "price": 500.00, "description": "Full exclusive ownership"},
    {"title": "Mixing (2 Track)", "type": "service", "price": 50.00, "description": "Basic 2-track mixing service"},
    {"title": "Full Mix & Master", "type": "service", "price": 150.00, "description": "Complete mixing and mastering"},
    {"title": "Custom Beat Production", "type": "service", "price": 300.00, "description": "Custom beat creation"},
]

# Income categories
INCOME_CATEGORIES = [
    "Beat Sales",
    "Exclusive Sales",
    "Services",
    "Royalties",
    "Other Income"
]

# Expense categories
EXPENSE_CATEGORIES = [
    "Studio Gear",
    "Software/Plugins",
    "Subscriptions",
    "Marketing",
    "Distribution",
    "Other Expense"
]

# Invoice statuses
INVOICE_STATUSES = {
    "draft": {"label": "Draft", "color": "#666666"},
    "sent": {"label": "Sent", "color": "#3B82F6"},
    "paid": {"label": "Paid", "color": "#22C55E"},
    "overdue": {"label": "Overdue", "color": "#EF4444"},
    "cancelled": {"label": "Cancelled", "color": "#6B7280"}
}


class BusinessManager:
    """Manages finances, invoices, products, and transactions for producers."""

    def __init__(self):
        self.db = get_database()
        self._init_default_products()

    def _init_default_products(self):
        """Initialize default products if the table is empty."""
        existing = self.get_products()
        if not existing:
            for product in DEFAULT_PRODUCTS:
                self.add_product(product)

    # ==================== PRODUCTS ====================

    def add_product(self, data: Dict) -> int:
        """
        Add a new product/service.

        Args:
            data: Dict with title, type (license/service), price, description.

        Returns:
            The ID of the created product.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO products (title, type, price, description)
            VALUES (?, ?, ?, ?)
        ''', (
            data.get('title', ''),
            data.get('type', 'license'),
            data.get('price', 0.0),
            data.get('description', '')
        ))
        conn.commit()
        return cursor.lastrowid

    def get_products(self, active_only: bool = True) -> List[Dict]:
        """Get all products."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        if active_only:
            cursor.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY type, title')
        else:
            cursor.execute('SELECT * FROM products ORDER BY type, title')

        return [dict(row) for row in cursor.fetchall()]

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a product by ID."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_product(self, product_id: int, data: Dict) -> bool:
        """Update a product."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        fields = ['title', 'type', 'price', 'description', 'is_active']
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])

        if not updates:
            return False

        values.append(product_id)
        query = f'UPDATE products SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

    def delete_product(self, product_id: int) -> bool:
        """Soft delete a product (set inactive)."""
        return self.update_product(product_id, {'is_active': 0})

    # ==================== INVOICES ====================

    def _generate_invoice_number(self) -> str:
        """Generate next invoice number (INV-YYYY-NNN format)."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        year = datetime.now().year
        prefix = f"INV-{year}-"

        cursor.execute('''
            SELECT invoice_number FROM invoices
            WHERE invoice_number LIKE ?
            ORDER BY invoice_number DESC LIMIT 1
        ''', (f"{prefix}%",))

        row = cursor.fetchone()
        if row:
            try:
                last_num = int(row[0].split('-')[-1])
                return f"{prefix}{last_num + 1:03d}"
            except:
                pass

        return f"{prefix}001"

    def create_invoice(self, data: Dict) -> int:
        """
        Create a new invoice.

        Args:
            data: Dict with client_id, due_date, notes, terms, tax_rate.

        Returns:
            The ID of the created invoice.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        invoice_number = self._generate_invoice_number()
        created_date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
            INSERT INTO invoices (invoice_number, client_id, status, due_date, created_date,
                                  tax_rate, notes, terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number,
            data.get('client_id'),
            'draft',
            data.get('due_date'),
            created_date,
            data.get('tax_rate', 0.0),
            data.get('notes', ''),
            data.get('terms', '')
        ))
        conn.commit()
        return cursor.lastrowid

    def get_invoices(self, status: str = None, client_id: int = None) -> List[Dict]:
        """Get invoices with optional filters."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT i.*, c.name as client_name
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE 1=1
        '''
        params = []

        if status:
            query += ' AND i.status = ?'
            params.append(status)

        if client_id:
            query += ' AND i.client_id = ?'
            params.append(client_id)

        query += ' ORDER BY i.created_at DESC'

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice with client info."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT i.*, c.name as client_name, c.email as client_email
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.id = ?
        ''', (invoice_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def update_invoice(self, invoice_id: int, data: Dict) -> bool:
        """Update invoice details."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        fields = ['client_id', 'status', 'due_date', 'tax_rate', 'notes', 'terms']
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])

        if not updates:
            return False

        values.append(invoice_id)
        query = f'UPDATE invoices SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()

        # Recalculate totals
        self._recalculate_invoice_totals(invoice_id)
        return cursor.rowcount > 0

    def update_invoice_status(self, invoice_id: int, new_status: str) -> bool:
        """
        Update invoice status.
        If status changes to 'paid', auto-create income transaction.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get current invoice info
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return False

        old_status = invoice.get('status')

        # Update status
        if new_status == 'paid':
            cursor.execute('''
                UPDATE invoices SET status = ?, paid_at = ? WHERE id = ?
            ''', (new_status, datetime.now().isoformat(), invoice_id))
        else:
            cursor.execute('''
                UPDATE invoices SET status = ?, paid_at = NULL WHERE id = ?
            ''', (new_status, invoice_id))

        conn.commit()

        # If changing to 'paid', create income transaction
        if new_status == 'paid' and old_status != 'paid':
            self.add_transaction({
                'type': 'income',
                'amount': invoice.get('total', 0),
                'category': 'Beat Sales',
                'description': f"Invoice {invoice.get('invoice_number', '')} - {invoice.get('client_name', 'Unknown')}",
                'date': datetime.now().strftime('%Y-%m-%d'),
                'invoice_id': invoice_id
            })

        # If changing FROM 'paid', remove the auto-created transaction
        if old_status == 'paid' and new_status != 'paid':
            cursor.execute('DELETE FROM transactions WHERE invoice_id = ?', (invoice_id,))
            conn.commit()

        return True

    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice and its items."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Delete items first
        cursor.execute('DELETE FROM invoice_items WHERE invoice_id = ?', (invoice_id,))
        # Delete related transactions
        cursor.execute('DELETE FROM transactions WHERE invoice_id = ?', (invoice_id,))
        # Delete invoice
        cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ==================== INVOICE ITEMS ====================

    def add_invoice_item(self, invoice_id: int, data: Dict) -> int:
        """Add an item to an invoice."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        quantity = data.get('quantity', 1)
        unit_price = data.get('unit_price', 0.0)
        total = quantity * unit_price

        cursor.execute('''
            INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total, product_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            invoice_id,
            data.get('description', ''),
            quantity,
            unit_price,
            total,
            data.get('product_id')
        ))
        conn.commit()

        # Recalculate invoice totals
        self._recalculate_invoice_totals(invoice_id)

        return cursor.lastrowid

    def get_invoice_items(self, invoice_id: int) -> List[Dict]:
        """Get all items for an invoice."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id
        ''', (invoice_id,))
        return [dict(row) for row in cursor.fetchall()]

    def update_invoice_item(self, item_id: int, data: Dict) -> bool:
        """Update an invoice item."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get invoice_id for recalculation
        cursor.execute('SELECT invoice_id FROM invoice_items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        if not row:
            return False
        invoice_id = row[0]

        # Update item
        quantity = data.get('quantity')
        unit_price = data.get('unit_price')

        updates = []
        values = []

        if 'description' in data:
            updates.append('description = ?')
            values.append(data['description'])
        if quantity is not None:
            updates.append('quantity = ?')
            values.append(quantity)
        if unit_price is not None:
            updates.append('unit_price = ?')
            values.append(unit_price)

        # Recalculate item total if quantity or price changed
        if quantity is not None or unit_price is not None:
            cursor.execute('SELECT quantity, unit_price FROM invoice_items WHERE id = ?', (item_id,))
            current = cursor.fetchone()
            new_qty = quantity if quantity is not None else current[0]
            new_price = unit_price if unit_price is not None else current[1]
            updates.append('total = ?')
            values.append(new_qty * new_price)

        if not updates:
            return False

        values.append(item_id)
        query = f'UPDATE invoice_items SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()

        # Recalculate invoice totals
        self._recalculate_invoice_totals(invoice_id)

        return cursor.rowcount > 0

    def delete_invoice_item(self, item_id: int) -> bool:
        """Delete an invoice item."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get invoice_id for recalculation
        cursor.execute('SELECT invoice_id FROM invoice_items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        if not row:
            return False
        invoice_id = row[0]

        cursor.execute('DELETE FROM invoice_items WHERE id = ?', (item_id,))
        conn.commit()

        # Recalculate invoice totals
        self._recalculate_invoice_totals(invoice_id)

        return cursor.rowcount > 0

    def _recalculate_invoice_totals(self, invoice_id: int):
        """Recalculate invoice subtotal, tax, and total."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Get subtotal from items
        cursor.execute('''
            SELECT COALESCE(SUM(total), 0) FROM invoice_items WHERE invoice_id = ?
        ''', (invoice_id,))
        subtotal = cursor.fetchone()[0]

        # Get tax rate
        cursor.execute('SELECT tax_rate FROM invoices WHERE id = ?', (invoice_id,))
        row = cursor.fetchone()
        tax_rate = row[0] if row else 0.0

        # Calculate tax and total
        tax_amount = subtotal * (tax_rate / 100)
        total = subtotal + tax_amount

        # Update invoice
        cursor.execute('''
            UPDATE invoices SET subtotal = ?, tax_amount = ?, total = ? WHERE id = ?
        ''', (subtotal, tax_amount, total, invoice_id))
        conn.commit()

    # ==================== TRANSACTIONS ====================

    def add_transaction(self, data: Dict) -> int:
        """
        Add a new transaction (income or expense).

        Args:
            data: Dict with type, amount, category, description, date, invoice_id.

        Returns:
            The ID of the created transaction.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO transactions (type, amount, category, description, date, invoice_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('type', 'income'),
            data.get('amount', 0.0),
            data.get('category', ''),
            data.get('description', ''),
            data.get('date', datetime.now().strftime('%Y-%m-%d')),
            data.get('invoice_id')
        ))
        conn.commit()
        return cursor.lastrowid

    def get_transactions(self, type: str = None, start_date: str = None,
                         end_date: str = None, category: str = None) -> List[Dict]:
        """Get transactions with optional filters."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM transactions WHERE 1=1'
        params = []

        if type:
            query += ' AND type = ?'
            params.append(type)

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        if category:
            query += ' AND category = ?'
            params.append(category)

        query += ' ORDER BY date DESC, created_at DESC'

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_transaction(self, transaction_id: int) -> Optional[Dict]:
        """Get a transaction by ID."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_transaction(self, transaction_id: int, data: Dict) -> bool:
        """Update a transaction."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        fields = ['type', 'amount', 'category', 'description', 'date']
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])

        if not updates:
            return False

        values.append(transaction_id)
        query = f'UPDATE transactions SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ==================== BUSINESS GOALS ====================

    def set_monthly_goal(self, amount: float, month: str = None) -> int:
        """Set a monthly income goal."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        if not month:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            # Last day of month
            if now.month == 12:
                end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            end_date = end_date.strftime('%Y-%m-%d')
        else:
            # Parse month string (YYYY-MM format)
            year, mon = map(int, month.split('-'))
            start_date = f"{year}-{mon:02d}-01"
            if mon == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, mon + 1, 1) - timedelta(days=1)
            end_date = end_date.strftime('%Y-%m-%d')

        # Check if goal already exists for this period
        cursor.execute('''
            SELECT id FROM business_goals WHERE type = 'monthly' AND start_date = ?
        ''', (start_date,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE business_goals SET target_amount = ? WHERE id = ?
            ''', (amount, existing[0]))
            conn.commit()
            return existing[0]
        else:
            cursor.execute('''
                INSERT INTO business_goals (type, target_amount, start_date, end_date)
                VALUES (?, ?, ?, ?)
            ''', ('monthly', amount, start_date, end_date))
            conn.commit()
            return cursor.lastrowid

    def get_monthly_goal(self, month: str = None) -> Optional[Dict]:
        """Get monthly goal for a given month."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        if not month:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
        else:
            year, mon = map(int, month.split('-'))
            start_date = f"{year}-{mon:02d}-01"

        cursor.execute('''
            SELECT * FROM business_goals WHERE type = 'monthly' AND start_date = ?
        ''', (start_date,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== STATISTICS ====================

    def get_revenue_stats(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get revenue statistics for a period."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Default to current month
        if not start_date:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Total income
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE type = 'income' AND date BETWEEN ? AND ?
        ''', (start_date, end_date))
        total_income = cursor.fetchone()[0]

        # Total expenses
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE type = 'expense' AND date BETWEEN ? AND ?
        ''', (start_date, end_date))
        total_expenses = cursor.fetchone()[0]

        # Net profit
        net_profit = total_income - total_expenses

        # Income by category
        cursor.execute('''
            SELECT category, SUM(amount) as total FROM transactions
            WHERE type = 'income' AND date BETWEEN ? AND ?
            GROUP BY category ORDER BY total DESC
        ''', (start_date, end_date))
        income_by_category = [{'category': row[0], 'total': row[1]} for row in cursor.fetchall()]

        # Expense by category
        cursor.execute('''
            SELECT category, SUM(amount) as total FROM transactions
            WHERE type = 'expense' AND date BETWEEN ? AND ?
            GROUP BY category ORDER BY total DESC
        ''', (start_date, end_date))
        expense_by_category = [{'category': row[0], 'total': row[1]} for row in cursor.fetchall()]

        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'income_by_category': income_by_category,
            'expense_by_category': expense_by_category,
            'start_date': start_date,
            'end_date': end_date
        }

    def get_invoice_stats(self) -> Dict:
        """Get invoice statistics."""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Count by status
        for status in INVOICE_STATUSES.keys():
            cursor.execute('SELECT COUNT(*) FROM invoices WHERE status = ?', (status,))
            stats[f'{status}_count'] = cursor.fetchone()[0]

        # Total outstanding (sent invoices)
        cursor.execute('''
            SELECT COALESCE(SUM(total), 0) FROM invoices WHERE status = 'sent'
        ''')
        stats['outstanding_total'] = cursor.fetchone()[0]

        # Total paid this month
        now = datetime.now()
        month_start = now.replace(day=1).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COALESCE(SUM(total), 0) FROM invoices
            WHERE status = 'paid' AND DATE(paid_at) >= ?
        ''', (month_start,))
        stats['paid_this_month'] = cursor.fetchone()[0]

        # Overdue invoices
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM invoices
            WHERE status = 'sent' AND due_date < ?
        ''', (today,))
        stats['overdue_count'] = cursor.fetchone()[0]

        return stats

    def get_goal_progress(self, month: str = None) -> Dict:
        """Get progress towards monthly goal."""
        goal = self.get_monthly_goal(month)

        if not goal:
            return {'has_goal': False, 'target': 0, 'current': 0, 'percentage': 0}

        # Get income for the period
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions
            WHERE type = 'income' AND date BETWEEN ? AND ?
        ''', (goal['start_date'], goal['end_date']))
        current = cursor.fetchone()[0]

        target = goal['target_amount']
        percentage = (current / target * 100) if target > 0 else 0

        return {
            'has_goal': True,
            'target': target,
            'current': current,
            'percentage': min(percentage, 100),
            'start_date': goal['start_date'],
            'end_date': goal['end_date']
        }

    def get_recent_transactions(self, limit: int = 5) -> List[Dict]:
        """Get most recent transactions."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions ORDER BY date DESC, created_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # ==================== PDF INVOICE GENERATION ====================

    def generate_invoice_pdf(self, invoice_id: int, output_path: str) -> bool:
        """
        Generate a PDF invoice using reportlab.

        Args:
            invoice_id: The invoice ID.
            output_path: Path to save the PDF file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.units import inch
        except ImportError:
            print("reportlab not installed. Run: pip install reportlab")
            return False

        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return False

        items = self.get_invoice_items(invoice_id)

        # Create the PDF document
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()
        story = []

        # Header
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF6B35'),
            spaceAfter=20
        )
        story.append(Paragraph("INVOICE", title_style))

        # Invoice info
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        )

        invoice_info = f"""
        <b>Invoice #:</b> {invoice.get('invoice_number', '')}<br/>
        <b>Date:</b> {invoice.get('created_date', '')}<br/>
        <b>Due Date:</b> {invoice.get('due_date', 'N/A')}<br/>
        <b>Status:</b> {invoice.get('status', '').upper()}
        """
        story.append(Paragraph(invoice_info, info_style))
        story.append(Spacer(1, 20))

        # Bill To
        bill_to = f"""
        <b>Bill To:</b><br/>
        {invoice.get('client_name', 'N/A')}<br/>
        {invoice.get('client_email', '')}
        """
        story.append(Paragraph(bill_to, info_style))
        story.append(Spacer(1, 20))

        # Items table
        table_data = [['Description', 'Qty', 'Unit Price', 'Total']]
        for item in items:
            table_data.append([
                item.get('description', ''),
                str(item.get('quantity', 1)),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total', 0):.2f}"
            ])

        table = Table(table_data, colWidths=[4*inch, 0.75*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Totals
        totals_data = [
            ['Subtotal:', f"${invoice.get('subtotal', 0):.2f}"],
            [f"Tax ({invoice.get('tax_rate', 0):.1f}%):", f"${invoice.get('tax_amount', 0):.2f}"],
            ['TOTAL:', f"${invoice.get('total', 0):.2f}"]
        ]
        totals_table = Table(totals_data, colWidths=[5.75*inch, 1*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#FF6B35')),
        ]))
        story.append(totals_table)

        # Notes and Terms
        if invoice.get('notes'):
            story.append(Spacer(1, 30))
            story.append(Paragraph("<b>Notes:</b>", info_style))
            story.append(Paragraph(invoice.get('notes', ''), info_style))

        if invoice.get('terms'):
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>Terms:</b>", info_style))
            story.append(Paragraph(invoice.get('terms', ''), info_style))

        # Footer
        story.append(Spacer(1, 40))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=1  # Center
        )
        story.append(Paragraph("Generated by ProducerOS | produceros.app", footer_style))

        # Build PDF
        doc.build(story)
        return True


# Singleton instance
_business_manager_instance: Optional[BusinessManager] = None


def get_business_manager() -> BusinessManager:
    """Get the global BusinessManager instance."""
    global _business_manager_instance
    if _business_manager_instance is None:
        _business_manager_instance = BusinessManager()
    return _business_manager_instance
