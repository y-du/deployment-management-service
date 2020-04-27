### /deployments

**GET**

_List all deployments._

    Response media type: application/json
    
    {
      <string>: {
        "image": <string>,
        "hash": <string>,
        "state": <string>       # "running", "stopped"
      },
      ...
    }


**POST**

_Create a deployment._

_Creates container. If container exists and not running removes it first._

    Request media type: application/json
    
    {
      "name": <string>,
      "deployment_configs": {
        "image": <string>,
        "volumes": {<string>:<string>},                 # can be null
        "devices": {<string>:<string>},                 # can be null
        "ports": [                                      # can be null
          {
            "container": <number>,
            "host": <number>,
            "protocol": <string/Null>                   # "tcp", "udp", "sctp"
          }
        ]
      },
      "service_configs": {<string>:<string/number>},    # can be null
      "runtime_vars": {<string>:<string/number>}        # can be null
    }


### /deployments/{deployment}

**PATCH**

_Start / stop deployment._

_Start or stop container._

    Request media type: application/json
    
    {
      "state": <string>     # "running", "stopped"
    }

**DELETE**

_Remove deployment._

_Container must be stopped. Removes container, volumes, image._