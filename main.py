# Copyright (c) 2023-2024 Westfall Inc.
#
# This file is part of Windstorm-Dwarven.
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

import time
start_time = time.time()

import os

SQLHOST = os.environ.get("SQLHOST","localhost:5432")
WINDSTORMHOST = os.environ.get(
    "WINDSTORMHOST",
    "http://windstorm-webhook-eventsource-svc.argo-events:12000/windstorm"
)

import json
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth
import sqlalchemy as db
from sqlalchemy.orm import DeclarativeBase, Mapped, \
    mapped_column, MappedAsDataclass, relationship, Session

class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""

class Containers(Base):
    __tablename__ = "containers"
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    resource_url: Mapped[str] = mapped_column(db.String(255))
    host: Mapped[str] = mapped_column(db.String(255))
    project: Mapped[str] = mapped_column(db.String(255))
    project_id: Mapped[int] = mapped_column(db.Integer())
    image: Mapped[str] = mapped_column(db.String(255))
    image_id: Mapped[int] = mapped_column(db.Integer())
    tag: Mapped[str] = mapped_column(db.String(255))

class Container_Commits(Base):
    __tablename__ = "container_commits"
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    containers_id: Mapped[int] = mapped_column(db.ForeignKey("containers.id"))
    digest: Mapped[str] = mapped_column(db.String(64))
    cmd: Mapped[str] = mapped_column(db.String())
    working_dir: Mapped[str] = mapped_column(db.String(255))
    date: Mapped[datetime] = mapped_column(default=None)

def connect():
    db_type = "postgresql"
    user = "postgres"
    passwd = "mysecretpassword"
    address = SQLHOST
    db_name = "sysml2"

    address = db_type+"://"+user+":"+passwd+"@"+address+"/"+db_name
    engine = db.create_engine(address)
    conn = engine.connect()

    return conn, engine

def get_container_info_harbor(proj, repo):
    domain = "http://harbor-core.harbor/api/v2.0"
    proj_url = "projects"
    repo_url = "repositories"
    artifact_url = "artifacts"

    info = {}

    print('Attempting to connect to harbor API.')
    r = requests.get(
        os.path.join(domain, proj_url, proj, repo_url, repo, artifact_url),
        auth=HTTPBasicAuth('admin', 'Harbor12345'))

    if 'errors' in r.json():
        if r.json()['errors'][0]['code'] == 'UNAUTHORIZED':
            print(r.request.url)
            print(r.request.body)
            print(r.request.headers)
            raise NotImplementedError('UNAUTHORIZED')

    if len(r.json()) == 0:
        print(proj, repo)
        raise NotImplementedError('Failed to get results from harbor api.')

    try:
        data = r.json()[0]
        config = data["extra_attrs"]["config"]
        info['project_id'] = data["project_id"]
        info['image_id'] = data["repository_id"]

    except KeyError:
        print(r.json())
        raise KeyError('Failed to find an entry.')
    except IndexError:
        print(r.json())
        raise KeyError('Failed to find an entry.')

    if 'entrypoint' in [x.lower() for x in data.keys()]:
        raise NotImplementedError('Cant handle this yet.')

    info['working_dir'] = config['WorkingDir']
    info['cmd'] = json.dumps(config['Cmd'])

    return info

def main(wh_type, wh_resource_url, wh_digest):
    if wh_type != 'PUSH_ARTIFACT':
        # This was not a push, disregard.
        return

    print('Parsing inputs')
    tagparts = wh_resource_url.split(':')
    tag = tagparts[1]
    urlparts = tagparts[0].split('/')
    host = urlparts[0]
    project = urlparts[1]
    image = urlparts[2]

    digest = wh_digest[7:]

    print('Pushing to database')
    c, engine = connect()
    with Session(engine) as session:

        # Check if this container is in the db.
        result = session \
            .query(Containers) \
            .filter(
                Containers.project == project,
                Containers.image == image,
                Containers.tag == tag,
            ) \
            .first()

        if result is None:
            # This container is not in the db.
            this_c = Containers(
                resource_url = wh_resource_url,
                host = host,
                project = project,
                project_id = None,
                image = image,
                image_id = None,
                tag = tag,
            )

            # Add it to the db.
            session.add(this_c)
            session.commit()
            print('Added {} to containers.'.format(wh_resource_url))

            # Search again to get the newly added row.
            result = session \
                .query(Containers) \
                .filter(
                    Containers.project == project,
                    Containers.image == image,
                    Containers.tag == tag,
                ) \
                .first()
        else:
            print('Found {} in containers.'.format(wh_resource_url))

        container_id = result.id

        info = get_container_info_harbor(project, image)

        this_cc = Container_Commits(
            containers_id = container_id,
            digest = digest,
            date = datetime.now(),
            cmd = info['cmd'],
            working_dir = info['working_dir']
        )
        session.add(this_cc)
        session.commit()
        print('Added digest--{} to container {}.'.format(digest, container_id))

        # Check to see if updates are needed to container info
        if result.project_id is None and info['cmd'] is not None:
            _ = session \
                .query(Containers) \
                .filter(Containers.id == container_id) \
                .update({
                    'project_id': info['project_id'],
                    'image_id': info['image_id']
                })
            session.commit()

    print('Closing session.')
    c.close()
    engine.dispose()

    requests.post(WINDSTORMHOST, json = {
        'source' : 'ripper',
        'payload' : {
            'container_id': container_id
        }
    })

if __name__ == '__main__':
    import fire
    fire.Fire(main)
    print("--- %s seconds ---" % (time.time() - start_time))
