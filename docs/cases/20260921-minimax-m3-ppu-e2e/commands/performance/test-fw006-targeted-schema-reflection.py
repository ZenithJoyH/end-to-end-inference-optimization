import tempfile
from pathlib import Path

import sqlalchemy

from flag_gems.utils.models.sql import SQLPersistantModel


with tempfile.TemporaryDirectory(prefix="fw006-") as tmpdir:
    db_path = Path(tmpdir) / "unit.db"
    engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
    metadata = sqlalchemy.MetaData()
    sqlalchemy.Table(
        "wanted",
        metadata,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    )
    sqlalchemy.Table(
        "decoy",
        metadata,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    )
    metadata.create_all(engine)

    wanted = SQLPersistantModel.build_sql_model_by_db("wanted", engine)
    assert wanted is not None
    assert wanted.__table__.name == "wanted"
    assert SQLPersistantModel.build_sql_model_by_db("missing", engine) is None

print("fw006_targeted_schema_reflection=passed")
