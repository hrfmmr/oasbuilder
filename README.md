# oasbuilder
OpenAPI Specification generator by using JSON stored via [mitmproxy's addon](https://github.com/hrfmmr/mitmproxy-elasticagent)

## Usage
1. Configure `.env` for Elasticsearch host and its index storing structured API endpoint's schema posted from [mitmproxy's addon](https://github.com/hrfmmr/mitmproxy-elasticagent)
1. Run `make bootstrap && make run`
1. Check artifacts at `.build/bundle.yml`(Also you can see the generated OAS docs as HTML at `.build/index.html`)
