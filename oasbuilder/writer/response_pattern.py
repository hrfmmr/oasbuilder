import pathlib
import re

import yaml
from oasbuilder.models import HTTPMethod
from oasbuilder.types import YAML
from oasbuilder.utils import endpoint_dir
from oasbuilder.utils.decorators import ensure_dest_exists


class OASResponsePatternWriter:
    """
    '200':
      $ref: '200/_index.yml'
    """

    def __init__(
        self,
        dest_root: pathlib.Path,
        endpoint_path: str,
        method: HTTPMethod,
    ) -> None:
        self.dest_root = dest_root
        self.endpoint_path = endpoint_path
        self.method = method

        self.dest = (
            self.dest_root
            / endpoint_dir(self.endpoint_path)
            / self.method.value
            / "responses"
            / "_index.yml"
        )
        self.rex_status_code = re.compile(
            r"^{}/(?P<status_code>[\d]+)/_index.ya?ml$".format(str(self.dest.parent))
        )

    def _build(self) -> YAML:
        paths = self.dest.parent.glob("**/*.yml")
        oas_json = {}
        for p in paths:
            result = re.match(self.rex_status_code, str(p))
            if not result:
                continue
            status_code = result.group("status_code")
            oas_json[status_code] = {"$ref": f"{status_code}/_index.yml"}
        return yaml.dump(oas_json)

    @ensure_dest_exists
    def write(self):
        oas_yaml = self._build()
        self.dest.write_text(oas_yaml)
