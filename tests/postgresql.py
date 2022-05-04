import os
import uuid
from datetime import date, datetime
from unittest import TestCase, expectedFailure
from unittest.mock import patch

import psycopg2

from database import PostgreSQL, create_database_interface
from tasks import DatabaseInterface


def get_database_name():
    return os.environ["POSTGRES_DB"]


def get_database_user():
    return os.environ["POSTGRES_USER"]


def get_database_password():
    return os.environ["POSTGRES_PASSWORD"]


def get_database_port():
    return os.environ["POSTGRES_PORT"]


@patch.dict(
    "os.environ",
    {
        "POSTGRES_DB": "db",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "9999",
    },
)
class CreationDatabaseInterfaceFunctionTests(TestCase):
    def test_create_database_interface_passing_valid_arguments(self):
        with patch(
            "psycopg2.connect",
        ) as mock:
            pgsql = create_database_interface()
            self.assertIsInstance(
                pgsql,
                DatabaseInterface,
                msg="create_database_interface should return an object of DatabaseInterface in order to be usefull by the tasks",
            )
            mock.called_once_with(
                dbname="db", user="user", password="pass", host="localhost", port="9999"
            )


class PostgreSQLConnectionTests(TestCase):
    def test_postgresql_connection(self):
        HOST = "localhost"
        DATABASE = get_database_name()
        USER = get_database_user()
        PASSWORD = get_database_password()
        PORT = get_database_port()
        with patch(
            "psycopg2.connect",
        ) as mock:
            pgsql = PostgreSQL(HOST, DATABASE, USER, PASSWORD, PORT)
            self.assertIsInstance(
                pgsql,
                DatabaseInterface,
                msg="PostgreSQL class should be a instance of DatabaseInterface in order to be usefull by the tasks",
            )
            mock.called_once()


class PostgreSQLTests(TestCase):

    _data = []

    def setUp(self):
        self.connect_to_database()
        self.clean_database()
        self.create_database_schema()
        self.insert_test_data()
        self._pgsql = PostgreSQL(
            "localhost",
            get_database_name(),
            get_database_user(),
            get_database_password(),
            get_database_port(),
        )

    def tearDown(self):
        self.disconnect_database()

    def connect_to_database(self):
        self._dbconnection = psycopg2.connect(
            dbname=get_database_name(),
            user=get_database_user(),
            password=get_database_password(),
            host="localhost",
        )

    def disconnect_database(self):
        self._dbconnection.close()

    def create_database_schema(self):
        with self._dbconnection.cursor() as cursor:
            self.create_territories_table(cursor)
            self.create_gazettes_table(cursor)
            self._dbconnection.commit()

    def create_territories_table(self, cursor):
        cursor.execute(
            """
            CREATE TABLE territories (
                id character varying NOT NULL,
                name character varying,
                state_code character varying,
                state character varying
            ); """
        )
        cursor.execute(
            """
            ALTER TABLE ONLY territories
                ADD CONSTRAINT territories_pkey PRIMARY KEY (id);
            """
        )

    def create_gazettes_table(self, cursor):
        cursor.execute(
            """
            CREATE TABLE gazettes (
                id integer NOT NULL,
                source_text text,
                date date,
                edition_number character varying,
                is_extra_edition boolean,
                power character varying,
                file_checksum character varying,
                file_path character varying,
                file_url character varying,
                scraped_at timestamp without time zone,
                created_at timestamp without time zone,
                territory_id character varying,
                processed boolean
        );"""
        )
        cursor.execute(
            """
            CREATE SEQUENCE gazettes_id_seq
                AS integer
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1;
        """
        )
        cursor.execute(
            """
            ALTER TABLE ONLY gazettes
                ALTER COLUMN id SET DEFAULT nextval('gazettes_id_seq'::regclass);
        """
        )
        cursor.execute(
            """
            ALTER TABLE ONLY gazettes
                ADD CONSTRAINT gazettes_pkey PRIMARY KEY (id);
        """
        )
        cursor.execute(
            """
            ALTER TABLE ONLY gazettes
                ADD CONSTRAINT gazettes_territory_id_date_file_checksum_key UNIQUE (territory_id, date, file_checksum);
        """
        )

    def insert_territories_data(self, cursor):
        territory_data = {
            "id": "3550308",
            "name": "Gaspar",
            "state_code": "SC",
            "state": "Santa Catarina",
        }
        cursor.execute(
            """
            INSERT INTO territories (
	        id,
	        name ,
	        state_code,
	        state)
            VALUES (
                %(id)s,
                %(name)s,
                %(state_code)s,
                %(state)s
                );""",
            territory_data,
        )

    def insert_gazettes_data(self, cursor):
        for data in self._data:
            cursor.execute(
                """
                INSERT INTO gazettes (
                    id,
                    source_text,
                    date ,
                    edition_number,
                    is_extra_edition,
                    power,
                    file_checksum ,
                    file_path ,
                    file_url ,
                    scraped_at,
                    created_at,
                    territory_id,
                    processed)
                VALUES ( %(id)s,
                    %(source_text)s,
                    %(date)s ,
                    %(edition_number)s,
                    %(is_extra_edition)s,
                    %(power)s,
                    %(file_checksum)s ,
                    %(file_path)s ,
                    %(file_url)s ,
                    %(scraped_at)s,
                    %(created_at)s,
                    %(territory_id)s,
                    %(processed)s);""",
                data,
            )

    def insert_test_data(self):
        self.generate_fake_data()
        with self._dbconnection.cursor() as cursor:
            self.insert_territories_data(cursor)
            self.insert_gazettes_data(cursor)
            self._dbconnection.commit()

    def generate_fake_data(self):
        self._data.clear()
        for id in range(10):
            self._data.append(
                {
                    "id": id,
                    "source_text": "",
                    "date": date.today(),
                    "edition_number": str(id),
                    "is_extra_edition": False,
                    "power": "executive",
                    "file_checksum": str(uuid.uuid1()),
                    "file_path": f"my/fake/path/gazette/{id}.pdf",
                    "file_url": "www.querido-diario.org",
                    "scraped_at": datetime.now(),
                    "created_at": datetime.now(),
                    "territory_id": "3550308",
                    "processed": False,
                    "state_code": "SC",
                    "territory_name": "Gaspar",
                }
            )
        self.set_some_fake_data_as_ingested_by_the_system_and_no_need_to_be_processed()

    def set_some_fake_data_as_ingested_by_the_system_and_no_need_to_be_processed(self):
        self._data[-1]["processed"] = True
        self._data[-2]["processed"] = True

    def get_gazettes_pending_to_be_processed(self):
        for gazette in self._data:
            if gazette["processed"] == False:
                yield gazette

    def clean_database(self):
        with self._dbconnection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS gazettes;")
            cursor.execute("DROP TABLE IF EXISTS territories;")
            cursor.execute("DROP SEQUENCE IF EXISTS gazettes_id_seq;")
            self._dbconnection.commit()

    def test_get_gazettes(self):
        gazettes_in_the_database = self._pgsql.get_pending_gazettes()
        self.assertCountEqual(
            gazettes_in_the_database, self.get_gazettes_pending_to_be_processed()
        )

    def test_get_pending_gazettes(self):
        gazettes_in_the_database = self._pgsql.get_pending_gazettes()
        expected_gazettes = self.get_gazettes_pending_to_be_processed()
        self.assertCountEqual(gazettes_in_the_database, expected_gazettes)

    def test_set_gazette_as_processed(self):
        pending_gazettes = self.get_gazettes_pending_to_be_processed()
        for gazette in pending_gazettes:
            self._pgsql.set_gazette_as_processed(
                gazette["id"], gazette["file_checksum"]
            )
        pending_gazettes_in_database = self._pgsql.get_pending_gazettes()
        self.assertEqual(0, len(list(pending_gazettes_in_database)))
