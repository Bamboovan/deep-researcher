# Copyright (c) Nex-AGI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import http.client
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Tuple
from urllib import request as urllib_request

logger = logging.getLogger(__name__)

JINA_READER_ENDPOINT = "https://r.jina.ai/"
SERPER_SCRAPE_HOST = "scrape.serper.dev"
DEFAULT_SUFFIX = ".txt"
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".py",
    ".json",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
}
# PDF and image extensions
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
BINARY_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS


class FileParser:
    """
    Fetch textual content from URLs or local files using configurable providers.
    Returns a tuple of (success, content, suffix).
    Supports: text files, PDFs, images (with OCR/captioning)
    """

    def __init__(self, timeout: float = 45.0) -> None:
        self.timeout = timeout
        self.jina_api_key = os.getenv("JINA_API_KEY")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.providers = self._load_provider_order()

        # Initialize optional parsers
        self._pdf_parser = None
        self._image_captioner = None

    async def parse(self, url_or_local_file: str) -> Tuple[bool, str, str]:
        if self._looks_like_url(url_or_local_file):
            return await self._parse_remote(url_or_local_file)
        return await self._parse_local(url_or_local_file)

    async def _parse_remote(self, url: str) -> Tuple[bool, str, str]:
        errors = []
        for provider in self.providers:
            if provider == "jina":
                success, content, suffix = await self._parse_remote_with_jina(url)
            elif provider == "serper":
                success, content, suffix = await self._parse_remote_with_serper(url)
            else:
                logger.warning("Unknown document parser provider: %s", provider)
                errors.append(f"{provider}: unsupported provider")
                continue

            if success:
                return True, content, suffix
            errors.append(f"{provider}: {content}")

        error_msg = "Failed to fetch document with available providers. " + " | ".join(
            errors
        )
        return False, error_msg, DEFAULT_SUFFIX

    async def _parse_remote_with_jina(self, url: str) -> Tuple[bool, str, str]:
        if not self.jina_api_key:
            error_msg = (
                "JINA_API_KEY environment variable is required but not set. "
                "Please set it with your Jina API key."
            )
            logger.warning(error_msg)
            return False, error_msg, DEFAULT_SUFFIX

        jina_url = self._build_jina_reader_url(url)
        logger.info("Fetching document via Jina reader: %s", jina_url)

        try:
            raw_bytes = await asyncio.to_thread(
                self._fetch_bytes, jina_url, self.timeout, self.jina_api_key
            )
        except Exception as exc:
            logger.exception("Failed to fetch remote document: %s", url)
            return False, f"Failed to fetch {url}: {exc}", DEFAULT_SUFFIX

        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("utf-8", errors="ignore")

        if not content.strip():
            logger.warning("Empty content returned from Jina reader for %s", url)
            return False, "Empty content returned from Jina reader", DEFAULT_SUFFIX

        return True, content, DEFAULT_SUFFIX

    async def _parse_remote_with_serper(self, url: str) -> Tuple[bool, str, str]:
        if not self.serper_api_key:
            error_msg = (
                "SERPER_API_KEY environment variable is required but not set. "
                "Please set it with your Serper API key."
            )
            logger.warning(error_msg)
            return False, error_msg, DEFAULT_SUFFIX

        payload = json.dumps({"url": url})
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json",
        }
        logger.info("Fetching document via Serper scrape: %s", url)

        try:
            status, raw_bytes = await asyncio.to_thread(
                self._fetch_serper_bytes,
                payload,
                headers,
                self.timeout,
            )
        except Exception as exc:
            logger.exception("Failed to fetch remote document via Serper: %s", url)
            return False, f"Failed to fetch via Serper {url}: {exc}", DEFAULT_SUFFIX

        if status >= 400:
            logger.error(
                "Serper scrape returned status %s for %s",
                status,
                url,
            )
            return (
                False,
                f"Serper scrape error (status {status})",
                DEFAULT_SUFFIX,
            )

        try:
            decoded = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            decoded = raw_bytes.decode("utf-8", errors="ignore")

        parsed = self._extract_text_from_serper_response(decoded)
        if not parsed.strip():
            logger.warning("Empty content returned from Serper scrape for %s", url)
            return False, "Empty content returned from Serper scrape", DEFAULT_SUFFIX

        return True, parsed, ".md"

    async def _parse_local(self, path_str: str) -> Tuple[bool, str, str]:
        path = Path(path_str).expanduser().resolve()

        if not path.exists():
            error_msg = f"Local file not found: {path}"
            logger.error(error_msg)
            return False, error_msg, DEFAULT_SUFFIX

        suffix = path.suffix.lower()

        # Handle PDF files
        if suffix in PDF_EXTENSIONS:
            return await self._parse_pdf(path)

        # Handle image files
        if suffix in IMAGE_EXTENSIONS:
            return await self._parse_image(path)

        # Handle text files
        read_as_text = suffix in TEXT_EXTENSIONS or self._is_probably_text(path)

        try:
            if read_as_text:
                content = await asyncio.to_thread(
                    path.read_text, encoding="utf-8", errors="ignore"
                )
            else:
                content = await asyncio.to_thread(
                    path.read_bytes,
                )
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    content = content.decode("utf-8", errors="ignore")
        except Exception as exc:
            logger.exception("Failed to read local file: %s", path)
            return False, f"Failed to read {path}: {exc}", suffix or DEFAULT_SUFFIX

        if not content.strip():
            logger.warning("Local file %s yielded empty content", path)
            return False, "Local file is empty", suffix or DEFAULT_SUFFIX

        return True, content, suffix or DEFAULT_SUFFIX

    async def _parse_pdf(self, path: Path) -> Tuple[bool, str, str]:
        """Parse PDF file and extract text"""
        logger.info("Parsing PDF file: %s", path)

        try:
            # Try to import pypdf
            if self._pdf_parser is None:
                try:
                    from pypdf import PdfReader

                    self._pdf_parser = PdfReader
                except ImportError:
                    error_msg = (
                        "pypdf library not installed. Install with: pip install pypdf"
                    )
                    logger.error(error_msg)
                    return False, error_msg, ".pdf"

            # Read PDF
            pdf_reader = self._pdf_parser(str(path))
            pages_text = []

            for i, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(f"--- Page {i+1} ---\n{text}")

            if not pages_text:
                logger.warning("No text extracted from PDF: %s", path)
                return False, "No text content found in PDF", ".pdf"

            content = "\n\n".join(pages_text)
            logger.info(
                "Successfully extracted text from PDF: %s (%d pages)",
                path,
                len(pages_text),
            )
            return True, content, ".pdf"

        except Exception as exc:
            logger.exception("Failed to parse PDF: %s", path)
            return False, f"Failed to parse PDF {path}: {exc}", ".pdf"

    async def _parse_image(self, path: Path) -> Tuple[bool, str, str]:
        """Parse image file - generate caption using multi-modal LLM or OCR"""
        logger.info("Parsing image file: %s", path)

        try:
            # Read image as base64
            image_bytes = await asyncio.to_thread(path.read_bytes)
            import base64

            base64_data = base64.b64encode(image_bytes).decode("utf-8")

            # Try to generate caption using multi-modal LLM
            caption = await self._generate_image_caption(
                base64_data, path.suffix.lower()
            )

            if caption:
                content = f"[Image Analysis]\n\n{caption}"
                logger.info("Successfully generated caption for image: %s", path)
                return True, content, path.suffix.lower()
            else:
                # Fallback to OCR if caption generation fails
                ocr_text = await self._ocr_image(path)
                if ocr_text:
                    content = f"[OCR Result]\n\n{ocr_text}"
                    logger.info("Successfully performed OCR on image: %s", path)
                    return True, content, path.suffix.lower()
                else:
                    return (
                        False,
                        "Failed to extract content from image",
                        path.suffix.lower(),
                    )

        except Exception as exc:
            logger.exception("Failed to parse image: %s", path)
            return False, f"Failed to parse image {path}: {exc}", path.suffix.lower()

    async def _generate_image_caption(self, base64_data: str, mime_type: str) -> str:
        """Generate caption for image using multi-modal LLM"""
        try:
            # Check if multi-modal LLM is configured
            api_key = os.getenv("MULTI_MODAL_LLM_API_KEY")
            base_url = os.getenv("MULTI_MODAL_LLM_BASE_URL")
            model = os.getenv("MULTI_MODAL_LLM_MODEL")

            if not all([api_key, base_url, model]):
                logger.warning(
                    "Multi-modal LLM not configured, skipping image captioning"
                )
                return None

            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key, base_url=base_url)

            # Determine mime type
            if mime_type in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            elif mime_type == ".png":
                mime = "image/png"
            elif mime_type == ".gif":
                mime = "image/gif"
            elif mime_type == ".webp":
                mime = "image/webp"
            else:
                mime = "image/jpeg"  # default

            data_url = f"data:{mime};base64,{base64_data}"

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please provide a detailed description of this image. Include any text visible in the image, describe the main subjects, colors, composition, and context. If it's a chart, graph, or diagram, explain what information it conveys.",
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                max_tokens=1000,
            )

            caption = response.choices[0].message.content
            return caption if caption else None

        except Exception as e:
            logger.warning("Failed to generate image caption: %s", str(e))
            return None

    async def _ocr_image(self, path: Path) -> str:
        """Perform OCR on image to extract text"""
        try:
            # Try to import pytesseract
            try:
                import pytesseract
                from PIL import Image
            except ImportError:
                logger.warning("pytesseract or PIL not installed, skipping OCR")
                return None

            # Perform OCR
            image = Image.open(path)
            text = pytesseract.image_to_string(image)

            if text and text.strip():
                return text
            return None

        except Exception as e:
            logger.warning("Failed to perform OCR: %s", str(e))
            return None

    @staticmethod
    def _looks_like_url(value: str) -> bool:
        return value.startswith("http://") or value.startswith("https://")

    @staticmethod
    def _fetch_bytes(url: str, timeout: float, api_key: str) -> bytes:
        headers = {
            "User-Agent": "NexDR/1.0",
            "Authorization": f"Bearer {api_key}",
        }
        request = urllib_request.Request(url, headers=headers)
        with urllib_request.urlopen(request, timeout=timeout) as response:
            return response.read()

    @staticmethod
    def _fetch_serper_bytes(
        payload: str, headers: dict, timeout: float
    ) -> Tuple[int, bytes]:
        conn = http.client.HTTPSConnection(SERPER_SCRAPE_HOST, timeout=timeout)
        try:
            conn.request("POST", "/", body=payload, headers=headers)
            res = conn.getresponse()
            status = res.status
            data = res.read()
        finally:
            conn.close()
        return status, data

    @staticmethod
    def _build_jina_reader_url(url: str) -> str:
        if url.startswith(JINA_READER_ENDPOINT):
            return url
        return f"{JINA_READER_ENDPOINT}{url}"

    @staticmethod
    def _is_probably_text(path: Path) -> bool:
        mime_type, _ = mimetypes.guess_type(path.name)
        return mime_type is not None and mime_type.startswith("text")

    @staticmethod
    def _load_provider_order() -> list[str]:
        providers_env = os.getenv("DOC_READER_PROVIDERS")
        if not providers_env:
            return ["jina", "serper"]
        providers = [
            provider.strip().lower()
            for provider in providers_env.split(",")
            if provider.strip()
        ]
        return providers or ["jina", "serper"]

    @staticmethod
    def _extract_text_from_serper_response(decoded_body: str) -> str:
        try:
            parsed_json = json.loads(decoded_body)
        except json.JSONDecodeError:
            return decoded_body

        if not isinstance(parsed_json, dict):
            return decoded_body

        if isinstance(parsed_json.get("markdown"), str):
            return parsed_json["markdown"]
        if isinstance(parsed_json.get("content"), str):
            return parsed_json["content"]
        if isinstance(parsed_json.get("text"), str):
            return parsed_json["text"]

        return decoded_body


if __name__ == "__main__":
    parser = FileParser()
    success, content, suffix = asyncio.run(parser.parse("https://chat2svg.github.io/"))
    print(success, content, suffix)
