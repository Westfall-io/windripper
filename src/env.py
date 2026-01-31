# Copyright (c) 2023-2024 Westfall Inc.
#
# This file is part of Windripper.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, and can be found in the file NOTICE inside this
# git repository.
#
# This program is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
env — environment configuration for Windripper

This module exposes configuration values read from environment variables
with reasonable defaults. These constants are used by the application to
configure database connectivity, Harbor registry access, and the Windstorm
webhook target.

Variables:
- `SQLHOST`: database host and port (default: "localhost:5432").
- `DBUSER`, `DBPASS`, `DBTABLE`: database user, password and database name.
- `HARBORHOST`, `HARBORUSER`, `HARBORPASS`: Harbor registry API endpoint
    and credentials.
- `WINDSTORMHOST`: URL to post notifications to the Windstorm webhook.
"""

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
