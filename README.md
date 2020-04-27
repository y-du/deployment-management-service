### /deployments

**GET**

_List all deployments._

    Response media type: application/json
    
    {
      "image": <string>,
      "hash": <string>,
      "state": <string>     # "running", "stopped"
    }

**POST**

_Create a deployment._

    Request media type: application/json
    
    {
      "name": <string>,
      "deployment_configs": {
        "image": <string>,
        "volumes": {<string>:<string>},
        "devices": {<string>:<string>},
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

**PATCH**

_Start / stop deployment._


    Request media type: application/json
    
    {
      "state": <string>     # "running", "stopped"
    }

**DELETE**

_Remove deployment._