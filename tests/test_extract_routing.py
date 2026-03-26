"""
Tests for API parser routing logic in server/extract.py.

Verifies that API-based parsers (marker, etc.) skip the remote parse
service, while local parsers (pymupdf, tables) use it.
"""
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["FIREBASE_AUTH_DISABLED"] = "1"

# Import after setting env var so firebase_admin skip works
from server.extract import (  # noqa: E402
    async_extract,
    async_extract_pages,
    extract_text,
    _remote_parse_fn,
    _remote_page_parse_fn,
    _set_ocr_env,
)

FIXTURES = Path(__file__).parent / "fixtures"
MCI_PDF = str(FIXTURES / "mci_page1.pdf")

MOCK_SETTINGS = {
    "model": "gpt-4o",
    "openai_api_key": "sk-test-key",
    "concurrency": 5,
    "parse_multiplier": 3,
}


# -------------------------------------------------------------------
# async_extract — parse_fn routing
# -------------------------------------------------------------------

class TestAsyncExtractRouting:
    @pytest.mark.asyncio
    async def test_local_parser_uses_remote_parse_fn(self):
        with (
            patch(
                "server.extract.get_settings",
                return_value=MOCK_SETTINGS,
            ),
            patch(
                "server.extract.get_provider",
                return_value="openai",
            ),
            patch(
                "server.extract._extract_async",
                new_callable=AsyncMock,
            ) as mock_ext,
            patch("server.extract._set_ocr_env"),
        ):
            mock_ext.return_value = MagicMock()
            await async_extract(
                MCI_PDF, MagicMock(),
                uid="test", parser="pymupdf",
            )

        kw = mock_ext.call_args.kwargs
        assert kw["parse_fn"] is _remote_parse_fn

    @pytest.mark.asyncio
    async def test_api_parser_skips_remote_parse_fn(self):
        with (
            patch(
                "server.extract.get_settings",
                return_value=MOCK_SETTINGS,
            ),
            patch(
                "server.extract.get_provider",
                return_value="openai",
            ),
            patch(
                "server.extract._extract_async",
                new_callable=AsyncMock,
            ) as mock_ext,
            patch("server.extract._set_ocr_env"),
        ):
            mock_ext.return_value = MagicMock()
            await async_extract(
                MCI_PDF, MagicMock(),
                uid="test", parser="marker",
            )

        kw = mock_ext.call_args.kwargs
        assert kw["parse_fn"] is None

    @pytest.mark.asyncio
    async def test_anthropic_requires_key(self):
        settings = {
            **MOCK_SETTINGS,
            "model": "claude-sonnet-4-20250514",
            "anthropic_api_key": "",
        }
        with (
            patch(
                "server.extract.get_settings",
                return_value=settings,
            ),
            patch(
                "server.extract.get_provider",
                return_value="anthropic",
            ),
            patch("server.extract._set_ocr_env"),
        ):
            with pytest.raises(ValueError, match="Anthropic"):
                await async_extract(
                    MCI_PDF, MagicMock(), uid="test",
                )

    @pytest.mark.asyncio
    async def test_openai_requires_key(self):
        settings = {
            **MOCK_SETTINGS,
            "model": "gpt-4o",
            "openai_api_key": "",
        }
        with (
            patch(
                "server.extract.get_settings",
                return_value=settings,
            ),
            patch(
                "server.extract.get_provider",
                return_value="openai",
            ),
            patch("server.extract._set_ocr_env"),
        ):
            with pytest.raises(ValueError, match="OpenAI"):
                await async_extract(
                    MCI_PDF, MagicMock(), uid="test",
                )


# -------------------------------------------------------------------
# async_extract_pages — parse_fn routing
# -------------------------------------------------------------------

class TestAsyncExtractPagesRouting:
    @pytest.mark.asyncio
    async def test_local_parser_uses_remote(self):
        with (
            patch(
                "server.extract.get_settings",
                return_value=MOCK_SETTINGS,
            ),
            patch(
                "server.extract.get_provider",
                return_value="openai",
            ),
            patch(
                "server.extract._extract_pages_async",
                new_callable=AsyncMock,
            ) as mock_ext,
            patch("server.extract._set_ocr_env"),
        ):
            mock_ext.return_value = []
            await async_extract_pages(
                MCI_PDF, MagicMock(),
                uid="test", parser="pymupdf",
            )

        kw = mock_ext.call_args.kwargs
        assert kw["parse_fn"] is _remote_page_parse_fn

    @pytest.mark.asyncio
    async def test_api_parser_skips_remote(self):
        with (
            patch(
                "server.extract.get_settings",
                return_value=MOCK_SETTINGS,
            ),
            patch(
                "server.extract.get_provider",
                return_value="openai",
            ),
            patch(
                "server.extract._extract_pages_async",
                new_callable=AsyncMock,
            ) as mock_ext,
            patch("server.extract._set_ocr_env"),
        ):
            mock_ext.return_value = []
            await async_extract_pages(
                MCI_PDF, MagicMock(),
                uid="test", parser="marker",
            )

        kw = mock_ext.call_args.kwargs
        assert kw["parse_fn"] is None

    @pytest.mark.asyncio
    async def test_passes_concurrency_settings(self):
        with (
            patch(
                "server.extract.get_settings",
                return_value=MOCK_SETTINGS,
            ),
            patch(
                "server.extract.get_provider",
                return_value="openai",
            ),
            patch(
                "server.extract._extract_pages_async",
                new_callable=AsyncMock,
            ) as mock_ext,
            patch("server.extract._set_ocr_env"),
            patch(
                "server.extract.configure_concurrency",
            ) as mock_cfg,
        ):
            mock_ext.return_value = []
            await async_extract_pages(
                MCI_PDF, MagicMock(), uid="test",
            )

        kw = mock_ext.call_args.kwargs
        assert kw["concurrency"] == 5
        assert "parse_multiplier" not in kw
        mock_cfg.assert_called_with(api_limit=5)


# -------------------------------------------------------------------
# _set_ocr_env
# -------------------------------------------------------------------

class TestSetOcrEnv:
    def test_sets_datalab_key(self):
        settings = {
            **MOCK_SETTINGS,
            "datalab_api_key": "dl-test-key",
        }
        with patch(
            "server.extract.get_settings",
            return_value=settings,
        ):
            _set_ocr_env("test")
        assert os.environ.get("DATALAB_API_KEY") == "dl-test-key"
        os.environ.pop("DATALAB_API_KEY", None)

    def test_sets_mistral_key(self):
        settings = {
            **MOCK_SETTINGS,
            "mistral_api_key": "ms-test-key",
        }
        with patch(
            "server.extract.get_settings",
            return_value=settings,
        ):
            _set_ocr_env("test")
        assert os.environ.get("MISTRAL_API_KEY") == "ms-test-key"
        os.environ.pop("MISTRAL_API_KEY", None)

    def test_skips_empty_keys(self):
        os.environ.pop("DATALAB_API_KEY", None)
        settings = {
            **MOCK_SETTINGS,
            "datalab_api_key": "",
        }
        with patch(
            "server.extract.get_settings",
            return_value=settings,
        ):
            _set_ocr_env("test")
        assert "DATALAB_API_KEY" not in os.environ


# -------------------------------------------------------------------
# extract_text — OCR fallback
# -------------------------------------------------------------------

class TestExtractTextOcrFallback:
    @pytest.mark.asyncio
    async def test_ocr_fallback_on_short_text(self):
        """When parser returns < 200 chars, OCR should kick in."""
        with (
            patch(
                "server.extract._remote_parse_fn",
                new_callable=AsyncMock,
                return_value="short",
            ),
            patch(
                "server.par_extract._ocr_pdf",
                return_value="OCR extracted a full page of useful text " * 10,
            ) as mock_ocr,
        ):
            text, info = await extract_text("/fake.pdf", ocr_fallback=True)

        assert "No usable text layer detected" in info[0]
        assert "OCR extracted" in text
        mock_ocr.assert_called_once()

    @pytest.mark.asyncio
    async def test_ocr_fallback_keeps_original_when_ocr_empty(self):
        """If OCR returns empty, keep the original text."""
        with (
            patch(
                "server.extract._remote_parse_fn",
                new_callable=AsyncMock,
                return_value="short",
            ),
            patch(
                "server.par_extract._ocr_pdf",
                return_value="",
            ),
        ):
            text, info = await extract_text("/fake.pdf", ocr_fallback=True)

        assert text == "short"
        assert any("OCR did not produce usable text" in m for m in info)

    @pytest.mark.asyncio
    async def test_ocr_fallback_handles_exception(self):
        """If OCR crashes, keep original text and report error."""
        with (
            patch(
                "server.extract._remote_parse_fn",
                new_callable=AsyncMock,
                return_value="short",
            ),
            patch(
                "server.par_extract._ocr_pdf",
                side_effect=RuntimeError("ghostscript missing"),
            ),
        ):
            text, info = await extract_text("/fake.pdf", ocr_fallback=True)

        assert text == "short"
        assert any("OCR failed" in m for m in info)

    @pytest.mark.asyncio
    async def test_no_ocr_when_text_sufficient(self):
        """No OCR fallback when text is >= 200 chars."""
        long_text = "x" * 200
        with (
            patch(
                "server.extract._remote_parse_fn",
                new_callable=AsyncMock,
                return_value=long_text,
            ),
        ):
            text, info = await extract_text("/fake.pdf", ocr_fallback=True)

        assert text == long_text
        assert info == []

    @pytest.mark.asyncio
    async def test_no_ocr_when_fallback_disabled(self):
        """No OCR when ocr_fallback=False even with short text."""
        with (
            patch(
                "server.extract._remote_parse_fn",
                new_callable=AsyncMock,
                return_value="short",
            ),
        ):
            text, info = await extract_text("/fake.pdf", ocr_fallback=False)

        assert text == "short"
        assert info == []
