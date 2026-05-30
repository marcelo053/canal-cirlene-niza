import requests
from typing import Any
from loguru import logger


class BaserowClient:
    """Baserow API client for Canal Cirlene Niza state layer."""

    def __init__(self, base_url: str, token: str, database_id: int = 0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.database_id = database_id
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Token {token}"})

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/api{path}"
        resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def get_productions(self) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            f"/database/rows/table/{self.database_id}/",
            params={"user_field_names": True}
        ).get("results", [])

    def create_production(self, fields: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/database/rows/table/{self.database_id}/",
            json={"fields": fields}
        )

    def update_scene(self, scene_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/database/rows/table/{self.database_id}/{scene_id}/",
            json={"fields": fields}
        )

    def create_row(self, table_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/database/rows/table/{table_id}/?user_field_names=true",
            json=fields,
        )

    def update_row(self, table_id: int, row_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/database/rows/table/{table_id}/{row_id}/?user_field_names=true",
            json=fields,
        )

    def list_rows(
        self,
        table_id: int,
        filter_field: str | None = None,
        filter_value: str | None = None,
        order_by: str = "-id",
        size: int = 100,
    ) -> list[dict[str, Any]]:
        """List rows from a table, optionally filtered by a single field value."""
        params: dict[str, Any] = {"user_field_names": "true", "order_by": order_by, "size": size}
        if filter_field and filter_value is not None:
            params[f"filter__{filter_field}__equal"] = filter_value
        return self._request(
            "GET",
            f"/database/rows/table/{table_id}/",
            params=params,
        ).get("results", [])

    def get_style_guide(self, production_id: int) -> dict[str, Any] | None:
        """Get Visual Style Guide for a production from Baserow."""
        rows = self._request(
            "GET",
            f"/database/rows/table/{self.database_id}/",
            params={
                "filter__field_123": f"eq.{production_id}",
                "user_field_names": True
            }
        ).get("results", [])
        return rows[0] if rows else None