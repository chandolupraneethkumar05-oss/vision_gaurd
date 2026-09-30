"""Camera registry and metadata manager."""
from typing import Dict, Any, List, Optional
from visionguard.database.db_manager import db

class CameraRegistry:
    """Provides fast in-memory access and updates to urban camera feeds."""

    def __init__(self):
        self._cameras: Dict[str, Dict[str, Any]] = {}
        self.reload()

    def reload(self):
        """Loads cameras from database into fast lookup dictionary."""
        cams = db.get_all_cameras()
        self._cameras = {c["camera_id"]: c for c in cams}

    def get(self, camera_id: str) -> Optional[Dict[str, Any]]:
        return self._cameras.get(camera_id)

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._cameras.values())

camera_registry = CameraRegistry()
