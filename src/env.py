import os

SQLHOST = os.environ.get("SQLHOST","localhost:5432")

DBUSER = os.environ.get("DBUSER",'postgres')
DBPASS = os.environ.get("DBPASS",'mysecretpassword')
DBTABLE = os.environ.get("DBTABLE",'sysml2')

HARBORHOST = os.environ.get("HARBORHOST","http://harbor-core.harbor/api/v2.0")
HARBORUSER = os.environ.get("HARBORUSER",'admin')
HARBORPASS = os.environ.get("HARBORPASS",'Harbor12345')

WINDSTORMHOST = os.environ.get(
    "WINDSTORMHOST",
    "http://windstorm-webhook-eventsource-svc.argo-events:12000/windstorm"
)
