import configparser
import pathlib
import unittest

from alembic.config import Config


class TestAlembicPercentEncoding(unittest.TestCase):
    def test_alembic_ini_fails_with_unescaped_percent_encoded_uri(self):
        """Without escaping, a percent-encoded character in the database URL
        triggers ConfigParser invalid interpolation syntax on set_section_option."""
        alembic_ini_path = pathlib.Path(__file__).parents[2] / "alembic.ini"
        cfg = Config(str(alembic_ini_path))
        raw_url = "postgresql+asyncpg://user%40example.com:p%25ss@localhost:5432/testdb"

        with self.assertRaises(ValueError) as ctx:
            cfg.set_section_option(
                cfg.config_ini_section,
                "SQLALCHEMY_DATABASE_URI",
                raw_url,
            )
        self.assertIn("invalid interpolation syntax", str(ctx.exception))

    def test_alembic_ini_succeeds_with_escaped_percent_encoded_uri(self):
        """With .replace('%', '%%'), Alembic's ConfigParser interpolation converts
        '%%' back into '%' and reproduces the exact raw URL without errors."""
        alembic_ini_path = pathlib.Path(__file__).parents[2] / "alembic.ini"
        cfg = Config(str(alembic_ini_path))
        raw_url = "postgresql+asyncpg://user%40example.com:p%25ss%3Aword@localhost:5432/testdb"

        cfg.set_section_option(
            cfg.config_ini_section,
            "SQLALCHEMY_DATABASE_URI",
            raw_url.replace("%", "%%"),
        )
        resolved_url = cfg.get_section_option(cfg.config_ini_section, "sqlalchemy.url")
        self.assertEqual(resolved_url, raw_url)

        section_dict = cfg.get_section(cfg.config_ini_section, {})
        self.assertEqual(section_dict["sqlalchemy.url"], raw_url)

    def test_various_url_encoded_credentials(self):
        """Test multiple percent-encoded credentials (OAuth emails, special symbols)."""
        alembic_ini_path = pathlib.Path(__file__).parents[2] / "alembic.ini"
        cfg = Config(str(alembic_ini_path))

        test_urls = [
            "postgresql+asyncpg://iam-user%40company.org:secret@host:5432/db",
            "postgresql+asyncpg://admin:p%25%21%23ss%2A@host:5432/db",
            "sqlite+aiosqlite:///path/with%20spaces/db.sqlite",
        ]

        for raw_url in test_urls:
            cfg.set_section_option(
                cfg.config_ini_section,
                "SQLALCHEMY_DATABASE_URI",
                raw_url.replace("%", "%%"),
            )
            self.assertEqual(
                cfg.get_section_option(cfg.config_ini_section, "sqlalchemy.url"),
                raw_url,
            )


if __name__ == "__main__":
    unittest.main()
