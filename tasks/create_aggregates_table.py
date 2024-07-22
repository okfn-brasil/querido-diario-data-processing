from .interfaces import DatabaseInterface


def create_aggregates_table(database: DatabaseInterface):
    database._commit_changes(
        """
        CREATE TABLE IF NOT EXISTS aggregates (
            id SERIAL PRIMARY KEY ,
            territory_id VARCHAR,
            state_code VARCHAR NOT NULL,
            year INTEGER,
            file_path VARCHAR(255) UNIQUE,
            file_size_mb REAL,
            hash_info VARCHAR(64),
            last_updated TIMESTAMP
        ); """)

        