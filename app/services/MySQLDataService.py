from __future__ import annotations

import os
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from .AbstractBaseDataService import AbstractBaseDataService


class MySQLDataService(AbstractBaseDataService):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._table_name = config["table_name"]
        self._primary_key_field = config["primary_key_field"]

        self._host = os.getenv("MYSQL_HOST", "localhost")
        self._port = int(os.getenv("MYSQL_PORT", "3306"))
        self._user = os.getenv("MYSQL_USER", "root")
        self._password = os.getenv("MYSQL_PASSWORD", "")
        self._database = os.getenv("MYSQL_DATABASE", "classicmodels")

    def _get_connection(self):
        return pymysql.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
            cursorclass=DictCursor,
            autocommit=True,
        )

    def _validate_identifier(self, name: str) -> None:
        if not name.replace("_", "").isalnum():
            raise ValueError(f"Invalid SQL identifier: {name}")

    def _validate_payload_keys(self, payload: dict) -> None:
        for key in payload.keys():
            self._validate_identifier(str(key))

    def retrieveByPrimaryKey(self, primary_key: str) -> dict:
        self._validate_identifier(self._table_name)
        self._validate_identifier(self._primary_key_field)

        sql = f"""
            SELECT *
            FROM {self._table_name}
            WHERE {self._primary_key_field} = %s
        """

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (primary_key,))
                row = cursor.fetchone()

        return dict(row) if row else {}

    def retrieveByTemplate(self, template: dict) -> list[dict]:
        self._validate_identifier(self._table_name)
        self._validate_payload_keys(template)

        sql = f"SELECT * FROM {self._table_name}"
        values: list[Any] = []

        if template:
            where_parts = []
            for key, value in template.items():
                where_parts.append(f"{key} = %s")
                values.append(value)
            sql += " WHERE " + " AND ".join(where_parts)

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def create(self, payload: dict) -> str:
        self._validate_identifier(self._table_name)
        self._validate_payload_keys(payload)

        columns = list(payload.keys())
        values = list(payload.values())

        column_sql = ", ".join(columns)
        placeholder_sql = ", ".join(["%s"] * len(columns))

        sql = f"""
            INSERT INTO {self._table_name} ({column_sql})
            VALUES ({placeholder_sql})
        """

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)

        return str(payload.get(self._primary_key_field, ""))

    def updateByPrimaryKey(self, primary_key: str, payload: dict) -> int:
        self._validate_identifier(self._table_name)
        self._validate_identifier(self._primary_key_field)
        self._validate_payload_keys(payload)

        update_fields = [
            key for key in payload.keys()
            if key != self._primary_key_field
        ]

        if not update_fields:
            return 0

        set_sql = ", ".join([f"{key} = %s" for key in update_fields])
        values = [payload[key] for key in update_fields]
        values.append(primary_key)

        sql = f"""
            UPDATE {self._table_name}
            SET {set_sql}
            WHERE {self._primary_key_field} = %s
        """

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                return cursor.rowcount

    def deleteByPrimaryKey(self, primary_key: str) -> int:
        self._validate_identifier(self._table_name)
        self._validate_identifier(self._primary_key_field)

        sql = f"""
            DELETE FROM {self._table_name}
            WHERE {self._primary_key_field} = %s
        """

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (primary_key,))
                return cursor.rowcount

    def updateByTemplate(self, template: dict, payload: dict) -> int:
        self._validate_identifier(self._table_name)
        self._validate_payload_keys(template)
        self._validate_payload_keys(payload)

        update_fields = [
            key for key in payload.keys()
            if key not in template
        ]

        if not update_fields:
            return 0

        set_sql = ", ".join([f"{key} = %s" for key in update_fields])
        where_sql = " AND ".join([f"{key} = %s" for key in template.keys()])

        values = [payload[key] for key in update_fields]
        values.extend(template.values())

        sql = f"""
            UPDATE {self._table_name}
            SET {set_sql}
            WHERE {where_sql}
        """

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                return cursor.rowcount

    def deleteByTemplate(self, template: dict) -> int:
        self._validate_identifier(self._table_name)
        self._validate_payload_keys(template)

        if not template:
            raise ValueError("Delete template cannot be empty")

        where_sql = " AND ".join([f"{key} = %s" for key in template.keys()])
        values = list(template.values())

        sql = f"""
            DELETE FROM {self._table_name}
            WHERE {where_sql}
        """

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                return cursor.rowcount