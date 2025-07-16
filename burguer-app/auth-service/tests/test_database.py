import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_get_db_returns_correct_db_instance():

    with patch('pymongo.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        
        from config.database import get_db


        with patch('config.database.client', mock_client.return_value):
            db_instance = get_db()
            assert db_instance is not None
        
        