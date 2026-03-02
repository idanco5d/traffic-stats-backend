from unittest.mock import MagicMock, patch

# Patch firebase_admin before any test module imports main
patch("firebase_admin.firestore.client", return_value=MagicMock()).start()
patch("firebase_admin.initialize_app", return_value=MagicMock()).start()