"""Client Manager for Beatflow - CRM functionality for music producers."""

import webbrowser
from typing import Dict, List, Optional
from core.database import get_database


class ClientManager:
    """Manages client data and social link integrations."""

    def __init__(self):
        self.db = get_database()

    def add_client(self, data: Dict) -> int:
        """
        Add a new client.

        Args:
            data: Dict with client fields (name, email, phone, instagram, twitter, website, notes).

        Returns:
            The ID of the created client.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO clients (name, email, phone, instagram, twitter, website, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('instagram', ''),
            data.get('twitter', ''),
            data.get('website', ''),
            data.get('notes', '')
        ))
        conn.commit()
        return cursor.lastrowid

    def get_clients(self, sort_by: str = 'name', search: str = None) -> List[Dict]:
        """
        Get all clients.

        Args:
            sort_by: Field to sort by ('name', 'created_at').
            search: Optional search string to filter by name.

        Returns:
            List of client dicts.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Validate sort field
        valid_sorts = {'name': 'name', 'created_at': 'created_at', 'id': 'id'}
        sort_field = valid_sorts.get(sort_by, 'name')

        if search:
            cursor.execute(f'''
                SELECT * FROM clients
                WHERE name LIKE ?
                ORDER BY {sort_field}
            ''', (f'%{search}%',))
        else:
            cursor.execute(f'SELECT * FROM clients ORDER BY {sort_field}')

        return [dict(row) for row in cursor.fetchall()]

    def get_client(self, client_id: int) -> Optional[Dict]:
        """
        Get a client by ID.

        Args:
            client_id: The client's ID.

        Returns:
            Client dict or None if not found.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_client(self, client_id: int, data: Dict) -> bool:
        """
        Update a client's information.

        Args:
            client_id: The client's ID.
            data: Dict with fields to update.

        Returns:
            True if updated, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        fields = ['name', 'email', 'phone', 'instagram', 'twitter', 'website', 'notes']
        updates = []
        values = []

        for field in fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])

        if not updates:
            return False

        values.append(client_id)
        query = f'UPDATE clients SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

    def delete_client(self, client_id: int) -> bool:
        """
        Delete a client.

        Args:
            client_id: The client's ID.

        Returns:
            True if deleted, False otherwise.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_client_count(self) -> int:
        """Get total number of clients."""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM clients')
        return cursor.fetchone()[0]

    @staticmethod
    def open_social_link(platform: str, handle: str) -> bool:
        """
        Open a social media link in the default browser.

        Args:
            platform: Social platform ('instagram', 'twitter', 'website').
            handle: The handle/URL to open.

        Returns:
            True if opened successfully, False otherwise.
        """
        if not handle:
            return False

        # Clean up handle
        handle = handle.strip()

        # Build URL based on platform
        if platform == 'instagram':
            # Handle could be @handle, handle, or full URL
            if handle.startswith('http'):
                url = handle
            else:
                handle = handle.lstrip('@')
                url = f'https://instagram.com/{handle}'
        elif platform == 'twitter':
            if handle.startswith('http'):
                url = handle
            else:
                handle = handle.lstrip('@')
                url = f'https://twitter.com/{handle}'
        elif platform == 'website':
            # Add https:// if missing
            if not handle.startswith(('http://', 'https://')):
                url = f'https://{handle}'
            else:
                url = handle
        else:
            return False

        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False


# Singleton instance
_client_manager_instance: Optional[ClientManager] = None


def get_client_manager() -> ClientManager:
    """Get the global ClientManager instance."""
    global _client_manager_instance
    if _client_manager_instance is None:
        _client_manager_instance = ClientManager()
    return _client_manager_instance
