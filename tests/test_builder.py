import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException

from app.services.geospatial import (
    GEOSPATIAL_API_ERROR_DETAIL,
    GeospatialServiceError,
)
from app.routers.builder import modeler_logic


class BuilderErrorHandlingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.input_data = Mock()
        self.input_data.model_dump_json.return_value = "{}"

    async def test_each_geospatial_api_failure_returns_the_user_message(self):
        upstream_errors = (
            "GLO-30 API returned HTTP 422",
            "ESA WorldCover API request failed",
            "WorldPop API returned HTTP 502",
        )

        for upstream_error in upstream_errors:
            with self.subTest(upstream_error=upstream_error):
                with patch(
                    "app.routers.builder.modeler",
                    new_callable=AsyncMock,
                    side_effect=GeospatialServiceError(upstream_error),
                ):
                    with self.assertRaises(HTTPException) as raised:
                        await modeler_logic(self.input_data, Mock())

                self.assertEqual(raised.exception.status_code, 502)
                self.assertEqual(
                    raised.exception.detail,
                    GEOSPATIAL_API_ERROR_DETAIL,
                )

    async def test_existing_worldpop_http_error_takes_precedence(self):
        worldpop_error = HTTPException(
            status_code=422,
            detail="WorldPop does not have population data for this location.",
        )

        with patch(
            "app.routers.builder.modeler",
            new_callable=AsyncMock,
            side_effect=worldpop_error,
        ):
            with self.assertRaises(HTTPException) as raised:
                await modeler_logic(self.input_data, Mock())

        self.assertIs(raised.exception, worldpop_error)


if __name__ == "__main__":
    unittest.main()
