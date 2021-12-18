import json
import logging
import os
import pathlib
import subprocess
import typing as t
from collections import defaultdict
from urllib.parse import parse_qs, urlparse

import yaml
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from oasbuilder.constants import OAS_REF, TEMPLATE_OAS_REF
from oasbuilder.logging import setup_logger
from oasbuilder.models import HTTPMethod
from oasbuilder.utils import parameterized_endpoint_path
from oasbuilder.writer import (
    OASEndpointMethodPatternWriter,
    OASEndpointMethodWriter,
    OASEndpointPatternWriter,
    OASIndexWriter,
    OASRequestBodySchemaWriter,
    OASResponseContentWriter,
    OASResponsePatternWriter,
    OASResponseSchemaWriter,
    OASSchemaIndexWriter,
)

load_dotenv()
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.environ["ELASTICSEARCH_INDEX"]
DEST_DIR = pathlib.Path(".build")
OAS_YAML_DEST = DEST_DIR / "bundle.yml"
OAS_HTML_DEST = DEST_DIR / "index.html"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def write_schemas(
    dest_root: pathlib.Path,
    endpoint_path: str,
    method: HTTPMethod,
    query: t.Optional[t.Dict[str, t.Any]],
    request_content: t.Optional[t.Dict[str, t.Any]],
    status_code: int,
    response_content: t.Optional[t.Dict[str, t.Any]],
):
    if request_content:
        OASRequestBodySchemaWriter(
            dest_root,
            endpoint_path,
            method,
            request_content=request_content,
        ).write()

    if response_content and (
        type(response_content) is dict or type(response_content) is list
    ):
        OASResponseSchemaWriter(
            dest_root,
            endpoint_path,
            method,
            status_code,
            response_content,
        ).write()


def main():
    setup_logger()
    es = Elasticsearch(ELASTICSEARCH_HOST)

    result = es.search(
        index=ELASTICSEARCH_INDEX,
        aggs=dict(
            requestpaths=dict(terms=dict(field="request.path.keyword", size=10_000))
        ),
        _source=[
            "request.path",
        ],
    )
    path_query_map = defaultdict(list)
    for bucket in result["aggregations"]["requestpaths"]["buckets"]:
        path = bucket["key"]
        parsed = urlparse(path)
        parameterized_path = parameterized_endpoint_path(parsed.path)
        path_query_map[parameterized_path].append(parse_qs(parsed.query))
    dest_root = pathlib.Path(DEST_DIR)
    pattern_set = set()
    for path in list(path_query_map.keys()):
        logger.info(f"path:{path}")
        result = es.search(
            index=ELASTICSEARCH_INDEX,
            query=dict(term={"request.path.keyword": path}),
            _source=[
                "request.method",
                "request.query",
                "request.content",
                "response.status_code",
                "response.content",
            ],
        )
        if not (result["hits"] and result["hits"]["hits"]):
            continue
        hits = result["hits"]["hits"]
        for hit in hits:
            info = hit["_source"]
            method = HTTPMethod[info["request"]["method"]]
            query = json.loads(info["request"]["query"])
            request_content_raw = info["request"]["content"]
            status_code = info["response"]["status_code"]
            request_content = (
                json.loads(request_content_raw) if request_content_raw else None
            )
            response_content_raw = info["response"]["content"]
            try:
                response_content = (
                    json.loads(response_content_raw) if response_content_raw else None
                )
            except json.decoder.JSONDecodeError:
                response_content = None

            pattern = (
                path,
                method.value,
                status_code,
            )
            if pattern in pattern_set:
                continue

            pattern_set.add(pattern)

            write_schemas(
                dest_root,
                path,
                method,
                query,
                request_content,
                status_code,
                response_content,
            )

            OASResponseContentWriter(
                dest_root,
                path,
                method,
                status_code,
                response_content,
            ).write()

            OASResponsePatternWriter(
                dest_root,
                path,
                method,
            ).write()

            OASEndpointMethodWriter(
                dest_root,
                path,
                method,
                query=query,
                request_content=request_content,
            ).write()
        OASEndpointMethodPatternWriter(dest_root, path).write()
    OASEndpointPatternWriter(dest_root).write()

    schema_index_writer = OASSchemaIndexWriter(dest_root)
    schema_index_writer.write()

    index_writer = OASIndexWriter(
        dest_root,
        openapi_version="3.0.0",
        version=os.environ["OAS_VERSION"],
        title=os.environ["OAS_TITLE"],
        description=os.environ["OAS_DESCRIPTION"],
        server_urls=os.environ["OAS_SERVER_URLS"].split(","),
        components={"schemas": yaml.safe_load(schema_index_writer.dest.read_text())},
    )
    index_writer.write()

    subprocess.run(
        [
            "./node_modules/.bin/swagger-cli",
            "bundle",
            str(index_writer.dest),
            "--outfile",
            str(OAS_YAML_DEST),
            "--type",
            "yaml",
        ],
        check=True,
    )
    raw_oas_yaml = OAS_YAML_DEST.read_text()
    ref_enabled = raw_oas_yaml.replace(TEMPLATE_OAS_REF, OAS_REF)
    OAS_YAML_DEST.write_text(ref_enabled)
    subprocess.run(
        [
            "./node_modules/.bin/spectral",
            "lint",
            str(OAS_YAML_DEST),
        ],
        check=True,
    )
    subprocess.run(
        [
            "node_modules/.bin/redoc-cli",
            "bundle",
            str(OAS_YAML_DEST),
            "--output",
            OAS_HTML_DEST,
            "--options.onlyRequiredInSamples",
        ],
        check=True,
    )
    print(f"👉Check the output:{pathlib.Path(OAS_HTML_DEST).resolve()}")
    print("✨Done")


if __name__ == "__main__":
    main()
