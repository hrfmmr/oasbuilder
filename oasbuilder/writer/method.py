import logging
import pathlib
import typing as t

import yaml
from oasbuilder.constants import TEMPLATE_OAS_REF
from oasbuilder.models import HTTPMethod, OASParameter, OASParameterSchema, SchemaType
from oasbuilder.parser import OASParser
from oasbuilder.types import YAML
from oasbuilder.utils import (
    build_operation_id,
    build_path_params,
    build_schema_identifier,
    endpoint_dir,
)
from oasbuilder.utils.decorators import ensure_dest_exists

logger = logging.getLogger(__name__)

RES_DELIMITER = "_"


class OASEndpointMethodWriter:
    """
    summary: Info for a specific pet
    operationId: showPetById
    tags:
      - pets
    responses:
      $ref: "responses/_index.yml"
    """

    def __init__(
        self,
        dest_root: pathlib.Path,
        endpoint_path: str,
        method: HTTPMethod,
        query: t.Optional[t.Dict[str, t.Any]] = None,
        request_content: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        self.dest_root = dest_root
        self.endpoint_path = endpoint_path
        self.method = method
        self.query = query
        self.request_content = request_content
        self.dest = (
            self.dest_root
            / endpoint_dir(self.endpoint_path)
            / self.method.value
            / "_index.yml"
        )

    @ensure_dest_exists
    def write(self):
        oas_yaml = self._build()
        self.dest.write_text(oas_yaml)

    def _build(self) -> YAML:
        oas_json: t.Dict[str, t.Any] = {
            "summary": "",
            "operationId": build_operation_id(self.method, self.endpoint_path),
            "responses": {"$ref": "responses/_index.yml"},
        }
        if self.request_content:
            schema_id = build_schema_identifier(
                self.method, self.endpoint_path, SchemaType.REQUEST_BODY
            )
            oas_json["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": {
                            TEMPLATE_OAS_REF: f"#/components/schemas/{schema_id}"
                        }
                    }
                }
            }
        params = []
        path_params = build_path_params(self.endpoint_path)
        if path_params:
            params.extend(
                [
                    OASParameter(
                        _in="path",
                        name=k,
                        required=True,
                        schema=OASParameterSchema(
                            type=OASParser.gettype(type(v).__name__)
                        ),
                    )
                    for k, v in path_params.items()
                ]
            )
        if self.query:
            params.extend(
                [
                    OASParameter(
                        _in="query",
                        name=k,
                        required=False,
                        schema=OASParameterSchema(
                            type=OASParser.gettype(type(v).__name__)
                        ),
                    )
                    for k, v in self.query.items()
                ]
            )
        if params:
            oas_json["parameters"] = [p.build_oas_json() for p in params]
        return yaml.dump(oas_json)
