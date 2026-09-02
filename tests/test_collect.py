from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from viraldzen.cli import main
from viraldzen.collect import keep_item
from viraldzen.dzen import DzenApi
from viraldzen.http import DzenHttpError
from viraldzen.models import ViralItem


def _item(**kwargs) -> ViralItem:
    base = dict(
        publication_id="x",
        url="https://dzen.ru/a/x",
        title="t",
        topic="здоровье",
        source_kind="feed",
    )
    base.update(kwargs)
    return ViralItem(**base)  # type: ignore[arg-type]


class KeepItemTests(unittest.TestCase):
    def test_search_and_seeds_survive_offtopic(self) -> None:
        off = _item(title="Тиара принцессы", source_kind="search")
        self.assertTrue(keep_item(off, channel_only=False, seed_urls=set()))
        seed = _item(
            publication_id="seed",
            url="https://dzen.ru/a/seed",
            title="Исходная статья",
            source_kind="article",
        )
        self.assertTrue(
            keep_item(seed, channel_only=False, seed_urls={"https://dzen.ru/a/seed"})
        )

    def test_feed_offtopic_is_dropped_unless_channel_only(self) -> None:
        off = _item(title="Тиара принцессы", source_kind="feed")
        self.assertFalse(keep_item(off, channel_only=False, seed_urls=set()))
        self.assertTrue(keep_item(off, channel_only=True, seed_urls=set()))


class FetchArticleMissingTests(unittest.TestCase):
    def test_http_404_returns_none(self) -> None:
        class DeadClient:
            def get_text(self, url: str, accept: str | None = None) -> str:
                raise DzenHttpError(f"HTTP 404 for {url}", status=404, url=url)

            def warmup(self) -> None:
                return None

        api = DzenApi(DeadClient())  # type: ignore[arg-type]
        self.assertIsNone(
            api.fetch_article("https://dzen.ru/a/YCOv_9buVzJJUFOz", topic="кредиты")
        )


class CliCollectHelpTests(unittest.TestCase):
    def test_collect_help_mentions_channel_only_and_url(self) -> None:
        buf = io.StringIO()
        with self.assertRaises(SystemExit) as caught, redirect_stdout(buf):
            main(["collect", "--help"])
        self.assertEqual(caught.exception.code, 0)
        text = buf.getvalue()
        self.assertIn("--channel-only", text)
        self.assertIn("--url", text)
        self.assertIn("--portable", text)


if __name__ == "__main__":
    unittest.main()
