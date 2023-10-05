import time
start_time = time.time()

import os

SQLDEF = "localhost:5432"
SQLHOST = os.environ.get("SQLHOST",SQLDEF)

from datetime import datetime

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
    image: Mapped[str] = mapped_column(db.String(255))
    tag: Mapped[str] = mapped_column(db.String(255))

class Container_Commits(Base):
    __tablename__ = "container_commits"
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    containers_id: Mapped[int] = mapped_column(db.ForeignKey("containers.id"))
    digest: Mapped[str] = mapped_column(db.String(64))
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
        result = session \
            .query(Containers) \
            .filter(
                Containers.project == project,
                Containers.image == image,
                Containers.tag == tag,
            ) \
            .first()
        if result is None:
            this_c = Containers(
                resource_url = wh_resource_url,
                host = host,
                project = project,
                image = image,
                tag = tag,
            )
            session.add(this_c)
            session.commit()
            result = session \
                .query(Containers) \
                .filter(
                    Containers.project == project,
                    Containers.image == image,
                    Containers.tag == tag,
                ) \
                .first()

        this_cc = Container_Commits(
            containers_id = result.id,
            digest = digest,
            date = datetime.now()
        )
        session.add(this_c)
        session.commit()

    print('Closing session.')
    c.close()
    engine.dispose()

    #requests.post(WINDSTORMHOST, json={'ref'=ref, 'commit':commit})

if __name__ == '__main__':
    import fire
    fire.Fire(main)
    print("--- %s seconds ---" % (time.time() - start_time))
