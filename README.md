### /deployments

**GET**

_List all deployments._

    Response media type: application/json
    
    {
      "image": <string>,
      "hash": <string>,
      "state": <string>     # "active", "inactive"
    }

**POST**

_Create a deployment._

    Request media type: application/json
    
    {
      "name": <string>,
      "deployment_configs": {
        "image": <string>,
        "volumes": {<string>:<string>},
        "ports": [
          {
            "container": <number>,
            "host": <number>,
            "protocol": <string/Null>       # "tcp", "udp", "sctp"
          }
        ]
      },
      "service_configs": {<string>:<string/number>},
      "runtime_vars": {<string>:<string/number>}
    }


### /deployments/{deployment}

**PUT**

_Start / stop deployment._


    Request media type: application/json
    
    {
      "image": <string>,
      "hash": <string>,
      "state": <string>     # "active", "inactive"
    }

**DELETE**

_Remove deployment._