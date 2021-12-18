import pathlib
import typing as t
from dataclasses import asdict

import yaml
from oasbuilder.models import OASIndexInfo, OASServer, OASSpecInfo
from oasbuilder.types import YAML
from oasbuilder.utils import endpoint_root_dir


class OASIndexWriter:
    """
    openapi: "3.0.0"
    info:
      version: 1.0.0
      title: Swagger Petstore
      description: Multi-file boilerplate for OpenAPI Specification.
      license:
        name: MIT
    servers:
      - url: http://petstore.swagger.io/v1
    paths:
      /pets:
        $ref: "paths/pets/_index.yml"
    """

    def __init__(
        self,
        dest_root: pathlib.Path,
        openapi_version: str,
        version: str,
        title: str,
        description: str,
        server_urls: t.Optional[t.List[str]] = None,
        components: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        self.dest_root = dest_root
        if not server_urls:
            server_urls = []
        if not components:
            components = {}
        self.info = OASIndexInfo(
            openapi=openapi_version,
            info=OASSpecInfo(version, title, description),
            servers=[OASServer(url) for url in server_urls],
            paths={"$ref": str(endpoint_root_dir() / "_index.yml")},
            components=components,
        )
        self.dest = self.dest_root / "index.yml"

    def write(self):
        oas_yaml = self._build()
        self.dest.write_text(oas_yaml)

    def _build(self) -> YAML:
        oas_json = asdict(self.info)
        return yaml.dump(oas_json)
