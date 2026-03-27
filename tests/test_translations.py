from unittest.mock import patch, MagicMock

from app.services.translation_service import translate_text, _split_text


def test_split_text_short():
    text = "Short text"
    chunks = _split_text(text)
    assert chunks == ["Short text"]


def test_split_text_long():
    text = "A" * 5000 + "\n\n" + "B" * 3000
    chunks = _split_text(text)
    assert all(len(c) <= 4500 for c in chunks)
    joined = "\n\n".join(chunks)
    assert "A" * 100 in joined
    assert "B" * 100 in joined


@patch("app.services.translation_service.GoogleTranslator")
def test_translate_text(mock_translator_cls):
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "Texto traducido"
    mock_translator_cls.return_value = mock_instance

    result = translate_text("Translated text", "en", "es")
    assert result == "Texto traducido"
    mock_translator_cls.assert_called_with(source="en", target="es")


@patch("app.services.translation_service.GoogleTranslator")
def test_translate_text_empty(mock_translator_cls):
    result = translate_text("", "en", "es")
    assert result == ""
    mock_translator_cls.assert_not_called()


@patch("app.services.translation_service.GoogleTranslator")
def test_translate_text_retry_on_failure(mock_translator_cls):
    mock_instance = MagicMock()
    mock_instance.translate.side_effect = [Exception("fail"), "Success"]
    mock_translator_cls.return_value = mock_instance

    with patch("app.services.translation_service.time.sleep"):
        result = translate_text("Hello", "en", "es")
    assert result == "Success"
    assert mock_instance.translate.call_count == 2
