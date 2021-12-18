import pathlib
import typing as t

import yaml
from oasbuilder.constants import TEMPLATE_OAS_REF
from oasbuilder.models import HTTPMethod, SchemaType
from oasbuilder.types import YAML
from oasbuilder.utils import build_schema_identifier, endpoint_dir, response_description
from oasbuilder.utils.decorators import ensure_dest_exists


class OASResponseContentWriter:
    """
    description: Expected response to a valid request
    content:
      application/json:
        schema:
          type: object
          properties:
            id:
              type: integer
              format: int64
            name:
              type: string
    """

    def __init__(
        self,
        dest_root: pathlib.Path,
        endpoint_path: str,
        method: HTTPMethod,
        status_code: int,
        response_content: t.Optional[t.Any],
    ) -> None:
        self.dest_root = dest_root
        self.endpoint_path = endpoint_path
        self.method = method
        self.status_code = status_code
        self.response_content = response_content
        self.dest = (
            self.dest_root
            / endpoint_dir(self.endpoint_path)
            / self.method.value
            / "responses"
            / str(self.status_code)
            / "_index.yml"
        )

    @ensure_dest_exists
    def write(self):
        oas_yaml = self._build()
        self.dest.write_text(oas_yaml)

    def _build(self) -> YAML:
        description = response_description(self.status_code)
        oas_json: t.Dict[str, t.Any] = {
            "description": description,
        }
        if self.response_content and (
            isinstance(self.response_content, dict)
            or isinstance(self.response_content, list)
        ):
            schema_id = build_schema_identifier(
                self.method, self.endpoint_path, SchemaType.RESPONSE_BODY
            )
            oas_json["content"] = {
                "application/json": {
                    "schema": {TEMPLATE_OAS_REF: f"#/components/schemas/{schema_id}"}
                }
            }
        return yaml.dump(oas_json)
