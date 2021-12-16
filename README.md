# oasbuilder
OpenAPI Specification generator by using JSON stored via [mitmproxy-elasticagent](https://github.com/hrfmmr/mitmproxy-elasticagent)

## Set up
`$ make`

## Usage
1. Configure `.env` for Elasticsearch host and its index storing structured API endpoint's schema posted from [mitmproxy-elasticagent](https://github.com/hrfmmr/mitmproxy-elasticagent) and other OAS metadata.
1. Run `$ make run`
1. Check artifacts at `.build/bundle.yml`(Also you can see the generated OAS docs as HTML at `.build/index.html`)
