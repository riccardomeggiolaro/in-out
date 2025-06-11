import json

k = {
    "apps": {
        "http": {
            "servers": {
                "srv0": {
                    "listen": [":443"],
                    "routes": [{
                        "handle": [{
                            "handler": "subroute",
                            "routes": [
                                {
                                    "handle": [{
                                        "handler": "headers",
                                        "response": {
                                            "deferred": True,
                                            "set": {
                                                "Access-Control-Allow-Credentials": ["true"],
                                                "Access-Control-Allow-Headers": ["*"],
                                                "Access-Control-Allow-Methods": ["*"],
                                                "Access-Control-Allow-Origin": ["*"]
                                            }
                                        }
                                    }]
                                },
                                # GPS Gate Server route
                                {
                                    "group": "group14",
                                    "handle": [{
                                        "handler": "subroute",
                                        "routes": [
                                            {"handle": [{"handler": "rewrite", "strip_path_prefix": "/gpsgateserver"}]},
                                            {"group": "group9", "handle": [{"handler": "rewrite", "uri": "/GpsGateServer{http.request.uri.path}"}]},
                                            {"handle": [{"handler": "reverse_proxy", "upstreams": [{"dial": "10.0.8.101:80"}]}]}
                                        ]
                                    }],
                                    "match": [{"path": ["/gpsgateserver/*"]}]
                                },
                                # Pesi pes002 route
                                {
                                    "group": "group14",
                                    "handle": [{
                                        "handler": "subroute",
                                        "routes": [
                                            {"handle": [{"handler": "rewrite", "strip_path_prefix": "/pesi/pes002"}]},
                                            {"group": "group0", "handle": [{"handler": "rewrite", "uri": "{http.request.uri.path}"}]},
                                            {"handle": [{"handler": "reverse_proxy", "upstreams": [{"dial": "172.20.0.23:80"}]}]}
                                        ]
                                    }],
                                    "match": [{"path": ["/pesi/pes002/*"]}]
                                },
                                # Other routes follow same pattern...
                            ]
                        }],
                        "match": [{"host": ["on.baron.it"]}],
                        "terminal": True
                    }]
                }
            }
        }
    }
}

# Pretty print the dictionary
print(json.dumps(k, indent=4))